#!/usr/bin/env python3
from __future__ import annotations

import sys


def main() -> int:
    sys.stderr.write('{"error":{"code":"CLIENT_NOT_RELEASED"}}\n')
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
