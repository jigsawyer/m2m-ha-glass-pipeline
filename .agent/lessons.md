# Experience Memory Bank — Operational Lessons

> Durable cross-session environment memory (ADR-0062).
> Read before shell commands, environment checks, or code generation.
> Constraints here take precedence over default agent assumptions.
>
> Schema per lesson (mandatory):
> - **Symptom / Failure Trigger**
> - **Operational Reality**
> - **Correct Action / Rule**
>
> After resolving a new unexpected environment failure: Self-Reflect → dedupe → append.
> Promote validated lessons to `.cursorrules` / ADRs in scheduled review (ADR-0064);
> mark `- **Status:** Promoted → ADR-XXXX` / `Promoted → .cursorrules` or remove graduates.
> Review hygiene: `python -m pipeline.harness lessons-status`.

---

## Lesson: Authenticated GitHub CLI may be absent

- **Symptom / Failure Trigger:** `gh` missing, unauthenticated, or remote GitHub
  operations fail when creating a PR / pushing via assumed CLI auth.
- **Operational Reality:** This host may lack an authenticated `gh` (or equivalent
  verified GitHub interface). Agent scope ends at a verified local commit when
  remote auth is unavailable (ADR-0061).
- **Correct Action / Rule:** On first detection, stage verified local work, create
  the local commit if authorized by the fail-fast protocol, halt remote delivery,
  and hand off with a compare URL / operator-CI instructions. Do not install or
  reconfigure `gh`; do not retry alternate bootstrap paths.

---

## Lesson: Harness MCP stdio needs project venv

- **Symptom / Failure Trigger:** Execution Harness MCP (`m2m-ha-glass-harness`)
  fails to start or import (`mcp` / `jsonpatch` missing, wrong interpreter).
- **Operational Reality:** MCP stdio dependencies live in the project `.venv`
  (`mcp`, `jsonpatch`) and require `PYTHONPATH=.` from the repo root.
- **Correct Action / Rule:** Invoke the harness with the project `.venv` Python
  and `PYTHONPATH=.`. Do not install packages into the system Python unless the
  task explicitly authorizes host dependency changes (ADR-0061).

---

## Lesson: Sandbox DNS can block `git fetch` / GitHub

- **Symptom / Failure Trigger:** `git fetch` / SSH to `github.com` fails with
  hostname resolution errors (e.g. `Could not resolve hostname github.com`)
  inside a restricted sandbox.
- **Operational Reality:** Some agent command sandboxes deny outbound DNS/SSH to
  GitHub even when the operator host itself can reach the remote.
- **Correct Action / Rule:** Re-run the same git remote command with full network
  / unsandboxed permissions once. If it still fails, treat as an environment
  restriction: fail-fast per ADR-0061 — do not invent alternate remotes or
  credential hacks.

---

## Lesson: Apple Git rejects injected `--trailer` on commit

- **Symptom / Failure Trigger:** `git commit` fails with
  `error: unknown option \`trailer'\` (exit 129) even with a normal `-m` /
  HEREDOC message.
- **Operational Reality:** Host ships Apple Git 2.24.x, which lacks
  `git commit --trailer`. Some agent/IDE commit wrappers inject `--trailer`,
  which this binary rejects.
- **Correct Action / Rule:** Commit with `/usr/bin/git commit -F <msgfile>` (no
  `--trailer`). Do not upgrade/reinstall git unless the task authorizes host
  dependency changes.
