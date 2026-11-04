"""Limites de requisição e de conexões simultâneas, em memória."""

from __future__ import annotations

import asyncio
import time
from collections import deque


class SlidingWindow:
    """Janela deslizante simples por chave (IP ou key_id)."""

    def __init__(self, limit: int, window_seconds: float = 60.0):
        if limit < 1:
            raise ValueError("limit deve ser >= 1")
        self._limit = limit
        self._window = window_seconds
        self._events: dict[str, deque[float]] = {}
        self._lock = asyncio.Lock()

    async def allow(self, key: str) -> bool:
        agora = time.monotonic()
        async with self._lock:
            fila = self._events.setdefault(key, deque())
            inicio = agora - self._window
            while fila and fila[0] <= inicio:
                fila.popleft()
            if len(fila) >= self._limit:
                return False
            fila.append(agora)
            return True


class KeyConcurrency:
    """Contador de streams simultâneos por chave."""

    def __init__(self, limit: int):
        if limit < 1:
            raise ValueError("limit deve ser >= 1")
        self._limit = limit
        self._counts: dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def acquire(self, key: str) -> bool:
        async with self._lock:
            atual = self._counts.get(key, 0)
            if atual >= self._limit:
                return False
            self._counts[key] = atual + 1
            return True

    async def release(self, key: str) -> None:
        async with self._lock:
            atual = self._counts.get(key, 0)
            if atual <= 1:
                self._counts.pop(key, None)
            else:
                self._counts[key] = atual - 1
