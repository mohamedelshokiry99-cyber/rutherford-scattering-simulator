# Security review — 2026-09-20 (Africa/Cairo)

Reviewed baseline: `9a5f74b45ac22f44d1591c24fa9e0b16030fd7e9`.

## Executive summary

No exploitable application vulnerability was confirmed in the reviewed source.
One repository-hygiene defect was reproduced and fixed. This is preventative
hardening, **not evidence of a credential leak or a remotely exploitable CVE**.
Four low-severity static-analysis alerts remain documented below.

The application is a local NumPy/matplotlib desktop simulator. The reviewed
entry point, GUI, and physics module contain no HTTP server, authentication
service, shell execution, or user-supplied file deserialization. This narrower
attack surface does not imply that dependencies or a compromised local machine
are harmless.

## Confirmed defect and fix

### H-01 — Repository ignore policy was inactive (low / preventative)

- Baseline file: `gitignore`, not `.gitignore`. Git did not apply its patterns.
- The intended `.env/` directory rule also would not exclude a regular `.env`
  credential file after a simple rename.
- Impact: accidental commits of local environment files, key material, virtual
  environments, and generated files were easier during normal Git workflows.
  No actual leaked credential was identified in the reviewed current files.
- Fix: rename to `.gitignore`; ignore `.env` variants, common private-key file
  extensions, `.venv`, and pytest cache. Placeholder `.env.example` and
  `.env.sample` remain trackable.
- Evidence: before the fix, the Git-based regression suite reported 13 failed
  path subtests; all those cases pass after the fix. Tests run in fresh temporary
  repositories with the user's global exclude file disabled.
- Limitation: ignore rules are not an access-control boundary. They do not affect
  already-tracked files and can be overridden with `git add -f`.

Reference: [Git's ignore-file documentation](https://git-scm.com/docs/gitignore).

## Dependency audit

`pip-audit 2.10.1` successfully resolved `requirements.txt` for Windows / Python
3.12.14 and returned **no known vulnerabilities for the 11 packages in its result**:

| Package | Audited version |
|---|---|
| contourpy | 1.4.0 |
| cycler | 0.12.1 |
| fonttools | 4.65.0 |
| kiwisolver | 1.5.1 |
| matplotlib | 3.11.2 |
| numpy | 2.5.3 |
| pillow | 12.3.0 |
| pyparsing | 3.3.2 |
| python-dateutil | 2.9.0.post0 |
| scipy | 1.18.1 |
| six | 1.17.0 |

The manifest is unpinned. These are the newly resolved versions, **not proof of
which versions are installed on an existing user's machine**. Other Python
versions and future installs may resolve differently. No dependency update is
claimed by this PR. Re-audit the actual environment before distributing it.

Reference: [pip-audit scope and limitations](https://github.com/pypa/pip-audit).

## Static-analysis triage

Bandit 1.9.4 scanned all three application modules: 1,006 lines of code, no scan
errors, no medium/high findings, and four low/high-confidence `B110` alerts in
`gui.py` at baseline lines 24, 67, 311, and 364:

| Location | Context | Assessment |
|---|---|---|
| 24 | Backend selection silently ignores failures | Diagnostic/reliability risk; no exploit demonstrated |
| 67 | Unsupported window-title operation is ignored | Optional GUI capability; no security impact demonstrated |
| 311 | Slider activation errors are ignored | Could hide UI-state failure; no security bypass demonstrated |
| 364 | Plot-artist removal errors are ignored | Could hide rendering failure; no exploit demonstrated |

These alerts have **not** been suppressed or described as fixed. Narrowing their
exception handling merits a separate GUI-tested change. The global warnings
filter in the GUI is another observability concern, not a proven vulnerability.

## Verification and limits

- `python -m pytest -q -p no:cacheprovider`: **8 passed, 17 subtests passed**.
- Standard-library runner: `python -m unittest discover -s tests -v`.
- Physics smoke checks: finite/default trajectory and energy conservation,
  mirrored paths, finite batch output, and high-energy nuclear contact.
- `python -m pip check`: no broken requirements in the verification environment.
- No application physics or GUI code changed in this PR.
- Native interactive GUI behavior, every scientific parameter edge case,
  every historical commit's contents, and other platforms were not exhaustively
  tested. No live service was attacked. A clean advisory result is not a security
  certification, malware scan, or proof that undisclosed flaws do not exist.

Reproduce the source/dependency scans in a separate environment:

```bash
python -m pip install -r requirements.txt bandit pip-audit
python -m bandit main.py physics_engine.py gui.py
python -m pip_audit -r requirements.txt
```

Bandit is expected to exit nonzero while the four documented low-severity alerts
remain; do not interpret that exit code as a clean scan.
