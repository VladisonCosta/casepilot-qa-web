# Evidências de validação local — 19/10/2026

- Testes do backend: `python -m pytest -q tests/backend` → **10 passed**.
- Sintaxe dos arquivos Python: validada via compilação (`compileall`).
- Selenium Java + Maven: **não executados localmente** (Maven ausente neste ambiente e o navegador de testes recebeu bloqueio administrativo ao acessar servidores). A suíte está completa em `automation/` e deve ser validada no GitHub Actions após o push.
- Preview `docs/assets/casepilot-dashboard.png`: imagem ilustrativa gerada usando o layout HTML/CSS e 3 tickets sintéticos inseridos no DOM, **não é evidência de E2E executado**.
- Docker / GitHub Actions: arquivos fornecidos, execução ainda não verificada neste ambiente.

Para confirmar: `python -m pytest tests/backend` e `cd automation; mvn test -Dheadless=true` com a aplicação servida em `http://localhost:8000`.
