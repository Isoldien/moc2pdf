# Project Plan — Obsidian MOC → PDF Exporter

## 1. The Problem, Precisely

You have a Zettelkasten vault in Obsidian. Concepts live as atomic notes. A **Map of Content (MOC)**
note links out to the notes that belong to a topic, and those notes may link to each other or to
further sub-MOCs. This structure is *the point* — it's what makes Zettelkasten useful — but it only
works inside a tool that understands `[[wikilinks]]`.

Your university's submission system doesn't run Obsidian or render Markdown. It does accept PDFs,
and PDFs support internal hyperlinks/bookmarks. So the actual engineering problem is:

> Given a starting MOC note, walk its link graph, collect every note it (transitively) points to,
> stitch them into one linear document in a sensible order, rewrite the `[[wikilinks]]` so they
> become **internal PDF links/bookmarks** instead of dead references, and render the whole thing
> to a single, properly formatted, navigable PDF.

Everything below is designed around that sentence.

---

## 2. Core Concepts You're Actually Building

Strip away the file formats and this is a classic **graph traversal + document transformation
pipeline**. Three distinct problems, worth keeping mentally separate even though they'll live in
the same repo:

1. **Graph problem** — parse a vault into a link graph, then walk it from a root node, handling
   cycles (Zettelkasten notes *will* link back to each other) and deciding an output order (DFS
   traversal, likely, so an MOC's sub-links appear as sub-sections).
2. **Transformation problem** — Obsidian Markdown isn't vanilla Markdown. Wikilinks, embeds
   (`![[image.png]]`), callouts (`> [!note]`), block references (`^block-id`), and YAML
   frontmatter all need to be normalised into something a standard Markdown/HTML renderer
   understands, *before* rendering.
3. **Rendering problem** — HTML/Markdown → PDF where internal anchors survive as clickable,
   bookmarked links, not just visually-styled text.

Solving these separately (rather than one script that does everything) is what will make this
maintainable and testable.

---

## 3. Proposed Architecture

```
vault (Obsidian) 
   │
   ▼
[1] vault_scanner      — index all .md files, extract frontmatter, note titles, aliases
   │
   ▼
[2] link_graph         — parse [[wikilinks]] & ![[embeds]] per note, build a directed graph
   │
   ▼
[3] moc_walker         — DFS/BFS from a chosen root note, dedupe, detect cycles, produce
   │                      an ORDERED LIST of notes to include (this defines the PDF's structure)
   ▼
[4] markdown_transform — per note: rewrite wikilinks → internal anchor links, resolve embeds
   │                      to actual image paths, strip/convert Obsidian-only syntax
   ▼
[5] doc_assembler      — concatenate transformed notes into one Markdown/HTML doc with a
   │                      generated Table of Contents, section headers, and anchor IDs
   ▼
[6] pdf_renderer       — HTML → PDF, preserving anchors as PDF internal links + bookmarks
   │
   ▼
output.pdf
```

Each stage is a pure function/module: input in, structured data out. That means each one is
independently unit-testable without needing a real Obsidian vault or a PDF renderer running.

### Suggested package layout (for when you do start coding)

```
moc2pdf/
├── moc2pdf/
│   ├── __init__.py
│   ├── vault_scanner.py     # Stage 1
│   ├── link_graph.py        # Stage 2
│   ├── moc_walker.py        # Stage 3
│   ├── transform.py         # Stage 4
│   ├── assembler.py         # Stage 5
│   ├── render.py            # Stage 6
│   ├── models.py            # dataclasses: Note, LinkGraph, ExportConfig
│   └── cli.py                # entry point
├── templates/
│   └── export.html.j2        # Jinja2 HTML shell + CSS for the PDF
├── tests/
│   ├── fixtures/
│   │   └── sample_vault/     # a tiny fake vault checked into the repo, for tests
│   ├── test_vault_scanner.py
│   ├── test_link_graph.py
│   ├── test_moc_walker.py
│   └── test_transform.py
├── pyproject.toml
├── README.md
├── AGENTS.md
└── PLAN.md
```

---

## 4. Requirements & Library Choices

| Need | Library | Why |
|---|---|---|
| Parse YAML frontmatter | `python-frontmatter` | Handles the `---` metadata block Obsidian puts at the top of notes |
| Markdown parsing/rendering | `markdown-it-py` (with plugin ecosystem) | More extensible than stdlib `markdown` for custom syntax (callouts, wikilinks) |
| Wikilink/embed parsing | custom regex module (`transform.py`) | Obsidian's `[[link|alias]]`, `![[embed]]`, `[[link#heading]]` syntax isn't standard — no library does this well, and it's a good learning exercise |
| Graph handling | `networkx` (optional, Phase 2+) | Cycle detection and traversal utilities once the graph gets non-trivial. Phase 1 can hand-roll DFS with a `visited` set — no need to reach for it immediately |
| Templating | `Jinja2` | Build the final HTML shell (TOC, styling, note sections) cleanly, separate from Python logic |
| HTML → PDF | `WeasyPrint` | Pure-Python, CSS-driven, and — critically — supports `bookmark-level`/`bookmark-label` CSS properties so headings become real PDF bookmarks, and `<a href="#anchor">` becomes a real internal PDF link. This is the single most important library choice, see note below. |
| CLI | `typer` (or `argparse` if you want zero dependencies) | Clean CLI ergonomics: `moc2pdf export "My MOC"` |
| Pretty console output | `rich` | Nice-to-have, not essential |
| Testing | `pytest` | You've used this before (ln2xhtml) — same approach applies here |
| Packaging & env management | `uv` | Handles venv creation, dependency resolution/locking, and running commands (`uv run`) in one tool — faster and simpler than juggling `pip` + `venv` separately |

### Platform Target

Primary development is on **macOS**, but **Linux is an equally supported target, not an
afterthought** — Obsidian and Markdown are both cross-platform by nature, and this tool should
match that rather than assume everyone's on the maintainer's OS. WeasyPrint's system dependencies
(Pango, Cairo, GDK-Pixbuf) install cleanly via Homebrew on macOS and via `apt`/`dnf`/`pacman` on
mainstream Linux distros; both paths get explicit setup instructions in `README.md`. **Windows**
support runs through **WSL2** — since WSL2 is a real Linux userspace, this isn't a third code path
to maintain, it's the same Linux path applied inside a Windows-hosted VM. A native (non-WSL2)
Windows build, which would require a different approach to WeasyPrint's dependency chain entirely,
is a Phase 4+/stretch concern, not before.

### Why WeasyPrint over alternatives

- **`pandoc` + LaTeX**: Best-in-class typography, but Obsidian-flavoured Markdown → clean LaTeX is
  its own can of worms, and debugging LaTeX errors is a poor use of your time here.
- **`markdown-pdf` / `wkhtmltopdf`-based tools**: wkhtmltopdf is unmaintained and internal-link
  support is flaky.
- **WeasyPrint**: You write normal HTML + CSS (which you already know from web dev), it's pure
  Python (no external binary dependency headaches), and it has first-class support for the exact
  thing this project needs — PDF bookmarks and internal anchor links driven straight from HTML.

---

## 5. The Hard Parts (worth thinking about before you write a line of code)

1. **Cycle handling** — Zettelkasten notes are *designed* to link to each other non-hierarchically.
   A naive recursive walk will infinite-loop. You need a `visited` set and a decision: do you
   include a note only once (at first encounter) and link back to it on subsequent references, or
   do you allow controlled duplication? (Recommendation: include once, all later references become
   internal links back to that one instance — this mirrors how Obsidian's own graph works and keeps
   the PDF from ballooning.)
2. **Wikilink resolution ambiguity** — Obsidian resolves `[[Note Name]]` by matching titles/aliases
   across the *entire* vault, not just linked notes. Your `vault_scanner` needs a title→file index
   built from the whole vault (or at least everything reachable) before you can resolve any link.
3. **Ordering** — DFS order is natural but you may want MOC sub-sections to visually nest (e.g. as
   H2s under the MOC's H1) rather than just appearing as a flat sequence. Decide the document's
   heading hierarchy early — it drives both the TOC and the PDF bookmarks.
4. **Embeds** — `![[image.png]]` and `![[Other Note]]` (note transclusion) are different things.
   The former is an image path to resolve and copy/reference; the latter means literally inlining
   another note's content at that point, which interacts with your cycle-handling logic.
5. **Non-portable syntax** — callouts (`> [!note]`), Dataview queries, footnotes, and block
   references (`^abc123`) all need explicit handling or they'll render as raw ugly text in the PDF.

---

## 6. Roadmap

### Phase 0 — Setup
- [ ] Repo scaffold via `uv init`, `pyproject.toml` + `uv.lock`, pytest configured, a tiny fixture
      vault in `tests/fixtures/` (5–6 fake notes with real wikilinks between them, so you're never
      testing against your real, private vault)
- [ ] Confirm WeasyPrint's native dependencies (Pango, Cairo, GDK-Pixbuf) install cleanly on both
      target platforms — Homebrew on macOS, and `apt`/`dnf`/`pacman` on the Linux distro(s) you
      test against — before writing any rendering code. This is the one dependency in the whole
      stack that isn't pure-Python, and the one most likely to behave differently across OSes,
      worth derisking early on both.
- [ ] `models.py` — define `Note`, `Link`, `ExportConfig` dataclasses first. Get the data shapes
      right before writing logic against them.

### Phase 1 — MVP (flat export, ugly but correct)
- [ ] `vault_scanner`: walk a vault directory, parse frontmatter, build title → filepath index
- [ ] `link_graph`: regex-extract `[[wikilinks]]` per note, resolve against the title index
- [ ] `moc_walker`: DFS from root MOC, dedupe via `visited` set, output an ordered `list[Note]`
- [ ] `transform`: rewrite `[[Note]]` → `[Note](#note-slug)`, strip unsupported syntax (log what
      you strip — don't fail silently)
- [ ] `assembler` + `render`: concatenate to one Markdown doc → HTML via Jinja2 → PDF via
      WeasyPrint, no styling beyond "readable"
- [ ] **Success criterion**: pick a real MOC, export it, every internal link in the PDF actually
      jumps to the right section when clicked

### Phase 2 — Correctness & structure
- [ ] Nested MOC support (MOC linking to sub-MOCs → nested heading levels, not flat)
- [ ] Proper cycle detection (swap hand-rolled `visited` set for `networkx.DiGraph` if it's getting
      unwieldy)
- [ ] Image embed resolution (`![[image.png]]` → copy/reference correctly, respecting Obsidian's
      attachment folder settings)
- [ ] Auto-generated Table of Contents page + PDF bookmark hierarchy matching your heading structure
- [ ] Callout (`> [!note]`) → styled HTML block conversion

### Phase 3 — Polish & configurability
- [ ] Config file (`moc2pdf.toml` or similar) for vault path, output path, theme, excluded folders
- [ ] CSS theme(s) — at minimum a clean academic-looking default; maybe a print-optimised one
- [ ] Frontmatter metadata surfaced in output (tags, created date) — useful for a cover page
- [ ] Footnote support
- [ ] Proper logging (what was included, what was skipped, what syntax was stripped) so exports
      are debuggable

### Phase 4 — Stretch goals / future
- [ ] Math rendering (KaTeX at build time, since WeasyPrint can't run JS) for notes with LaTeX
- [ ] Batch mode: export every MOC in a folder in one run
- [ ] "Watch mode": re-export automatically on vault file changes (nice for iterating on a
      formatting theme while writing notes)
- [ ] Package as an actual Obsidian plugin (TypeScript) that shells out to / reimplements this,
      so export is a right-click action inside Obsidian itself
- [ ] Optional: a small graph visualisation page at the front of the PDF (which notes link where),
      generated from the same `link_graph` data

---

## 7. Testing Strategy

- Never test against your real vault — it's private, and it'll change under you. Build a small,
  representative fixture vault under `tests/fixtures/` and commit it to the repo.
- Unit test each stage in isolation against the fixture data: does `link_graph` extract the links
  you expect, does `moc_walker` produce the order you expect, does `transform` produce the anchor
  syntax you expect.
- One integration test per phase milestone: full pipeline, fixture vault in, assert the final PDF
  (or the final HTML before PDF rendering, which is easier to assert against) contains the right
  structure.
- This mirrors the pytest approach from `ln2xhtml` — same discipline, applied to a graph problem
  instead of a scraping problem.

---

## 8. Open Decisions (flag these before Phase 1 rather than during it)

- Include-once vs allow-duplicate for notes referenced from multiple places?
- How deep does MOC nesting go before you cap it (avoid accidentally exporting your entire vault
  from one root MOC)?
- Cover page / metadata page — yes or no for MVP?
- Do embedded images get copied into a build folder, or referenced by absolute path from your
  vault (simpler, but less portable if you ever move the repo)?
