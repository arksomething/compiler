"""Compatibility wrapper for older `python -m compiler.main` usage."""

from .cli import main, scan_file

__all__ = ["main", "scan_file"]


if __name__ == "__main__":
    raise SystemExit(main())
