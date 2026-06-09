"""Entry point for `python -m granola_sync` / `granola-sync`."""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(prog="granola-sync")
    parser.add_argument(
        "--tkinter",
        action="store_true",
        help="Launch the V1 Tkinter GUI instead of the new pywebview frontend.",
    )
    parser.add_argument(
        "--frontend-url",
        default=None,
        help="Load the frontend from this URL (e.g. http://localhost:5173 "
             "during development). Defaults to the bundled frontend/dist.",
    )
    args = parser.parse_args()

    if args.tkinter:
        from .gui import main as gui_main
        gui_main()
        return

    from .app import launch
    launch(dev_url=args.frontend_url)


if __name__ == "__main__":
    main()
