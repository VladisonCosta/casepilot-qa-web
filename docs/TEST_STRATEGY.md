# Estratégia de Testes — CasePilot

**Contexto:** central de atendimento utilizada como SUT (System Under Test). Dados demo são fictícios.

## Pirâmide de testes

| Camada | Ferramenta | Escopo | Evidência |
|---|---|---|---|
| Backend | pytest/TestClient | login, sessão, permissões, contratos de endpoint, regras e validações | `backend-results.xml` |
| E2E web | Selenium 4/JUnit 5 | autenticação, tickets, filtros, mudança de status, controle por papel e logout | `target/surefire-reports`, `target/evidence` em falhas |
| Manual exploratório | Checklist | responsividade, acessibilidade, mensagens e usabilidade | `docs/EXPLORATORY.md` |

## Riscos e mitigação

- **Flakiness:** Page Objects, seletores estáveis `data-testid` e `WebDriverWait` em vez de `Thread.sleep`.
- **Dependência de estado:** títulos únicos com UUID, testes preparados para executar isolados, criação apenas com conta agente.
- **Sessões:** tokens temporários revogados no logout; não são salvos em arquivos do repositório.
- **Dados:** banco SQLite é descartável e ignorado pelo Git.
- **Confiabilidade CI:** Chrome headless, dependências pinadas por faixas ou versões, evidências JUnit sempre armazenadas.

## Critérios de aceite

1. Agente acessa listagem e registra chamados válidos.
2. Campos obrigatórios/limites bloqueiam entradas incompletas.
3. Busca e filtros retornam dados coerentes.
4. Agente muda status, visualizador não possui ação de mudança e servidor rejeita tentativa com 403.
5. Logout revoga token no backend.

## Limitações conhecidas (deliberadas)

O sistema de demonstração não oferece recuperação de senha, trilha de auditoria nem paginação; não deve ser usado com usuários reais ou exposto à internet. A interface guarda o token na memória de sessão do navegador. Os cards de métricas refletem a listagem filtrada (não totais globais) — uma escolha de demonstração a ser revisada em produto real.
