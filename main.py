"""Vstopna točka: en proces, API in zajem zamud skupaj.

Gostitelji ta paket zaženejo na dva načina in oba delujeta:

    uvicorn main:app --host 0.0.0.0 --port $PORT   # gostitelj vodi strežnik
    python main.py                                 # strežnik zaženemo sami
"""
from __future__ import annotations

import os

# Pella in podobni naložijo ASGI objekt po imenu `main:app`, zato mora biti
# dosegljiv na ravni modula -- ne samo pod __main__.
from kajros.api import app

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
        workers=1,
        access_log=False,      # 0,1 jedra -- dnevnik dostopov je odveč
        log_level="info",
    )
