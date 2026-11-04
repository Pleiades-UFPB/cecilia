"""Servidor HTTP somente leitura dos datasets publicados."""

import asyncio
import json
import logging
import re
import time
from functools import partial
from pathlib import Path
from typing import Annotated
from uuid import uuid4

import anyio
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from cecilia import __version__

from .audit import AuditEntry, AuditLog
from .auth import KeyStore, Principal, parse_token
from .errors import RemoteError, ValidationError
from .hashing import sha256_json
from .index import BlobIndex
from .layout import BLOB_PATTERN, validate_dataset, validate_version
from .manifest import load_manifest
from .ratelimit import KeyConcurrency, SlidingWindow
from .settings import Settings

logger = logging.getLogger(__name__)

TRANSFER_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
USER_AGENT_LIMIT = 200
CATALOG_MAX_AGE = 30
MANIFEST_MAX_AGE = 300
BLOB_MAX_AGE = 31_536_000


class AuditMiddleware:
    """Conta bytes reais e grava a auditoria mesmo quando o cliente aborta."""

    def __init__(self, app: ASGIApp, audit: AuditLog, trust_proxy: bool):
        self.app = app
        self._audit = audit
        self._trust_proxy = trust_proxy

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("path") == "/health":
            return await self.app(scope, receive, send)

        state = scope.setdefault("cecilia", {})
        state.setdefault("request_id", uuid4().hex)
        state.setdefault("audit", {})
        state["transfer_id"] = _transfer_id(scope)
        inicio = time.perf_counter()
        status = 500
        bytes_sent = 0

        async def send_wrapper(message: Message) -> None:
            nonlocal status, bytes_sent
            if message["type"] == "http.response.start":
                status = message["status"]
            elif message["type"] == "http.response.body":
                bytes_sent += len(message.get("body", b""))
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            with anyio.CancelScope(shield=True):
                release = state.get("release")
                if release is not None:
                    await release()
                principal = state.get("principal")
                info = state.get("audit", {})
                entrada = AuditEntry(
                    request_id=state["request_id"],
                    transfer_id=state.get("transfer_id"),
                    alias=principal.alias if principal is not None else None,
                    key_id=principal.key_id if principal is not None else state.get("key_id"),
                    action=info.get("action", "http"),
                    path=scope.get("path"),
                    dataset=info.get("dataset"),
                    version=info.get("version"),
                    file=info.get("file"),
                    blob=info.get("blob"),
                    bytes_sent=bytes_sent,
                    status=status,
                    duration_ms=int((time.perf_counter() - inicio) * 1000),
                    client_ip=_client_ip(scope, self._trust_proxy),
                    user_agent=_user_agent(scope),
                )
                try:
                    await asyncio.to_thread(self._audit.record, entrada)
                except Exception:
                    logger.exception("falha ao gravar auditoria")


class GlobalRateLimitMiddleware:
    """Limite por IP antes da autenticação, só para requisições sem Bearer."""

    def __init__(self, app: ASGIApp, limiter: SlidingWindow, trust_proxy: bool):
        self.app = app
        self._limiter = limiter
        self._trust_proxy = trust_proxy

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("path") == "/health":
            return await self.app(scope, receive, send)
        if _bearer_from_scope(scope) is not None:
            return await self.app(scope, receive, send)

        state = scope.setdefault("cecilia", {})
        ip = _client_ip(scope, self._trust_proxy) or "desconhecido"
        if not await self._limiter.allow(ip):
            state["audit"] = {"action": "rate-limit"}
            resposta = JSONResponse(
                {"detail": "limite de requisições excedido"},
                status_code=429,
            )
            return await resposta(scope, receive, send)
        return await self.app(scope, receive, send)


