#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import stat
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


TLS_DIRECTIVE = "listen 443 ssl"
SERVER_NAME_DIRECTIVE = "server_name yutou.space www.yutou.space"
TOKEN_PATTERN = re.compile(r"\bserver\b|[{}]")


class InstallError(RuntimeError):
    pass


def strip_comments_preserving_offsets(text: str) -> str:
    parts: list[str] = []
    for line in text.splitlines(keepends=True):
        comment = line.find("#")
        if comment == -1:
            parts.append(line)
            continue
        newline_length = len(line) - len(line.rstrip("\r\n"))
        content_end = len(line) - newline_length
        parts.append(line[:comment])
        parts.append(" " * (content_end - comment))
        parts.append(line[content_end:])
    return "".join(parts)


def top_level_server_spans(text: str) -> list[tuple[int, int]]:
    stripped = strip_comments_preserving_offsets(text)
    spans: list[tuple[int, int]] = []
    depth = 0
    pending_server: int | None = None
    active_server: int | None = None

    for token in TOKEN_PATTERN.finditer(stripped):
        value = token.group(0)
        if value == "server":
            if depth == 0:
                pending_server = token.start()
            continue
        if value == "{":
            if depth == 0 and pending_server is not None:
                active_server = pending_server
            depth += 1
            pending_server = None
            continue

        if depth == 0:
            raise InstallError("unbalanced closing brace")
        depth -= 1
        if depth == 0:
            if active_server is not None:
                spans.append((active_server, token.end()))
                active_server = None
            pending_server = None

    if depth != 0:
        raise InstallError("unbalanced opening brace")
    return spans


def matching_tls_span(text: str) -> tuple[int, int]:
    stripped = strip_comments_preserving_offsets(text)
    matches = [
        span
        for span in top_level_server_spans(text)
        if TLS_DIRECTIVE in stripped[slice(*span)]
        and SERVER_NAME_DIRECTIVE in stripped[slice(*span)]
    ]
    if len(matches) != 1:
        raise InstallError(f"expected exactly one matching TLS server block; found {len(matches)}")
    return matches[0]


def content_with_include(text: str, include_line: str) -> str | None:
    start, end = matching_tls_span(text)
    stripped = strip_comments_preserving_offsets(text)
    block = stripped[start:end]
    include_count = block.count(include_line)
    if include_count == 1:
        return None
    if include_count > 1:
        raise InstallError("matching TLS server block contains the include more than once")

    server_name_at = block.find(SERVER_NAME_DIRECTIVE)
    if server_name_at == -1:
        raise InstallError("matching server_name line not found")
    absolute_at = start + server_name_at
    line_start = text.rfind("\n", start, absolute_at) + 1
    line_end = text.find("\n", absolute_at, end)
    if line_end == -1:
        line_end = end
        newline = "\n"
        insertion_at = line_end
        prefix = newline
    else:
        newline = "\r\n" if line_end > 0 and text[line_end - 1] == "\r" else "\n"
        insertion_at = line_end + 1
        prefix = ""
    indentation = re.match(r"[ \t]*", text[line_start:]).group(0)
    insertion = f"{prefix}{indentation}{include_line}{newline}"
    return text[:insertion_at] + insertion + text[insertion_at:]


def write_backup(backup_dir: Path, original: bytes) -> Path:
    backup_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_dir / f"yutou-space.{timestamp}.conf"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(backup_path, flags, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(original)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(descriptor)
    return backup_path


def atomic_replace(site_file: Path, content: bytes, mode: int) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{site_file.name}.", suffix=".tmp", dir=site_file.parent
    )
    temporary_path = Path(temporary_name)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.close(descriptor)
        descriptor = -1
        os.replace(temporary_path, site_file)
    finally:
        if descriptor != -1:
            os.close(descriptor)
        temporary_path.unlink(missing_ok=True)


def install(site_file: Path, include_line: str, backup_dir: Path) -> Path | None:
    original = site_file.read_bytes()
    try:
        text = original.decode("utf-8")
    except UnicodeDecodeError as error:
        raise InstallError("site file is not valid UTF-8") from error
    changed = content_with_include(text, include_line)
    if changed is None:
        return None

    site_mode = stat.S_IMODE(site_file.stat().st_mode)
    backup_path = write_backup(backup_dir, original)
    atomic_replace(site_file, changed.encode("utf-8"), site_mode)
    return backup_path


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(
        description="Safely add the Cognitive Card OS include to one Nginx TLS block."
    )
    argument_parser.add_argument("--site-file", required=True, type=Path)
    argument_parser.add_argument("--include-line", required=True)
    argument_parser.add_argument("--backup-dir", required=True, type=Path)
    return argument_parser


def main(arguments: list[str] | None = None) -> int:
    options = parser().parse_args(arguments)
    try:
        backup_path = install(
            site_file=options.site_file,
            include_line=options.include_line,
            backup_dir=options.backup_dir,
        )
    except (InstallError, OSError) as error:
        print(f"error={error}", file=sys.stderr)
        return 1
    if backup_path is None:
        print("status=unchanged")
    else:
        print(f"status=changed backup={backup_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
