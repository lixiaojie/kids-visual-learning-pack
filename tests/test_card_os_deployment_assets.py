from __future__ import annotations

import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "ops" / "cognitive-card-server"
ENV_FILE = OPS / "env" / "card-os.env"
API_UNIT = OPS / "systemd" / "cognitive-card-server.service"
BACKUP_UNIT = OPS / "systemd" / "cognitive-card-backup.service"
BACKUP_TIMER = OPS / "systemd" / "cognitive-card-backup.timer"
NGINX_SNIPPET = OPS / "nginx" / "card-os.conf"
INSTALLER = OPS / "install_nginx_include.py"

INCLUDE_LINE = "include /etc/nginx/snippets/cognitive-card-server.conf;"

EXPECTED_ENV = """CARD_OS_DATABASE=/var/lib/cognitive-card-server/card-os.sqlite3
CARD_OS_CANDIDATE_ROOT=/var/lib/cognitive-card-server/candidates
CARD_OS_HOST=127.0.0.1
CARD_OS_PORT=8765
CARD_OS_MAX_REQUEST_BYTES=29360128
CARD_OS_MAX_DECODED_PAYLOAD_BYTES=20971520
"""

EXPECTED_API_UNIT = """[Unit]
Description=Cognitive Card OS API
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=60s
StartLimitBurst=5

[Service]
Type=simple
User=cardos
Group=cardos
UMask=0077
WorkingDirectory=/opt/cognitive-card-server/current
EnvironmentFile=/etc/cognitive-card-server/card-os.env
ExecStartPre=/usr/bin/test -d /var/lib/cognitive-card-server/candidates
ExecStart=/opt/cognitive-card-server/current/.venv/bin/cognitive-card-api
Restart=on-failure
RestartSec=5s
RuntimeDirectory=cognitive-card-server
RuntimeDirectoryMode=0700
RuntimeDirectoryPreserve=restart
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/cognitive-card-server /run/cognitive-card-server
CapabilityBoundingSet=
AmbientCapabilities=
RestrictAddressFamilies=AF_INET AF_INET6
SystemCallArchitectures=native

[Install]
WantedBy=multi-user.target
"""

EXPECTED_BACKUP_UNIT = """[Unit]
Description=Verified Cognitive Card OS backup
After=cognitive-card-server.service

[Service]
Type=oneshot
User=root
Group=root
UMask=0077
ExecStart=/usr/bin/python3 /opt/cognitive-card-server/current/ops/card_os_backup.py create --database /var/lib/cognitive-card-server/card-os.sqlite3 --candidate-root /var/lib/cognitive-card-server/candidates --backup-root /var/backups/cognitive-card-server --current-release /opt/cognitive-card-server/current --retention-days 14
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadOnlyPaths=/var/lib/cognitive-card-server
ReadWritePaths=/var/backups/cognitive-card-server
CapabilityBoundingSet=CAP_DAC_READ_SEARCH
AmbientCapabilities=CAP_DAC_READ_SEARCH

[Install]
WantedBy=multi-user.target
"""

EXPECTED_BACKUP_TIMER = """[Unit]
Description=Daily verified Cognitive Card OS backup

[Timer]
OnCalendar=*-*-* 03:20:00 Asia/Shanghai
Persistent=true
RandomizedDelaySec=10m
Unit=cognitive-card-backup.service

[Install]
WantedBy=timers.target
"""

