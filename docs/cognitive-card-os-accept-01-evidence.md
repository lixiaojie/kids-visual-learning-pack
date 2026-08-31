# Cognitive Card OS ACCEPT-01 Evidence

## Identity

- Server branch: `knowledge-pipeline-v1` @ `10b14c8`.
- Kids governance: `kids-visual-learning-pack` `main` @ `c5154c3` plus this evidence and ACCEPT-01 docs.
- Formal input: `examples/authoring/rabbit-real.json` (AUTHOR-02) + `examples/four-card-converter/rabbit-request.json` (rabbit, Shenzhen, age-5-6, bilingual, print).
- Actor: `owner`. Clock: `2026-08-31T04:00:00Z`.
- Work root: `/tmp/card-os-accept-01`.

## Chain

| Step | Result |
| --- | --- |
| Authoring overlay `projection.family=four-card` | Knowledge library `rabbit/revision-0001` |
| Browse | `/tmp/card-os-accept-01/browse/index.html` |
| Convert + AGE-01 | joined generation-input; child CN/EN from registry |
| Lock | `content_lock_sha256=sha256:f53f4e03863cd56fee560f85bcb2974ff4dbd2e4bd8b447f8fdb214338695f37` |
| Render | four A4 PNG + `print.pdf` (1,728,853 bytes) |
| Machine QA | `awaiting_review`, empty issues |
| Human review | `approved`, actor `owner` |
| Publish | package `rabbit` `revision-0001`, `package_sha256=sha256:c56a29475a585a1bf33a35beb306d64e2157e83910647ec0368f19c111c9b69f` |
| Local view | `/tmp/card-os-accept-01/view/index.html` contains the same lock digest |

Knowledge Core file SHA-256 after the whole chain: `sha256:49452c063f8ea88c9c02d8c8609181f68d325bdefea0af99244fab0019128c32`. Convert/lock/render/publish did not rewrite that file.

## Package files

`/tmp/card-os-accept-01/catalog/rabbit/revision-0001/` contains `cards/cn-observe.png`, `cards/en-observe.png`, `cards/cn-know.png`, `cards/en-know.png`, `print.pdf`, `manifest.json`, `qa-report.json`, `sources.json`.

Loopback preview used during this session: `http://127.0.0.1:8766/view/index.html` bound to 127.0.0.1 only. That is not PORTAL-01.

## Tests

- focused lock + accept: 9 PASS
- pipeline regression (accept/lock + publish + QA + renderer + AGE + converter + library/browse/HTTP library/joined/authoring): 118 PASS

## Caveats

- Lock assembler is a text-faithful projection, not a full `production-record-v1` generator. RUN-01 already closed the snapshot validator on a fixture record.
- Eight English knowledge sentences do not fit two equal mammal zones; the last handling sentence is packed into the sources zone after source ids. Chinese handling text remains visible on the CN knowledge page.
- Safety zone keeps Knowledge Core English originals (AGE-01 contract).
- `/tmp/card-os-accept-01` is a local run, not a git artifact. Re-run the CLI to recreate it.
- Server ACCEPT-01 code is locally committed as `10b14c8`; not merged to `main`.