def create_app(settings: Settings) -> FastAPI:
    """Monta o app FastAPI com auth, auditoria, limites e rotas de leitura."""
    layout = settings.layout
    layout.prepare()

    keys = KeyStore(layout, settings.pepper)
    audit = AuditLog(layout)
    audit.prune(settings.audit_retention_days)
    index = BlobIndex(layout)

    catalogo_limite = SlidingWindow(settings.catalog_per_minute)
    blob_limite = SlidingWindow(settings.blob_per_minute)
    limite_global = SlidingWindow(settings.global_per_minute)
    concorrencia = KeyConcurrency(settings.max_streams_per_key)

    app = FastAPI(
        title="CECILIA",
        version=__version__,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.settings = settings
    app.state.keys = keys
    app.state.audit = audit
    app.state.index = index

    app.add_middleware(
        GlobalRateLimitMiddleware, limiter=limite_global, trust_proxy=settings.trust_proxy
    )
    app.add_middleware(AuditMiddleware, audit=audit, trust_proxy=settings.trust_proxy)

    async def current_principal(request: Request) -> Principal:
        state = request.scope.setdefault("cecilia", {})
        token = _extract_token(request)
        if token is None:
            state["audit"] = {"action": "auth"}
            raise HTTPException(
                status_code=401,
                detail="chave ausente",
                headers={"WWW-Authenticate": "Bearer"},
            )
        principal = await asyncio.to_thread(keys.verify, token)
        if principal is None:
            partes = parse_token(token)
            if partes is not None:
                state["key_id"] = partes[0]
            state["audit"] = {"action": "auth"}
            raise HTTPException(
                status_code=401,
                detail="chave inválida, expirada ou revogada",
                headers={"WWW-Authenticate": "Bearer"},
            )
        state["principal"] = principal
        if not await concorrencia.acquire(principal.key_id):
            state["audit"] = {"action": "concurrency"}
            raise HTTPException(
                status_code=429,
                detail="limite de conexões simultâneas excedido",
            )
        state["release"] = partial(concorrencia.release, principal.key_id)
        return principal

    async def enforce_rate(
        request: Request,
        principal: Principal,
        limiter: SlidingWindow,
    ) -> None:
        if not await limiter.allow(principal.key_id):
            request.scope["cecilia"]["audit"] = {"action": "rate-limit"}
            raise HTTPException(
                status_code=429,
                detail="limite de requisições excedido",
            )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/v1/catalog")
    async def catalog(
        request: Request,
        principal: Annotated[Principal, Depends(current_principal)],
    ) -> Response:
        await enforce_rate(request, principal, catalogo_limite)
        try:
            data = await asyncio.to_thread(_read_json, layout.catalog)
        except (OSError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=503, detail="catálogo indisponível") from exc

        etag = f'"{sha256_json(data.get("datasets", []))}"'
        request.scope["cecilia"]["audit"] = {"action": "catalog"}
        if request.headers.get("if-none-match") == etag:
            return Response(status_code=304, headers={"ETag": etag})
        return JSONResponse(
            data,
            headers={"ETag": etag, "Cache-Control": f"private, max-age={CATALOG_MAX_AGE}"},
        )

    @app.get("/v1/datasets/{dataset}/versions/{version}")
    async def manifest(
        dataset: str,
        version: str,
        request: Request,
        principal: Annotated[Principal, Depends(current_principal)],
    ) -> Response:
        await enforce_rate(request, principal, catalogo_limite)
        request.scope["cecilia"]["audit"] = {
            "action": "manifest",
            "dataset": dataset,
            "version": version,
        }
        try:
            validate_dataset(dataset)
            validate_version(version)
        except ValidationError as exc:
            raise HTTPException(status_code=404, detail="dataset ou versão desconhecido") from exc

        caminho = layout.manifest_path(dataset, version)
        try:
            data = await asyncio.to_thread(load_manifest, caminho)
        except RemoteError as exc:
            raise HTTPException(status_code=404, detail="dataset ou versão desconhecido") from exc

        etag = f'"{data.digest()}"'
        if request.headers.get("if-none-match") == etag:
            return Response(status_code=304, headers={"ETag": etag})
        return JSONResponse(
            data.to_dict(),
            headers={"ETag": etag, "Cache-Control": f"private, max-age={MANIFEST_MAX_AGE}"},
        )

    @app.get("/v1/blobs/{blob}")
    async def blob(
        blob: str,
        request: Request,
        principal: Annotated[Principal, Depends(current_principal)],
    ) -> Response:
        await enforce_rate(request, principal, blob_limite)
        request.scope["cecilia"]["audit"] = {"action": "blob"}
        if not BLOB_PATTERN.fullmatch(blob):
            raise HTTPException(status_code=404, detail="blob desconhecido")

        referencias = await asyncio.to_thread(index.lookup, blob)
        if not referencias:
            referencias = await asyncio.to_thread(lambda: index.lookup(blob, force=True))
        if not referencias:
            raise HTTPException(status_code=404, detail="blob desconhecido")

        caminho = layout.blobs / blob
        if not caminho.is_file():
            raise HTTPException(status_code=404, detail="blob indisponível")

        referencia = referencias[0]
        request.scope["cecilia"]["audit"] = {
            "action": "blob",
            "dataset": referencia.dataset,
            "version": referencia.version,
            "file": referencia.path,
            "blob": blob,
        }

        etag = f'"{blob}"'
        if request.headers.get("if-none-match") == etag:
            return Response(status_code=304, headers={"ETag": etag})
        return FileResponse(
            caminho,
            media_type="application/octet-stream",
            headers={
                "ETag": etag,
                "Cache-Control": f"private, max-age={BLOB_MAX_AGE}, immutable",
            },
        )

    @app.get("/v1/whoami")
    async def whoami(
        request: Request,
        principal: Annotated[Principal, Depends(current_principal)],
    ) -> dict[str, str]:
        await enforce_rate(request, principal, catalogo_limite)
        request.scope["cecilia"]["audit"] = {"action": "whoami"}
        return {
            "alias": principal.alias,
            "key_id": principal.key_id,
            "expires_at": principal.expires_at,
        }

    return app


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _header(scope: Scope, nome: bytes) -> str | None:
    for chave, valor in scope.get("headers", []):
        if chave.lower() == nome:
            return valor.decode("latin-1")
    return None


def _extract_token(request: Request) -> str | None:
    header = request.headers.get("authorization", "")
    if not header.lower().startswith("bearer "):
        return None
    token = header[7:].strip()
    return token or None


def _bearer_from_scope(scope: Scope) -> str | None:
    header = _header(scope, b"authorization")
    if header is None or not header.lower().startswith("bearer "):
        return None
    token = header[7:].strip()
    return token or None


def _transfer_id(scope: Scope) -> str | None:
    valor = _header(scope, b"x-cecilia-transfer-id")
    if valor is None or not TRANSFER_ID_PATTERN.fullmatch(valor):
        return None
    return valor


def _user_agent(scope: Scope) -> str | None:
    valor = _header(scope, b"user-agent")
    if valor is None:
        return None
    return valor[:USER_AGENT_LIMIT]


def _client_ip(scope: Scope, trust_proxy: bool) -> str | None:
    # VERIFICAR no servidor: confirmar se o tailscale serve envia X-Forwarded-For.
    if trust_proxy:
        encaminhado = _header(scope, b"x-forwarded-for")
        if encaminhado:
            return encaminhado.split(",")[0].strip()
    cliente = scope.get("client")
    return cliente[0] if cliente else None


__all__ = ["create_app"]
