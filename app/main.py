"""Demo help-desk API and website, designed as a real local QA target."""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT.parent / "data" / "casepilot.sqlite3"
STATUS = ("OPEN", "IN_PROGRESS", "RESOLVED")


def password_hash(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 150_000).hex()


def connect(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=10, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


@contextmanager
def db_conn(db_path: Path):
    conn = connect(db_path)
    try:
        yield conn
    finally:
        conn.close()


def seed(db_path: Path):
    with db_conn(db_path) as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY, email TEXT NOT NULL UNIQUE,
          salt TEXT NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions (
          token TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), expires_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tickets (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL, description TEXT NOT NULL,
          priority TEXT NOT NULL CHECK(priority IN ('LOW','MEDIUM','HIGH')),
          status TEXT NOT NULL CHECK(status IN ('OPEN','IN_PROGRESS','RESOLVED')),
          reporter_id INTEGER NOT NULL REFERENCES users(id), created_at TEXT NOT NULL
        );
        """)
        users = [("agent@casepilot.local", "AGENT"), ("viewer@casepilot.local", "VIEWER")]
        for email, role in users:
            if con.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone():
                continue
            salt = secrets.token_bytes(16)
            con.execute("INSERT INTO users(email,salt,password_hash,role) VALUES(?,?,?,?)",
                        (email, salt.hex(), password_hash("demo1234", salt), role))
        if con.execute("SELECT count(*) FROM tickets").fetchone()[0] == 0:
            agent = con.execute("SELECT id FROM users WHERE email=?", (users[0][0],)).fetchone()[0]
            now = datetime.now(timezone.utc).isoformat()
            for title, description, priority, status in [
                ("Falha ao exportar relatório", "CSV apresenta caracteres incorretos", "HIGH", "OPEN"),
                ("Atualização de endereço", "Alterar endereço cadastrado no portal", "MEDIUM", "IN_PROGRESS"),
                ("Dúvida sobre acesso", "Usuário não encontra o painel", "LOW", "RESOLVED"),
            ]:
                con.execute("INSERT INTO tickets(title,description,priority,status,reporter_id,created_at) VALUES(?,?,?,?,?,?)",
                            (title, description, priority, status, agent, now))


class LoginRequest(BaseModel):
    email: str
    password: str


class TicketCreate(BaseModel):
    title: str = Field(min_length=5, max_length=100)
    description: str = Field(min_length=10, max_length=1000)
    priority: Literal["LOW", "MEDIUM", "HIGH"]


class StatusUpdate(BaseModel):
    status: Literal["OPEN", "IN_PROGRESS", "RESOLVED"]


def create_app(db_path: Path | None = None) -> FastAPI:
    path = Path(db_path or os.environ.get("CASEPILOT_DB_PATH", DEFAULT_DB))
    seed(path)
    app = FastAPI(title="CasePilot Service Desk", version="1.0.0")

    def current_user(authorization: Annotated[str | None, Header()] = None):
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Autenticação necessária")
        token = authorization.removeprefix("Bearer ")
        with db_conn(path) as con:
            row = con.execute("""SELECT u.id,u.email,u.role FROM sessions s JOIN users u ON u.id=s.user_id
                                 WHERE s.token=? AND s.expires_at>?""",
                              (token, datetime.now(timezone.utc).isoformat())).fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Sessão inválida")
        return dict(row)

    @app.get("/")
    def index():
        return FileResponse(ROOT / "static" / "index.html")

    @app.get("/static/{file_name}")
    def static(file_name: str):
        if file_name not in ("style.css", "app.js"):
            raise HTTPException(404)
        return FileResponse(ROOT / "static" / file_name)

    @app.get("/api/health")
    def health():
        return {"status": "ok", "service": "casepilot"}

    @app.post("/api/login")
    def login(payload: LoginRequest):
        with db_conn(path) as con:
            row = con.execute("SELECT * FROM users WHERE email=?", (payload.email.strip().lower(),)).fetchone()
            salt = bytes.fromhex(row["salt"]) if row else b"0" * 16
            attempt = password_hash(payload.password, salt)
            if not row or not hmac.compare_digest(attempt, row["password_hash"]):
                raise HTTPException(status_code=401, detail="Credenciais inválidas")
            token = secrets.token_urlsafe(32)
            exp = (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat()
            con.execute("INSERT INTO sessions(token,user_id,expires_at) VALUES(?,?,?)", (token, row["id"], exp))
        return {"token": token, "email": row["email"], "role": row["role"]}

    @app.post("/api/logout", status_code=204)
    def logout(authorization: Annotated[str | None, Header()] = None):
        if authorization and authorization.startswith("Bearer "):
            with db_conn(path) as con:
                con.execute("DELETE FROM sessions WHERE token=?", (authorization[7:],))
        return None

    @app.get("/api/tickets")
    def get_tickets(
        search: str = Query("", max_length=100), status: str = "ALL",
        user: dict = Depends(current_user)
    ):
        if status not in (*STATUS, "ALL"):
            raise HTTPException(422, "Status inválido")
        where = ["(title LIKE ? OR description LIKE ?)"]
        args: list = [f"%{search}%", f"%{search}%"]
        if status != "ALL":
            where.append("status = ?")
            args.append(status)
        if user["role"] == "VIEWER":
            where.append("reporter_id = ?")
            args.append(user["id"])
        with db_conn(path) as con:
            rows = con.execute(f"SELECT id,title,description,priority,status,created_at FROM tickets WHERE {' AND '.join(where)} ORDER BY id DESC", args).fetchall()
        return {"items": [dict(x) for x in rows], "total": len(rows)}

    @app.post("/api/tickets", status_code=201)
    def create_ticket(payload: TicketCreate, user: dict = Depends(current_user)):
        title, description = payload.title.strip(), payload.description.strip()
        if len(title) < 5 or len(description) < 10:
            raise HTTPException(422, "Título ou descrição insuficiente")
        with db_conn(path) as con:
            cursor = con.execute("INSERT INTO tickets(title,description,priority,status,reporter_id,created_at) VALUES(?,?,?,?,?,?)",
                                 (title, description, payload.priority, "OPEN", user["id"], datetime.now(timezone.utc).isoformat()))
            ticket_id = cursor.lastrowid
        return {"id": ticket_id, "title": title, "status": "OPEN"}

    @app.patch("/api/tickets/{ticket_id}/status")
    def update_status(ticket_id: int, payload: StatusUpdate, user: dict = Depends(current_user)):
        if user["role"] != "AGENT":
            raise HTTPException(403, "Apenas agentes podem alterar o status")
        with db_conn(path) as con:
            changed = con.execute("UPDATE tickets SET status=? WHERE id=?", (payload.status, ticket_id)).rowcount
        if not changed:
            raise HTTPException(404, "Chamado não encontrado")
        return {"id": ticket_id, "status": payload.status}

    return app


app = create_app()