EXPECTED_NGINX = """location = /card-os {
    return 308 /card-os/;
}

location = /card-os/ {
    access_log off;
    if ($request_method !~ ^(GET|HEAD)$) {
        return 405;
    }
    proxy_connect_timeout 5s;
    proxy_read_timeout 120s;
    proxy_send_timeout 120s;
    proxy_pass http://127.0.0.1:8765;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location = /card-os/skill/v1/manifest.json {
    access_log off;
    if ($request_method !~ ^(GET|HEAD)$) {
        return 405;
    }
    autoindex off;
    add_header Cache-Control "no-cache" always;
    alias /var/www/cognitive-card-skill-registry/v1/manifest.json;
}

location = /card-os/skill/v1/install.sh {
    access_log off;
    if ($request_method !~ ^(GET|HEAD)$) {
        return 405;
    }
    autoindex off;
    add_header Cache-Control "no-cache" always;
    alias /var/www/cognitive-card-skill-registry/v1/installer-current/install.sh;
}

location = /card-os/skill/v1/install.sh.sha256 {
    access_log off;
    if ($request_method !~ ^(GET|HEAD)$) {
        return 405;
    }
    autoindex off;
    add_header Cache-Control "no-cache" always;
    alias /var/www/cognitive-card-skill-registry/v1/installer-current/install.sh.sha256;
}

location ^~ /card-os/skill/v1/installers/ {
    access_log off;
    if ($request_method !~ ^(GET|HEAD)$) {
        return 405;
    }
    autoindex off;
    add_header Cache-Control "public, max-age=31536000, immutable" always;
    alias /var/www/cognitive-card-skill-registry/v1/installers/;
    try_files $uri =404;
}

location ^~ /card-os/skill/v1/manifests/ {
    access_log off;
    if ($request_method !~ ^(GET|HEAD)$) {
        return 405;
    }
    autoindex off;
    add_header Cache-Control "public, max-age=31536000, immutable" always;
    alias /var/www/cognitive-card-skill-registry/v1/manifests/;
    try_files $uri =404;
}

location ^~ /card-os/skill/v1/releases/ {
    access_log off;
    if ($request_method !~ ^(GET|HEAD)$) {
        return 405;
    }
    autoindex off;
    add_header Cache-Control "public, max-age=31536000, immutable" always;
    alias /var/www/cognitive-card-skill-registry/v1/releases/;
    try_files $uri =404;
}

location ^~ /card-os/api/ {
    access_log off;
    client_max_body_size 30m;
    proxy_connect_timeout 5s;
    proxy_read_timeout 120s;
    proxy_send_timeout 120s;
    proxy_pass http://127.0.0.1:8765;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location ^~ /card-os/packages/ {
    access_log off;
    if ($request_method !~ ^(GET|HEAD)$) {
        return 405;
    }
    proxy_connect_timeout 5s;
    proxy_read_timeout 120s;
    proxy_send_timeout 120s;
    proxy_pass http://127.0.0.1:8765;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location ^~ /card-os/ {
    access_log off;
    return 404;
}
"""


