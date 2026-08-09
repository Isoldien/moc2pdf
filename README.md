# moc2pdf — Obsidian MOC → PDF Exporter

Turn a Zettelkasten Map of Content (MOC) and everything it links to into a single, properly
formatted PDF with **working internal hyperlinks** — for submitting to systems that don't support
Markdown or Obsidian, but do accept PDFs.

> Status: 🚧 Planning stage. See [`PLAN.md`](./PLAN.md) for the full architecture and roadmap, and
> [`AGENTS.md`](./AGENTS.md) if you're an AI coding assistant working in this repo.

---

## The Problem

Obsidian's Zettelkasten workflow (atomic notes + `[[wikilinks]]` + MOCs) is great for actually
thinking and studying, but it's useless the moment you need to hand work to a system that only
understands plain files. Copy-pasting flattens your links; exporting to plain Markdown breaks
them entirely.

PDFs, on the other hand, support internal hyperlinks and bookmarks — so the goal here is to
preserve the *structure* of a Zettelkasten (not just the text) when converting to PDF.

## What It Does

Given a starting MOC note in your vault, `moc2pdf`:

1. Walks the link graph outward from that MOC, following `[[wikilinks]]` to every note it
   (transitively) references
2. Assembles those notes into one linear document, ordered to reflect the MOC's structure
3. Rewrites every `[[wikilink]]` as an internal PDF link/bookmark instead of a dead reference
4. Renders the result to a single navigable PDF, with a generated table of contents

## Why Python

