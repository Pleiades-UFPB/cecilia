"""Erros do subsistema de acesso remoto."""


class RemoteError(Exception):
    """Base para erros do subsistema remoto."""


class ValidationError(RemoteError):
    """Nome, versão, blob ou caminho fora do contrato."""


class PublishError(RemoteError):
    """Falha ao publicar um dataset."""
