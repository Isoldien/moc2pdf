from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Link:
    """A single Obsidian wikilink or embed edge discovered in a note.

    The Phase 1 pipeline expects this structure to be carried from vault scan to
    link-graph resolution and then to the transform/assembler stages.
    """
    source_note: str
    target_text: str
    target_title: str | None = None
    target_path: Path | None = None
    raw_link: str = ""
    is_embed: bool = False
    is_broken: bool = False


@dataclass
class Note:
    """One Obsidian Markdown note that is indexed by the vault scanner.

    The `links` field is intentionally mutable so the graph resolver can append
    or annotate outgoing references after the raw note text has already been read.
    """

    title: str
    path: Path
    content: str
    frontmatter: dict[str, Any] = field(default_factory=dict)
    links: list[Link] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    slug: str = ""
    is_moc: bool = False


@dataclass
class ExportConfig:
    """Configuration values for a single export run.

    These values are deliberately small and explicit so the CLI and render stages
    can accept one object instead of a large positional argument list.
    """

    vault_path: Path
    root_moc: str
    output_path: Path
    include_frontmatter: bool = False
    toc_enabled: bool = True
    max_depth: int | None = None
    theme_name: str | None = None
