#!/usr/bin/env python3
"""Atalho para o pacote scripts/pandora_press (PANDORA PRESS-SUITE Ω)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pandora_press.__main__ import main  # noqa: E402

if __name__ == '__main__':
    sys.exit(main())
