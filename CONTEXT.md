# CONTEXT.md — Current Project State

Quick-orientation doc for picking this project back up, or for an AI agent starting a fresh
session. Unlike `PLAN.md` (long-term design) and `AGENTS.md` (standing rules), **this file is
meant to be edited often** — update it at the end of a work session so the next session (yours or
an agent's) starts from an accurate picture, not a stale one.

If this file and `PLAN.md`/`AGENTS.md` ever disagree, `PLAN.md`/`AGENTS.md` are the source of
truth for *design* and *rules*; this file is only the source of truth for *what's actually done*.

---

## Where Things Stand

**Phase:** 0 — Setup (in progress)

**Last updated:** 2026-08-09

Repo has just been scaffolded via `uv init moc2pdf --package`. Docs (`README.md`, `PLAN.md`,
`AGENTS.md`, `LICENSE`) are in place. Module skeleton (`src/moc2pdf/*.py`) exists as empty files
matching the planned pipeline shape, but **no pipeline logic has been written yet**. WeasyPrint's
native dependency chain has been sanity-checked on macOS.

## Done

- [x] Project renamed/finalized as `moc2pdf`
- [x] `PLAN.md`, `README.md`, `AGENTS.md`, `LICENSE` (GPLv3) written
- [x] Package name, license (GPLv3), package manager (`uv`) all decided — see Key Decisions below
- [x] Cross-platform setup instructions (macOS + Linux, WSL2 for Windows) written into README
- [x] `uv init --package` run, `.python-version` pinned to 3.11
- [x] Core deps added: `python-frontmatter`, `jinja2`, `typer`; dev deps: `pytest`, `ruff`, `black`
- [x] `weasyprint` added and smoke-tested on macOS (native deps via Homebrew)
- [x] Module skeleton created: `vault_scanner.py`, `link_graph.py`, `moc_walker.py`, `transform.py`,
      `assembler.py`, `render.py`, `models.py`, `cli.py` (all empty stubs)
- [x] `.gitignore` covers `.envrc`, `*.pdf`, `__pycache__/`

## Not Done Yet

- [ ] `models.py` — no dataclasses (`Note`, `Link`, `ExportConfig`) written yet. **This is the
      next task** — everything downstream depends on these shapes.
- [ ] Fixture vault (`tests/fixtures/sample_vault/`) — no fake notes exist yet. Needs at least one
      cycle, one nested MOC, and one broken/unresolvable link (per `PLAN.md` §7).
- [ ] Every pipeline stage is an empty file — no vault scanning, link parsing, traversal,
      transformation, assembly, or rendering logic exists yet.
- [ ] No tests written (test files are empty stubs).
- [ ] No real export has been run against a real vault yet.

## Key Decisions Made So Far

These were explicitly decided during planning — don't re-litigate them without a reason, but they
*are* listed here (not buried in git history) so it's clear they were deliberate:

| Decision | Choice | Why |
|---|---|---|
| Package manager | `uv` | Single tool for venv + deps + running, faster than pip/venv |
| License | GPLv3 | Ensures forks/derivatives stay open source |
| Package name | `moc2pdf` | Renamed from initial placeholder `mocpdf` |
| Platform support | macOS + Linux equally; Windows via WSL2 only | Obsidian/Markdown are cross-platform, tooling should match; native Windows deferred to Phase 4+ |
| HTML→PDF renderer | WeasyPrint | Only mainstream option with real CSS-driven PDF bookmarks/internal links (see `PLAN.md` §4) |
| Graph library | None yet — hand-rolled DFS + `visited` set for Phase 1 | Avoid front-loading `networkx` before it's needed |
| Package layout | `src/moc2pdf/` (via `uv init --package`) | Proper installable layout from day one, not a flat script |

## Open Decisions (still unresolved — see `PLAN.md` §8)

These need an answer before or during Phase 1, and haven't been picked yet:

- Include-once vs. allow-duplicate for notes referenced from multiple places
- MOC nesting depth cap
- Cover page / metadata page — in scope for MVP or not?
- Embedded images: copied into a build folder, or referenced by absolute vault path?

## Immediate Next Step

Write `src/moc2pdf/models.py`: `Note`, `Link`, `ExportConfig` dataclasses. Once those shapes exist,
`vault_scanner.py` (Stage 1) is the next logical module, since every later stage consumes its
output.

## How to Update This File

At the end of a work session (or when an agent finishes a task), update:
1. **Where Things Stand** — phase and one-line summary, plus the date
2. **Done** / **Not Done Yet** — move checklist items across as they're actually completed *and
   tested*, not just written
3. **Key Decisions** — append a row if a new deliberate choice was made
4. **Immediate Next Step** — replace with whatever's genuinely next
5. **Understanding check** — for anything moved into "Done" that's a core pipeline stage (not
   boilerplate/config): could you re-derive it, out loud, without opening the file? If not, that's
   not a documentation gap, it's a signal to revisit the module with more of your own hands on it
   before calling it done. See `AGENTS.md` → Role Expectation for the assistance-vs-dependence
   guardrails this is meant to enforce.

Keep entries factual and short — this file is a snapshot, not a changelog. Git history already
covers the "how we got here"; this file only needs to answer "where are we now."