from pathlib import Path

from moc2pdf.data.models import ExportConfig, Link, Note


def test_note_and_link_dataclasses_can_be_instantiated() -> None:
    source = Note(
        title="Algorithms",
        path=Path("vault/Algorithms.md"),
        content="# Algorithms\n\n[[Sorting]]",
    )

    link = Link(
        source_note="Algorithms",
        target_text="Sorting",
        target_title="Sorting",
        raw_link="[[Sorting]]",
    )

    source.links.append(link)

    assert source.title == "Algorithms"
    assert source.path == Path("vault/Algorithms.md")
    assert source.content.startswith("# Algorithms")
    assert source.links == [link]

    assert link.source_note == "Algorithms"
    assert link.target_text == "Sorting"
    assert link.target_title == "Sorting"
    assert link.raw_link == "[[Sorting]]"


def test_export_config_models_export_shape() -> None:
    cfg = ExportConfig(
        vault_path=Path("/tmp/vault"),
        root_moc="Algorithms MOC",
        output_path=Path("/tmp/output.pdf"),
        toc_enabled=True,
    )

    assert cfg.vault_path == Path("/tmp/vault")
    assert cfg.root_moc == "Algorithms MOC"
    assert cfg.output_path == Path("/tmp/output.pdf")
    assert cfg.toc_enabled is True