Straightforward text/graph processing, a mature Markdown/HTML ecosystem, and — via
[WeasyPrint](https://weasyprint.org/) — genuine support for CSS-driven PDF bookmarks and internal
links, without needing a heavier toolchain like LaTeX.

## Planned Usage

```bash
# Export a single MOC by note title
uv run moc2pdf export "Algorithms MOC" --vault ~/ObsidianVault --output algorithms.pdf

# Export every MOC found in a folder
uv run moc2pdf export-all --vault ~/ObsidianVault --moc-folder "MOCs/" --output-dir ./exports/
```

*(CLI shape is a working draft — see `PLAN.md` §6 for what's actually implemented at each phase.)*

## Requirements

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** — used for dependency management, the virtual environment,
  and running the tool (`uv sync`, `uv run`)
- **macOS or Linux**, with a Unix shell. Any mainstream Linux distro works — Ubuntu/Debian, Fedora,
  and Arch are all covered explicitly below. **Windows is supported via WSL2** (which is itself a
  real Linux environment, so the Linux instructions apply directly once you're inside it) —
  native Windows Python is not supported, since WeasyPrint's underlying rendering libraries
  (Pango, Cairo, GDK-Pixbuf) are unreliable to install and link there. See `PLAN.md` §6, Phase 4
  for the long-term native-Windows question.
- See `pyproject.toml` for the full dependency list once scaffolded (key ones: `python-frontmatter`,
  `markdown-it-py`, `Jinja2`, `WeasyPrint`, `typer`)

## Development Setup

This project is managed entirely with [`uv`](https://docs.astral.sh/uv/) — no manual `venv`
activation, no bare `pip install`.

1. **Install uv** (skip if already installed):

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone and enter the repo:**

   ```bash
   git clone <repo-url>
   cd moc2pdf
   ```

3. **Sync the environment.** This reads `pyproject.toml`/`uv.lock`, provisions the pinned Python
   version if you don't already have it, and builds `.venv/`:

   ```bash
   uv sync
   ```

4. **WeasyPrint's native dependencies** (Pango, Cairo, GDK-Pixbuf) aren't pure-Python and need to
   be installed via your system package manager, not `uv`. Pick the line for your OS:

   ```bash
   # macOS (Homebrew)
   brew install pango cairo gdk-pixbuf libffi

   # Ubuntu / Debian / WSL2 (Ubuntu)
   sudo apt update && sudo apt install libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libgdk-pixbuf2.0-0 libffi-dev

   # Fedora
   sudo dnf install pango cairo gdk-pixbuf2 libffi-devel

   # Arch
   sudo pacman -S pango cairo gdk-pixbuf2 libffi
   ```

   Sanity-check the install actually renders before relying on it:

   ```bash
   uv run python -c "from weasyprint import HTML; HTML(string='<h1>ok</h1>').write_pdf('test.pdf')"
   rm test.pdf
   ```

   **If that command fails with something like
   `OSError: cannot load library 'libgobject-2.0-0'`**, see
   [Troubleshooting: WeasyPrint can't find its native libraries](#troubleshooting-weasyprint-cant-find-its-native-libraries)
   below before continuing — this is a common (and fixable) linking issue, not a broken install.

5. **Run the test suite** to confirm everything's wired up:

   ```bash
   uv run pytest
   ```

6. **Everyday commands**, always via `uv run` so they execute inside the locked environment:

   ```bash
   uv run moc2pdf --help    # run the CLI
   uv run pytest -v         # run tests
   uv run ruff check .      # lint
   uv run black .           # format
   uv add <package>         # add a new runtime dependency
   uv add --dev <package>   # add a new dev-only dependency (test/lint tooling)
   ```

See [Requirements](#requirements) above for OS coverage — macOS, Linux, and Windows via WSL2 are
all first-class here, since Obsidian and Markdown themselves are cross-platform and this tool
should be too.

### Troubleshooting: WeasyPrint can't find its native libraries

This shows up differently depending on OS, but the root cause is always the same: the native
libraries (Pango, Cairo, GDK-Pixbuf) are installed, but the dynamic linker doesn't know where to
look for them.

**On macOS (Apple Silicon):** Homebrew installs to `/opt/homebrew` instead of `/usr/local`, which
isn't on macOS's default library search path. You'll see an `OSError` from `cffi`/`dlopen` saying
it can't find `libgobject-2.0-0` (or `libpango`, `libcairo`, etc.) even though `brew` reports it's
installed.

First, confirm the libraries are actually there:

```bash
ls "$(brew --prefix)/lib" | grep gobject
```

If nothing shows up, the Homebrew install itself failed — re-run
`brew reinstall pango cairo gdk-pixbuf libffi` and check for errors. If the `.dylib` **is** there,
scope the fix to this project only via [`direnv`](https://direnv.net/), rather than editing your
shell profile:

```bash
brew install direnv
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc && source ~/.zshrc   # one-time, enables direnv itself

# from inside the moc2pdf repo:
echo 'export DYLD_LIBRARY_PATH="$(brew --prefix)/lib:$DYLD_LIBRARY_PATH"' > .envrc
direnv allow
```

**On Linux (including WSL2):** this is much rarer — `apt`/`dnf`/`pacman` install shared libraries
into the system's standard linker paths (`/usr/lib`, `/usr/lib/x86_64-linux-gnu`, etc.), which are
already searched by default. If you do hit a similar `OSError` on Linux, it usually means the
package didn't actually install (re-run the install command for your distro above and check for
errors) or you're in a minimal/container environment missing `ldconfig` metadata — running
`sudo ldconfig` to refresh the linker cache after installing resolves it in that case.

In either case, re-run the smoke test from step 4 above once fixed — it should pass.

`.envrc` (macOS/direnv route) is machine-specific, so it's listed in `.gitignore` rather than
committed — each contributor generates their own with the command above.



## Project Structure

```
moc2pdf/
├── moc2pdf/          # package source
├── templates/       # Jinja2 + CSS for PDF rendering
├── tests/           # pytest suite + fixture vault
├── PLAN.md          # architecture, requirements, roadmap
├── AGENTS.md         # instructions for AI coding assistants working in this repo
└── README.md
```

## Roadmap

See [`PLAN.md`](./PLAN.md) for full detail. Short version:

- [x] **Phase 0** — repo scaffold, fixture vault, data models
- [ ] **Phase 1** — MVP: flat single-MOC export with working internal links
- [ ] **Phase 2** — nested MOCs, image embeds, generated TOC, callout styling
- [ ] **Phase 3** — config file, themes, frontmatter metadata, footnotes
- [ ] **Phase 4 (stretch)** — math rendering, batch export, watch mode, Obsidian plugin

## Contributing

This is currently a personal/university-support project, built primarily for one person's own
Zettelkasten workflow — so contribution bandwidth is limited and there's no formal process for
reviewing external PRs right now. That said, the [dev setup](#development-setup) above works for
anyone who wants to run or poke at the code. If you're working from this repo, open an issue or
PR describing the vault feature you're trying to support — Obsidian's Markdown flavour has a lot
of edge cases and it's easier to fix them one at a time with a concrete example.

## License

Licensed under the [GNU General Public License v3.0](./LICENSE) — chosen deliberately so that this
project, and anything forked or built on top of it, stays open source.

## Acknowledgements

Built around the [Zettelkasten](https://zettelkasten.de/) method and [Obsidian](https://obsidian.md/)'s
linking model.
