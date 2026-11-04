---
description: "CECILIA — current position and accumulated context"
type: ProjectState
about: "CECILIA"
---

# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-10-04)

**Core value:** O grupo aprende o pipeline completo — da consulta ao catálogo até a interpretação do modelo — de forma cientificamente correta e reprodutível.
**Current focus:** v0.1 Pipeline completo — Phase 02.5 (Acesso remoto aos dados)

## Current Position

Milestone: v0.1 Pipeline completo (v0.1.0)
Phase: 2.5 of 8 (Acesso remoto aos dados) — In Progress
Plan: 02.5-03 complete (3 de 4 previstos)
Status: Ready for next PLAN (02.5-04)
Last activity: 2026-11-04 16:25 — UNIFY 02.5-03, loop closed

Progress:
- Milestone: [░░░░░░░░░░] 5%
- Phase 02.5: [███████░░░] 75%

## Loop Position

Current loop state:
```
PLAN ──▶ APPLY ──▶ UNIFY
  ✓        ✓        ✓     [Loop complete - ready for next PLAN]
```

## Accumulated Context

### Decisions
- PROJECT.md populado a partir de `docs/PROJECT-BRIEF.md`
- Sem integrações opcionais (SonarQube, enterprise audit, special flows)
- Repositório conectado a github.com/Pleiades-UFPB/cecilia (main)
- Fase 1 dividida em 3 planos: 01-01 ambiente+CI, 01-02 aquecimento HR, 01-03 revisão do vocabulário
- CI no GitHub Actions incluído no 01-01 (escopo extra aprovado)
- Python 3.11 fixado; ruff E/F/I/UP/B; .claude e .paul fora do ruff (01-01)
- Milestone v0.1 com as 7 fases de `docs/ROADMAP-PROPOSTO.md`; Fase 8 adiada para v0.2
- Fase 02.5 (Acesso remoto aos dados) inserida no v0.1 em 2026-11-04: distribuição dos Parquets do servidor do lab
- Acesso remoto sem BD de dados: blob store + manifesto versionado; DuckDB lê Parquet no cliente
- Admin local no servidor (sem `/v1/admin`); chave HMAC-SHA256 com pepper, 90 dias; auditoria com IP por 90 dias
- Fase 1 pausada no plano 01-02; retomar após a fase 02.5 ou por decisão do grupo
- 02.5-01 concluído: blob store endereçado por SHA-256, manifesto imutável, catálogo e CLI `cecilia admin`
- Typer adotado para a CLI com `Annotated`; `rich` entrou como dependência transitiva, não como API
- Fase 02.5 usa branch de integração `feat/remoteAccess`: cada plano entra nela por PR e a fase entra na `main` por um PR único (desvio consciente do fluxo plano→main)
- 02.5-02 concluído: servidor FastAPI somente leitura com chave HMAC, Range/ETag, auditoria e limites
- Admin continua local (sem `/v1/admin`); o servidor só lê blobs e escreve chaves/auditoria
- Limite global só para requisições sem Bearer; tráfego autenticado usa limite por chave
- fastapi, uvicorn, anyio, httpx e rich nas dependências principais
- 02.5-03 concluído: cliente com login, catálogo, sync retomável, verify e doctor
- Sync deduplica blobs por hash; um único `.part` por conteúdo
- Credenciais do cliente em arquivo 0600; chave nunca em argv; HTTP remoto recusado por padrão
- Linhas do `data/README.md` são emitidas pelo sync, não gravadas automaticamente

### Deferred Issues
| Issue | Origin | Effort | Revisit |
|-------|--------|--------|---------|
| PendingDeprecationWarning do shap ao importar | 01-01 | S | Ao atualizar shap/matplotlib |
| Tornar check "CI" obrigatório na proteção da main | 01-01 | S | Após primeiro run verde |
| Confirmar disco (SSD/HDD) do servidor do lab | 02.5-01 | S | Antes do benchmark do 02.5-04 |
| Verificar IP de origem atrás do `tailscale serve` | 02.5-01 | S | 02.5-04 (auditoria) |
| Fechar nome dos datasets e raiz do servidor | 02.5-01 | S | 02.5-04 (operação) |
| Aviso de depreciação do TestClient sobre `httpx2` | 02.5-02 | S | Ao atualizar Starlette/FastAPI |
| Benchmark e throughput no servidor real | 02.5-03 | M | 02.5-04 |

### Blockers/Concerns
| Blocker | Impact | Resolution Path |
|---------|--------|-----------------|
| Servidor do lab ainda não configurado | Testes de rede e benchmark | Usar fixtures locais; validação real no 02.5-04 |

## Session Continuity

Last session: 2026-11-04 16:25
Stopped at: 02.5-03 concluído (cliente remoto, sync e verify)
Next action: /paul:plan para 02.5-04 (systemd, Tailscale Serve, docs e benchmark)
Resume file: .paul/phases/02.5-acesso-remoto/02.5-03-SUMMARY.md

---
*STATE.md — Updated after every significant action*