def parse_nginx_location_blocks(nginx: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    pattern = re.compile(r"location\s+((?:=|\^~)\s+\S+)\s*\{")
    for match in pattern.finditer(nginx):
        depth = 1
        cursor = match.end()
        while cursor < len(nginx) and depth:
            if nginx[cursor] == "{":
                depth += 1
            elif nginx[cursor] == "}":
                depth -= 1
            cursor += 1
        if depth:
            raise AssertionError(f"unterminated Nginx location: {match.group(1)}")
        blocks[match.group(1)] = nginx[match.end() : cursor - 1]
    return blocks


SITE_FIXTURE = """# A comment containing braces must not affect parsing: { }
server {
    listen 80;
    server_name yutou.space www.yutou.space;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name yutou.space www.yutou.space;

    location / {
        try_files $uri $uri/ =404;
    }
}
"""


class CardOsDeploymentAssetTests(unittest.TestCase):
    def read_asset(self, path: Path) -> str:
        if not path.is_file():
            self.fail(f"missing deployment asset: {path.relative_to(ROOT)}")
        return path.read_text(encoding="utf-8")

    def test_environment_file_is_complete_and_contains_no_credentials(self) -> None:
        environment = self.read_asset(ENV_FILE)

        self.assertEqual(EXPECTED_ENV, environment)
        self.assertNotIn("Authorization", environment)
        self.assertNotIn("root@", environment)
        self.assertIsNone(re.search(r"ccos_v1\.", environment))

    def test_api_unit_matches_hardened_contract(self) -> None:
        unit = self.read_asset(API_UNIT)

        self.assertEqual(EXPECTED_API_UNIT, unit)
        unit_section, service_and_install = unit.split("[Service]", maxsplit=1)
        self.assertIn("StartLimitIntervalSec=60s", unit_section)
        self.assertIn("StartLimitBurst=5", unit_section)
        self.assertNotIn("StartLimitIntervalSec", service_and_install)
        self.assertNotIn("StartLimitBurst", service_and_install)
        self.assertIn("RuntimeDirectoryPreserve=restart", unit)
        self.assertEqual(
            ["CapabilityBoundingSet=", "AmbientCapabilities="],
            [
                line
                for line in unit.splitlines()
                if line.startswith(("CapabilityBoundingSet=", "AmbientCapabilities="))
            ],
        )
        for forbidden in ("0.0.0.0", "root@", "Authorization"):
            self.assertNotIn(forbidden, unit)
        self.assertIsNone(re.search(r"ccos_v1\.", unit))

    def test_backup_service_and_timer_match_hardened_contract(self) -> None:
        service = self.read_asset(BACKUP_UNIT)
        timer = self.read_asset(BACKUP_TIMER)

        self.assertEqual(EXPECTED_BACKUP_UNIT, service)
        self.assertEqual(EXPECTED_BACKUP_TIMER, timer)
        self.assertIn("User=root", service)
        self.assertIn("Group=root", service)
        self.assertIn("PrivateTmp=true", service)
        self.assertIn("ReadOnlyPaths=/var/lib/cognitive-card-server", service)
        self.assertEqual(
            ["ReadWritePaths=/var/backups/cognitive-card-server"],
            [line for line in service.splitlines() if line.startswith("ReadWritePaths=")],
        )
        self.assertEqual(
            [
                "CapabilityBoundingSet=CAP_DAC_READ_SEARCH",
                "AmbientCapabilities=CAP_DAC_READ_SEARCH",
            ],
            [
                line
                for line in service.splitlines()
                if line.startswith(("CapabilityBoundingSet=", "AmbientCapabilities="))
            ],
        )

    def test_nginx_snippet_matches_routing_contract(self) -> None:
        nginx = self.read_asset(NGINX_SNIPPET)

        self.assertEqual(EXPECTED_NGINX, nginx)
        self.assertIn("location = /card-os", nginx)
        self.assertIn("return 308 /card-os/", nginx)
        self.assertIn("location = /card-os/", nginx)
        self.assertNotIn("return 307 /card-os/api/v1/capabilities", nginx)
        self.assertIn("location ^~ /card-os/packages/", nginx)
        self.assertIn("location ^~ /card-os/api/", nginx)
        self.assertIn("proxy_pass http://127.0.0.1:8765;", nginx)
        self.assertIn("client_max_body_size 30m", nginx)
        self.assertIn("access_log off", nginx)
        self.assertNotIn("/var/lib/cognitive-card-server/candidates", nginx)

    def test_nginx_registry_is_exactly_read_only_and_fail_closed(self) -> None:
        nginx = self.read_asset(NGINX_SNIPPET)
        blocks = parse_nginx_location_blocks(nginx)
        registry_root = "/var/www/cognitive-card-skill-registry/v1/"
        active_aliases = {
            "= /card-os/skill/v1/manifest.json": registry_root + "manifest.json",
            "= /card-os/skill/v1/install.sh": (
                registry_root + "installer-current/install.sh"
            ),
            "= /card-os/skill/v1/install.sh.sha256": (
                registry_root + "installer-current/install.sh.sha256"
            ),
        }
        immutable_aliases = {
            "^~ /card-os/skill/v1/installers/": registry_root + "installers/",
            "^~ /card-os/skill/v1/manifests/": registry_root + "manifests/",
            "^~ /card-os/skill/v1/releases/": registry_root + "releases/",
        }

        self.assertEqual(
            set(active_aliases) | set(immutable_aliases),
            {selector for selector in blocks if "/card-os/skill/v1/" in selector},
        )
        api_offset = nginx.index("location ^~ /card-os/api/")
        catch_all_offset = nginx.index("location ^~ /card-os/ {")
        for selector in (*active_aliases, *immutable_aliases):
            body = blocks[selector]
            self.assertLess(nginx.index(f"location {selector} {{"), api_offset)
            self.assertLess(nginx.index(f"location {selector} {{"), catch_all_offset)
            self.assertIn("access_log off;", body)
            self.assertIn("if ($request_method !~ ^(GET|HEAD)$)", body)
            self.assertEqual(1, body.count("return 405;"))
            self.assertIn("autoindex off;", body)
            self.assertNotIn("proxy_pass", body)
            self.assertNotIn("limit_except", body)
            self.assertNotIn("error_page", body)
            self.assertNotIn("rewrite", body)
            for private_name in (
                "candidate",
                "database",
                "sqlite",
                "backup",
                "staging",
                "journal",
            ):
                self.assertNotIn(private_name, body.lower())

        for selector, alias in active_aliases.items():
            body = blocks[selector]
            self.assertIn('add_header Cache-Control "no-cache" always;', body)
            self.assertIn(f"alias {alias};", body)
            self.assertNotIn("try_files", body)

        for selector, alias in immutable_aliases.items():
            body = blocks[selector]
            self.assertIn(
                'add_header Cache-Control "public, max-age=31536000, immutable" always;',
                body,
            )
            self.assertIn(f"alias {alias};", body)
            self.assertIn("try_files $uri =404;", body)

        registry_text = "\n".join(
            blocks[selector] for selector in (*active_aliases, *immutable_aliases)
        )
        self.assertEqual(6, registry_text.count(f"alias {registry_root}"))
        self.assertNotIn("root ", registry_text)

    def test_non_api_card_os_namespace_selects_deny_only_catch_all(self) -> None:
        nginx = self.read_asset(NGINX_SNIPPET)
        blocks = parse_nginx_location_blocks(nginx)

        def selected_location(uri: str) -> str | None:
            exact = f"= {uri}"
            if exact in blocks:
                return exact
            prefixes = [
                selector
                for selector in blocks
                if selector.startswith("^~ ") and uri.startswith(selector[3:])
            ]
            return max(prefixes, key=lambda selector: len(selector[3:]), default=None)

        sensitive_looking_paths = (
            "/card-os/card-os.sqlite3",
            "/card-os/candidates/",
            "/card-os/card-os.env",
            "/card-os/backups/",
            "/card-os/skill/v1/candidates/",
            "/card-os/skill/v1/card-os.sqlite3",
            "/card-os/skill/v1/backups/",
            "/card-os/skill/v1/staging/",
            "/card-os/skill/v1/journal/",
        )
        for uri in sensitive_looking_paths:
            with self.subTest(uri=uri):
                self.assertEqual("^~ /card-os/", selected_location(uri))

        deny_body = blocks.get("^~ /card-os/", "")
        self.assertIn("access_log off;", deny_body)
        self.assertIn("return 404;", deny_body)
        for file_serving_directive in ("alias ", "root ", "try_files ", "proxy_pass "):
            self.assertNotIn(file_serving_directive, deny_body)

        self.assertEqual(
            "^~ /card-os/api/",
            selected_location("/card-os/api/v1/health"),
        )
        self.assertEqual(
            "^~ /card-os/api/",
            selected_location("/card-os/api/v1/capabilities"),
        )
        self.assertEqual("= /card-os/", selected_location("/card-os/"))
        self.assertEqual(
            "^~ /card-os/packages/",
            selected_location("/card-os/packages/rabbit"),
        )
        self.assertEqual(
            "^~ /card-os/packages/",
            selected_location(
                "/card-os/packages/rabbit/revisions/0001/files/print.pdf"
            ),
        )
        for selector in ("= /card-os/", "^~ /card-os/packages/"):
            body = blocks[selector]
            self.assertIn("proxy_pass http://127.0.0.1:8765;", body)
            self.assertIn("if ($request_method !~ ^(GET|HEAD)$)", body)
            self.assertNotIn("alias ", body)
            self.assertNotIn("root ", body)
            self.assertNotIn("try_files ", body)
        self.assertEqual(
            "^~ /card-os/skill/v1/releases/",
            selected_location(
                "/card-os/skill/v1/releases/0.1.0/cognitive-card-os.zip"
            ),
        )


class NginxIncludeInstallerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.base = Path(self.temporary_directory.name)
        self.site_file = self.base / "site.conf"
        self.backup_dir = self.base / "backups"
        self.backup_dir.mkdir()

    def invoke(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                os.fspath(INSTALLER),
                "--site-file",
                os.fspath(self.site_file),
                "--include-line",
                INCLUDE_LINE,
                "--backup-dir",
                os.fspath(self.backup_dir),
            ],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_modifies_only_unique_tls_block_and_creates_private_exact_backup(self) -> None:
        original = SITE_FIXTURE.encode("utf-8")
        self.site_file.write_bytes(original)

        process = self.invoke()

        self.assertEqual(0, process.returncode, process.stderr)
        changed = self.site_file.read_text(encoding="utf-8")
        expected_tls_line = (
            "    server_name yutou.space www.yutou.space;\n"
            f"    {INCLUDE_LINE}\n"
        )
        self.assertEqual(1, changed.count(INCLUDE_LINE))
        self.assertIn(expected_tls_line, changed)
        port_80, tls = changed.split("server {", maxsplit=2)[1:]
        self.assertNotIn(INCLUDE_LINE, port_80)
        self.assertIn(INCLUDE_LINE, tls)

        backups = list(self.backup_dir.iterdir())
        self.assertEqual(1, len(backups))
        self.assertRegex(
            backups[0].name,
            r"^yutou-space\.\d{8}T\d{6}Z\.conf$",
        )
        self.assertEqual(original, backups[0].read_bytes())
        self.assertEqual(0o600, stat.S_IMODE(backups[0].stat().st_mode))
        self.assertIn(os.fspath(backups[0]), process.stdout)

        first_changed_bytes = self.site_file.read_bytes()
        second = self.invoke()
        self.assertEqual(0, second.returncode, second.stderr)
        self.assertEqual("status=unchanged\n", second.stdout)
        self.assertEqual(first_changed_bytes, self.site_file.read_bytes())
        self.assertEqual(backups, list(self.backup_dir.iterdir()))

    def test_zero_matching_tls_blocks_fails_without_writing(self) -> None:
        original = SITE_FIXTURE.replace("listen 443 ssl;", "listen 8443 ssl;")
        self.site_file.write_text(original, encoding="utf-8")

        process = self.invoke()

        self.assertNotEqual(0, process.returncode)
        self.assertEqual(original.encode("utf-8"), self.site_file.read_bytes())
        self.assertEqual([], list(self.backup_dir.iterdir()))

    def test_two_matching_tls_blocks_fail_without_writing(self) -> None:
        duplicated_tls = "server {" + SITE_FIXTURE.rsplit("server {", maxsplit=1)[1]
        original = SITE_FIXTURE + "\n" + duplicated_tls
        self.site_file.write_text(original, encoding="utf-8")

        process = self.invoke()

        self.assertNotEqual(0, process.returncode)
        self.assertEqual(original.encode("utf-8"), self.site_file.read_bytes())
        self.assertEqual([], list(self.backup_dir.iterdir()))


if __name__ == "__main__":
    unittest.main()
