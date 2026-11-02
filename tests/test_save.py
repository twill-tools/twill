"""Test saving pages and downloads with save_html and save_content."""

from io import StringIO
from pathlib import Path
from urllib.parse import quote

import pytest

from twill import commands
from twill.errors import TwillException

from .server import BINARY_CONTENT


@pytest.fixture
def work_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Use an empty subdirectory of a temporary directory as cwd."""
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    monkeypatch.chdir(work_dir)
    return work_dir


def go_download(url: str, name: str = "", disposition: str = "") -> None:
    """Go to the download page with the given name and disposition."""
    url = f"{url}download/{quote(name)}"
    if disposition:
        url += f"?disposition={quote(disposition)}"
    commands.go(url)
    commands.code(200)


def saved_files(path: Path) -> list[str]:
    """Get the sorted names of all files below the given path."""
    return sorted(
        str(p.relative_to(path)) for p in path.rglob("*") if p.is_file()
    )


def test_save_content_with_filename_from_header(url: str, work_dir: Path):
    go_download(url, "data.bin", 'attachment; filename="x.pdf"')
    commands.save_content()
    assert saved_files(work_dir) == ["x.pdf"]
    assert (work_dir / "x.pdf").read_bytes() == BINARY_CONTENT


def test_save_content_with_encoded_filename(url: str, work_dir: Path):
    go_download(
        url,
        "data.bin",
        'attachment; filename="fallback.pdf";'
        " filename*=UTF-8''%C3%84rger%20%E2%82%AC.pdf",
    )
    commands.save_content()
    assert saved_files(work_dir) == ["Ärger €.pdf"]
    assert (work_dir / "Ärger €.pdf").read_bytes() == BINARY_CONTENT


def test_save_content_with_malicious_filename(url: str, work_dir: Path):
    go_download(url, "data.bin", 'attachment; filename="../../evil.txt"')
    commands.save_content()
    assert saved_files(work_dir.parent) == ["work/evil.txt"]
    assert (work_dir / "evil.txt").read_bytes() == BINARY_CONTENT


def test_save_content_with_hidden_filename(url: str, work_dir: Path):
    go_download(url, "data.bin", 'attachment; filename="..\\\\.bashrc"')
    commands.save_content()
    assert saved_files(work_dir.parent) == ["work/data.bin"]
    assert (work_dir / "data.bin").read_bytes() == BINARY_CONTENT


def test_save_content_with_filename_from_url(url: str, work_dir: Path):
    go_download(url, "data.bin")
    commands.save_content()
    assert saved_files(work_dir) == ["data.bin"]
    assert (work_dir / "data.bin").read_bytes() == BINARY_CONTENT


def test_save_content_with_encoded_filename_from_url(url: str, work_dir: Path):
    go_download(url, "my data.bin")
    commands.save_content()
    assert saved_files(work_dir) == ["my data.bin"]
    assert (work_dir / "my data.bin").read_bytes() == BINARY_CONTENT


def test_save_content_with_default_filename(url: str, work_dir: Path):
    go_download(url)
    commands.save_content()
    assert saved_files(work_dir) == ["download.pdf"]
    assert (work_dir / "download.pdf").read_bytes() == BINARY_CONTENT


def test_save_content_with_explicit_filename(url: str, work_dir: Path):
    go_download(url, "data.bin", 'attachment; filename="x.pdf"')
    (work_dir / "sub").mkdir()
    commands.save_content("sub/y.pdf")
    assert saved_files(work_dir) == ["sub/y.pdf"]
    assert (work_dir / "sub" / "y.pdf").read_bytes() == BINARY_CONTENT


def test_save_content_logs_filename(
    url: str, work_dir: Path, output: StringIO
):
    go_download(url, "data.bin", 'attachment; filename="x.pdf"')
    commands.save_content()
    assert "Using filename 'x.pdf'." in output.getvalue()
    assert saved_files(work_dir) == ["x.pdf"]


def test_save_html_with_filename_from_url(url: str, work_dir: Path):
    commands.go(f"{url}test spaces?foo=bar")
    commands.save_html()
    assert saved_files(work_dir) == ["test spaces"]
    assert (work_dir / "test spaces").read_text() == commands.browser.html


def test_save_html_with_default_filename(url: str, work_dir: Path):
    commands.go(url)
    commands.save_html()
    assert saved_files(work_dir) == ["index.html"]
    assert (work_dir / "index.html").read_text() == commands.browser.html


def test_save_without_page(work_dir: Path):
    commands.reset_browser()
    with pytest.raises(TwillException, match="no page"):
        commands.save_content()
    with pytest.raises(TwillException, match="no page"):
        commands.save_html()
    assert not saved_files(work_dir)
