#!/usr/bin/env python3
"""Ukazna vrstica: python cli.py slika.png --debug"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from flange_picker.config import load_config
from flange_picker.pipeline import process_file, result_to_json_string


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Detekcija prirobnic za bin picking iz ene slike")
    parser.add_argument("image", help="pot do vhodne slike")
    parser.add_argument("--config", default=None, help="pot do config.yaml")
    parser.add_argument("--debug", action="store_true", help="zapisi overlay slike v debug/")
    parser.add_argument("--debug-dir", default=None, help="mapa za debug slike")
    parser.add_argument("--out", default=None, help="zapisi JSON v datoteko namesto na stdout")
    parser.add_argument("--top", type=int, default=None, help="omeji stevilo kandidatov")
    args = parser.parse_args(argv)

    cfg = load_config(args.config)
    if args.top is not None:
        cfg.set("output.max_candidates", args.top)
    logging.basicConfig(level=getattr(logging, str(cfg["logging.level"]).upper(), logging.INFO),
                        format="%(levelname)s %(name)s: %(message)s")

    result = process_file(args.image, cfg, debug=args.debug, debug_dir=args.debug_dir)
    text = result_to_json_string(result, cfg)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
    else:
        print(text)
    for warning in result.warnings:
        print(f"opozorilo: {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
