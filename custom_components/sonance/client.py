"""Async TCP client for Sonance DSP amplifiers."""
from __future__ import annotations

import asyncio
import re

CONNECT_TIMEOUT = 5.0
RESPONSE_TIMEOUT = 1.5
GRACE = 0.15  # extra wait after expected text matched, to collect trailing bytes


class SonanceError(Exception):
    """Communication error."""


class SonanceClient:
    """Persistent connection; one command/response exchange at a time."""

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()

    async def _connect(self) -> None:
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), CONNECT_TIMEOUT
            )
        except (OSError, asyncio.TimeoutError) as err:
            raise SonanceError(f"Cannot connect to {self.host}:{self.port}: {err}") from err

    async def close(self) -> None:
        if self._writer is not None:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except OSError:
                pass
        self._reader = self._writer = None

    async def _drain_pending(self) -> None:
        """Discard unsolicited data left in the buffer."""
        assert self._reader is not None
        try:
            while True:
                data = await asyncio.wait_for(self._reader.read(1024), 0.01)
                if not data:
                    raise SonanceError("Connection closed by amplifier")
        except asyncio.TimeoutError:
            return

    async def send(
        self,
        frame: bytes,
        expect: re.Pattern[str] | None = None,
        required: bool = True,
    ) -> str:
        """Send a frame; return feedback text.

        If ``expect`` is given, return as soon as it matches (plus a short grace
        period); otherwise collect until the line goes quiet / timeout.
        """
        async with self._lock:
            for attempt in (0, 1):
                try:
                    if self._writer is None or self._writer.is_closing():
                        await self._connect()
                    await self._drain_pending()
                    assert self._writer is not None
                    self._writer.write(frame)
                    await self._writer.drain()
                    return await self._read(expect, required)
                except (OSError, SonanceError) as err:
                    await self.close()
                    if attempt:
                        raise SonanceError(str(err)) from err
        raise SonanceError("unreachable")  # pragma: no cover

    async def _read(self, expect: re.Pattern[str] | None, required: bool) -> str:
        assert self._reader is not None
        loop = asyncio.get_running_loop()
        deadline = loop.time() + RESPONSE_TIMEOUT
        buf = ""
        matched = False
        while True:
            remaining = deadline - loop.time()
            if remaining <= 0:
                break
            wait = min(remaining, GRACE) if matched else remaining
            try:
                data = await asyncio.wait_for(self._reader.read(1024), wait)
            except asyncio.TimeoutError:
                break
            if not data:
                raise SonanceError("Connection closed by amplifier")
            buf += data.decode("ascii", errors="replace")
            if expect is None or expect.search(buf):
                matched = True
        if not buf and required:
            raise SonanceError("No response from amplifier")
        return buf
