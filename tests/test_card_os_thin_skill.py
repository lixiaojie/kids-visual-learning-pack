"""Content/contract tests for the cognitive-card-os thin Skill instructions.

These tests pin the production teaching contract of the five-file Skill
closure: ``SKILL.md`` teaches only the workflow, ``references/protocol.md``
carries the wire contract, ``references/errors.md`` enumerates every frozen
error code, ``agents/openai.yaml`` stays consistent, and the repository
``README.md`` documents the verified four-step bootstrap.

Error-code assertions extract backtick-quoted code tokens from the docs and
compare them to the frozen sets with SET EQUALITY, never a loose subset.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "cognitive-card-os"
SKILL_MD = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
PROTOCOL_MD = (SKILL_ROOT / "references" / "protocol.md").read_text(
    encoding="utf-8"
)
ERRORS_MD = (SKILL_ROOT / "references" / "errors.md").read_text(encoding="utf-8")
OPENAI_YAML = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
README_MD = (ROOT / "README.md").read_text(encoding="utf-8")

# Frozen 0.3.1 client-visible server-code contract snapshot, copied from app
# commit c2a898cba5b8a8948c06688d8c2a387353d7cbbe. Mirrors SERVER_ERROR_CODES
# in scripts/card_os_client.py; 57 codes in five groups.
SERVER_CODE_GROUPS = {
    "auth/protocol": frozenset(
        {
            "AUTH_REQUIRED", "AUTH_INVALID", "AUTH_EXPIRED",
            "AUTH_SCOPE_REQUIRED", "AUTH_REVOKED", "CLIENT_UPGRADE_REQUIRED",
            "SERVER_UPGRADE_REQUIRED", "INVALID_SKILL_RELEASE",
        }
    ),
    "request/http": frozenset(
        {
            "REQUEST_VALIDATION_FAILED", "REQUEST_TOO_LARGE",
            "PAYLOAD_TOO_LARGE", "UNSUPPORTED_MEDIA_TYPE",
            "UNSUPPORTED_CONTENT_ENCODING", "ROUTE_NOT_FOUND",
            "METHOD_NOT_ALLOWED", "HTTP_ERROR", "INTERNAL_ERROR",
        }
    ),
    "packet/state": frozenset(
        {
            "JOB_NOT_FOUND", "PACKET_NOT_FOUND", "PACKET_ALREADY_CLAIMED",
            "PACKET_EXPIRED", "LEASE_EXPIRED", "LEASE_OWNER_MISMATCH",
            "INVALID_STATE_TRANSITION", "INVALID_CLIENT_ID", "CLIENT_REVOKED",
            "INVALID_PACKET_LIMIT", "INVALID_LEASE_DURATION",
        }
    ),
    "result/artifact": frozenset(
        {
            "INVALID_IDEMPOTENCY_KEY", "IDEMPOTENCY_CONFLICT",
            "SKILL_RELEASE_MISMATCH", "INVALID_BASE64", "MISSING_ARTIFACT",
            "UNDECLARED_ARTIFACT", "UNSAFE_ARTIFACT_PATH",
            "ARTIFACT_MEDIA_TYPE_MISMATCH", "ARTIFACT_SIZE_MISMATCH",
            "ARTIFACT_TOO_LARGE", "ARTIFACT_DIGEST_MISMATCH",
            "UNSUPPORTED_ARTIFACT_MEDIA_TYPE", "INVALID_ARTIFACT_MEDIA",
            "UNSAFE_ARTIFACT_COMPRESSION", "CONTENT_LOCK_MISMATCH",
            "PACKET_PROFILE_MISMATCH", "RESULT_CLIENT_MISMATCH",
            "STAGED_METADATA_MISMATCH",
        }
    ),
    "server-integrity": frozenset(
        {
            "CANDIDATE_DIGEST_MISMATCH", "CANDIDATE_STORE_CLOSED",
            "CANDIDATE_STORE_REQUIRED", "INVALID_STORAGE_KEY",
            "UNSAFE_CANDIDATE_STORE", "FORBIDDEN_CREDENTIAL_FIELD",
            "FORBIDDEN_CREDENTIAL_VALUE", "NON_CANONICAL_JSON",
            "DATABASE_CONSTRAINT_VIOLATION", "INVALID_UTC_CLOCK",
            "INVALID_UTC_TIMESTAMP",
        }
    ),
}
SERVER_CODES = frozenset().union(*SERVER_CODE_GROUPS.values())

# Frozen local production codes. UNSAFE_ARCHIVE is frozen by the plan but
# reserved: card_os_client.py 0.1.0 emits the other nine.
LOCAL_PRODUCTION_CODES = frozenset(
    {
        "TRUSTED_UPSTREAM_REQUIRED", "REDIRECT_REFUSED", "TLS_REQUIRED",
        "DIGEST_MISMATCH", "UNSAFE_ARCHIVE", "CREDENTIAL_IN_RESULT",
        "ATTEMPT_BODY_CHANGED", "CREDENTIAL_STORE_UNAVAILABLE",
        "CREDENTIAL_STORE_UNSAFE", "SERVER_CONTRACT_DRIFT",
    }
)

# Documented but never emitted by card_os_client.py (installer-only).
INSTALLER_ONLY_CODES = frozenset({"UNMANAGED_ACTIVE_SKILL"})

ALL_DOCUMENTED_CODES = SERVER_CODES | LOCAL_PRODUCTION_CODES | INSTALLER_ONLY_CODES

# Skeleton-only code that must not survive into the 0.1.0 production source.
RETIRED_CODES = frozenset({"CLIENT_NOT_RELEASED"})

_CODE_TOKEN_RE = re.compile(r"`([A-Z][A-Z0-9_]{2,63})`")
_HEADING_RE = re.compile(r"^(#{2,3})\s+(.*)$", re.MULTILINE)


def extract_backtick_codes(text: str) -> set[str]:
    """Backtick-quoted ALL-CAPS tokens are the documented code tokens."""
    return set(_CODE_TOKEN_RE.findall(text))


def extract_section(text: str, heading: str, *, level: int) -> str:
    """Return the body under ``heading`` up to the next same/higher heading."""
    prefix = "#" * level
    matches = list(_HEADING_RE.finditer(text))
    for index, match in enumerate(matches):
        if match.group(1) == prefix and match.group(2).strip() == heading:
            start = match.end()
            for following in matches[index + 1 :]:
                if len(following.group(1)) <= level:
                    return text[start : following.start()]
            return text[start:]
    raise AssertionError(f"missing section heading: {prefix} {heading}")


class SkillMdTests(unittest.TestCase):
    def test_frontmatter_is_name_and_description_only(self) -> None:
        self.assertTrue(SKILL_MD.startswith("---\n"))
        _, frontmatter, body = SKILL_MD.split("---\n", maxsplit=2)
        fields = {}
        for line in frontmatter.splitlines():
            key, separator, value = line.partition(":")
            self.assertEqual(":", separator, f"invalid frontmatter line: {line!r}")
            fields[key.strip()] = value.strip()
        self.assertEqual({"name", "description"}, set(fields))
        self.assertEqual("cognitive-card-os", fields["name"])
        self.assertTrue(fields["description"])
        self.assertTrue(body.strip())

    def test_skill_md_stays_concise(self) -> None:
        _, _, body = SKILL_MD.split("---\n", maxsplit=2)
        self.assertLessEqual(
            len(body.encode("utf-8")),
            8192,
            "SKILL.md must stay concise; wire detail belongs in references/",
        )
        self.assertLessEqual(len(body.splitlines()), 120)

    def test_skill_md_links_only_the_two_references(self) -> None:
        targets = set(re.findall(r"\]\(([^)\s]+)\)", SKILL_MD))
        self.assertEqual(
            {"references/protocol.md", "references/errors.md"}, targets
        )

    def test_skill_md_teaches_the_workflow_in_order(self) -> None:
        order = [
            "doctor",
            "packets list",
            "packets claim",
            "packets get",
            "packets complete",
            "results submit",
        ]
        position = -1
        for step in order:
            following = SKILL_MD.find(step, position + 1)
            self.assertNotEqual(-1, following, f"missing workflow step: {step}")
            self.assertGreater(following, position)
            position = following
        self.assertIn("generate", SKILL_MD.lower())

    def test_skill_md_makes_automatic_submit_primary(self) -> None:
        self.assertRegex(SKILL_MD, r"(?i)automatic submit[^\n]*primary")

    def test_skill_md_states_chatgpt_pro_needs_no_openai_api_key(self) -> None:
        self.assertIn("ChatGPT Pro", SKILL_MD)
        self.assertRegex(
            SKILL_MD,
            r"(?i)(no|without an?) OpenAI API key",
        )
        # The uppercase env-var shape is forbidden anywhere in the source.
        self.assertNotIn("OPENAI" + "_API_KEY", SKILL_MD)

    def test_skill_md_fails_free_concepts_closed(self) -> None:
        self.assertIn("TRUSTED_UPSTREAM_REQUIRED", SKILL_MD)
        self.assertRegex(SKILL_MD, r"(?i)free concept")
        self.assertRegex(SKILL_MD, r"(?i)do not synthesize a lock")

    def test_skill_md_prohibitions_and_no_publication_claim(self) -> None:
        self.assertRegex(SKILL_MD, r"(?i)do not[^.\n]*admin")
        self.assertRegex(SKILL_MD, r"(?i)do not[^.\n]*publish")
        self.assertRegex(SKILL_MD, r"(?i)do not[^.\n]*ChatGPT identity")
        self.assertIn("candidate_staged", SKILL_MD)
        self.assertRegex(SKILL_MD, r"(?i)never a publication")

    def test_skill_md_has_the_first_version_decision_table(self) -> None:
        for row in (
            "packet ID present",
            "no packet ID",
            "free concept only",
            "candidate directory ready",
        ):
            self.assertIn(row, SKILL_MD)
        self.assertIn("| Input state | Action |", SKILL_MD)

    def test_retired_skeleton_code_is_gone(self) -> None:
        for name, content in (
            ("SKILL.md", SKILL_MD),
            ("references/protocol.md", PROTOCOL_MD),
            ("references/errors.md", ERRORS_MD),
            ("agents/openai.yaml", OPENAI_YAML),
        ):
            for code in RETIRED_CODES:
                self.assertNotIn(code, content, name)


class ProtocolReferenceTests(unittest.TestCase):
    def test_enumerates_the_exact_command_surface(self) -> None:
        commands = [
            "python3 scripts/card_os_client.py doctor",
            "python3 scripts/card_os_client.py auth set --stdin [--allow-file-store]",
            "python3 scripts/card_os_client.py auth status",
            "python3 scripts/card_os_client.py auth delete",
            "python3 scripts/card_os_client.py packets list",
            "python3 scripts/card_os_client.py packets claim PACKET_ID",
            "python3 scripts/card_os_client.py packets get PACKET_ID --output FILE",
            "python3 scripts/card_os_client.py packets complete PACKET_ID",
            "python3 scripts/card_os_client.py results submit PACKET_ID --directory DIR",
            "python3 scripts/card_os_client.py jobs status JOB_ID",
            "python3 scripts/card_os_client.py jobs events JOB_ID",
        ]
        for command in commands:
            self.assertIn(command, PROTOCOL_MD)

    def test_enumerates_the_exact_routes(self) -> None:
        routes = [
            "GET /card-os/api/v1/health",
            "GET /card-os/api/v1/capabilities",
            "GET /card-os/api/v1/packets/available",
            "POST /card-os/api/v1/packets/<packet_id>/claim",
            "GET /card-os/api/v1/packets/<packet_id>",
            "POST /card-os/api/v1/packets/<packet_id>/complete",
            "POST /card-os/api/v1/packets/<packet_id>/results",
            "GET /card-os/api/v1/jobs/<job_id>",
            "GET /card-os/api/v1/jobs/<job_id>/events",
        ]
        for route in routes:
            self.assertIn(route, PROTOCOL_MD)
        self.assertIn("https://www.yutou.space/card-os/", PROTOCOL_MD)

    def test_enumerates_the_protected_headers(self) -> None:
        self.assertIn("Authorization: Bearer", PROTOCOL_MD)
        self.assertIn("X-Card-OS-Protocol: 1", PROTOCOL_MD)
        self.assertIn("X-Card-OS-Skill-Release: 0.1.0", PROTOCOL_MD)
        self.assertIn("Idempotency-Key", PROTOCOL_MD)

    def test_enumerates_the_schemas(self) -> None:
        for schema in (
            "cognitive-card-capabilities-v1",
            "cognitive-card-generation-packet-v1",
            "cognitive-card-generation-result-v1",
            "cognitive-card-submit-attempt-v1",
        ):
            self.assertIn(schema, PROTOCOL_MD)

    def test_enumerates_digest_and_idempotency_algorithms(self) -> None:
        self.assertIn("packet_digest", PROTOCOL_MD)
        self.assertRegex(
            PROTOCOL_MD,
            r'"sha256:" \+ sha256\(',
        )
        self.assertIn("sort_keys=True", PROTOCOL_MD)
        self.assertIn('separators=(",", ":")', PROTOCOL_MD)
        self.assertIn("ccos-v1-", PROTOCOL_MD)
        self.assertRegex(
            PROTOCOL_MD,
            r'sha256\(packet_id \+ "\\n" \+ canonical',
        )

    def test_enumerates_the_size_limits(self) -> None:
        self.assertIn("20 MiB", PROTOCOL_MD)
        self.assertIn("28 MiB", PROTOCOL_MD)

    def test_documents_client_surface_and_attempt_journal(self) -> None:
        self.assertIn("codex-cli", PROTOCOL_MD)
        self.assertIn("CLIENT_SURFACE", PROTOCOL_MD)
        self.assertIn("cognitive-card-submit-attempt-v1", PROTOCOL_MD)

    def test_documents_magic_byte_only_checks_and_pil_authority(self) -> None:
        self.assertRegex(PROTOCOL_MD, r"(?i)magic[- ]byte")
        self.assertIn("PIL", PROTOCOL_MD)
        self.assertIn("INVALID_ARTIFACT_MEDIA", PROTOCOL_MD)

    def test_documents_free_concept_classification(self) -> None:
        self.assertIn("TRUSTED_UPSTREAM_REQUIRED", PROTOCOL_MD)
        self.assertRegex(PROTOCOL_MD, r"(?i)free")
        self.assertRegex(PROTOCOL_MD, r"(?i)whitespace")
        self.assertRegex(PROTOCOL_MD, r"(?i)non-ASCII")


class ErrorsReferenceTests(unittest.TestCase):
    def test_every_server_group_matches_the_frozen_set_exactly(self) -> None:
        for group, expected in SERVER_CODE_GROUPS.items():
            with self.subTest(group=group):
                section = extract_section(ERRORS_MD, group, level=3)
                self.assertEqual(expected, extract_backtick_codes(section))

    def test_local_codes_match_the_frozen_set_exactly(self) -> None:
        section = extract_section(ERRORS_MD, "Local client codes", level=2)
        self.assertEqual(LOCAL_PRODUCTION_CODES, extract_backtick_codes(section))

    def test_packet_not_found_documents_cross_invocation_replay(self) -> None:
        section = extract_section(ERRORS_MD, "packet/state", level=3)
        self.assertRegex(section, r"(?i)cross-invocation")
        self.assertRegex(section, r"(?i)invisible to the claimant")
        # Gate I-1 reconciliation: with a valid attempt journal and unchanged
        # files the cross-invocation submit replays (replayed=true); without
        # a journal it fails closed.
        self.assertRegex(section, r"(?i)attempt journal")
        self.assertRegex(section, r"(?i)replayed=true")
        self.assertRegex(section, r"(?i)fails closed")

    def test_installer_only_codes_are_marked_not_emitted(self) -> None:
        section = extract_section(ERRORS_MD, "Installer-only codes", level=2)
        self.assertEqual(INSTALLER_ONLY_CODES, extract_backtick_codes(section))
        self.assertRegex(section, r"(?i)not emitted")
        self.assertIn("card_os_client.py", section)

    def test_reference_union_is_exactly_the_documented_code_universe(self) -> None:
        documented = extract_backtick_codes(PROTOCOL_MD) | extract_backtick_codes(
            ERRORS_MD
        )
        self.assertEqual(ALL_DOCUMENTED_CODES, documented)
        self.assertEqual(57, len(SERVER_CODES))
        self.assertTrue(RETIRED_CODES.isdisjoint(documented))


class OpenAiYamlTests(unittest.TestCase):
    def _interface(self) -> dict[str, str]:
        match = re.search(
            r"^interface:\n((?:  .+\n)+)", OPENAI_YAML, re.MULTILINE
        )
        self.assertIsNotNone(match, "openai.yaml must have an interface block")
        fields: dict[str, str] = {}
        for line in match.group(1).splitlines():
            key, separator, value = line.strip().partition(":")
            self.assertEqual(":", separator, f"invalid line: {line!r}")
            fields[key.strip()] = value.strip().strip('"')
        return fields

    def test_interface_fields_are_present(self) -> None:
        fields = self._interface()
        self.assertEqual(
            {"display_name", "short_description", "default_prompt"},
            set(fields),
        )
        self.assertEqual("Cognitive Card OS", fields["display_name"])

    def test_interface_is_consistent_with_skill_md(self) -> None:
        fields = self._interface()
        self.assertRegex(
            fields["short_description"], r"(?i)upload candidates"
        )
        self.assertIn("$cognitive-card-os", fields["default_prompt"])
        self.assertRegex(fields["default_prompt"], r"(?i)claim")
        self.assertRegex(fields["default_prompt"], r"(?i)locked task")
        # Consistent with the SKILL.md teaching: automatic upload, no API key.
        self.assertRegex(SKILL_MD, r"(?i)automatic submit")
        self.assertNotIn("CLIENT_NOT_RELEASED", OPENAI_YAML)


class ReadmeBootstrapTests(unittest.TestCase):
    BOOTSTRAP_LINES = (
        "curl -q --proto '=https' --tlsv1.2 --location --max-redirs 0 "
        "--fail --silent --show-error --remote-name "
        "https://www.yutou.space/card-os/skill/v1/install.sh",
        "curl -q --proto '=https' --tlsv1.2 --location --max-redirs 0 "
        "--fail --silent --show-error --remote-name "
        "https://www.yutou.space/card-os/skill/v1/install.sh.sha256",
        "shasum -a 256 -c install.sh.sha256",
        "bash install.sh --channel stable",
    )

    def test_readme_identifies_source_and_release_authorities(self) -> None:
        self.assertIn("私有 GitHub", README_MD)
        self.assertRegex(README_MD, r"源码权威")
        self.assertIn("https://www.yutou.space/card-os/", README_MD)
        self.assertRegex(README_MD, r"可安装.{0,12}权威")

    def test_readme_documents_isolated_codex_home(self) -> None:
        self.assertIn("CODEX_HOME", README_MD)
        self.assertRegex(README_MD, r"隔离")

    def test_readme_has_the_exact_four_step_bootstrap(self) -> None:
        for line in self.BOOTSTRAP_LINES:
            self.assertIn(line, README_MD)

    def test_bootstrap_first_curl_argument_is_q(self) -> None:
        curl_lines = [
            line
            for line in README_MD.splitlines()
            if line.startswith("curl ") and "install.sh" in line
        ]
        self.assertEqual(2, len(curl_lines))
        for line in curl_lines:
            self.assertEqual("-q", line.split()[1])
            self.assertIn("--proto '=https'", line)
            self.assertIn("--tlsv1.2", line)
            self.assertIn("--location --max-redirs 0", line)

    def test_readme_rejects_shortened_or_piped_install(self) -> None:
        self.assertNotIn("curl -fsSLO", README_MD)
        self.assertNotIn("curl -sSL", README_MD)
        self.assertNotIn("curl | sh", README_MD)
        self.assertNotIn("| sh", README_MD)

    def test_readme_never_advises_overwriting_the_active_skill(self) -> None:
        path = "~/.codex/skills/cognitive-card-os"
        self.assertIn(path, README_MD)
        for line in README_MD.splitlines():
            if path in line:
                self.assertRegex(
                    line,
                    r"(不要|do not|Do not|never)",
                    f"line mentions the active Skill path without a prohibition: {line}",
                )


if __name__ == "__main__":
    unittest.main()
