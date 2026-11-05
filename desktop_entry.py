"""Windowed EXE entry point; no terminal or external browser is started."""
from pulsedeck.desktop import main

if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()
    raise SystemExit(main())
