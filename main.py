"""Vstopna točka za gostovanje (Pella in podobni): en proces, API + zajem.

    python main.py
"""
from __future__ import annotations

import os

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "sztrack.api:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
        workers=1,
        access_log=False,      # 0,1 jedra -- dnevnik dostopov je odveč
        log_level="info",
    )
