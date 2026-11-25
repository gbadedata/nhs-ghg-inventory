"""The download guard: a file is accepted only if size and SHA-256 both match."""
import hashlib

import pytest

from nhs_ghg import config, fetch


def _spec(data: bytes) -> dict:
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def test_matching_file_passes(tmp_path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"official bytes")
    fetch.verify(p, _spec(b"official bytes"))


def test_changed_content_same_size_fails(tmp_path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"official bytez")
    with pytest.raises(fetch.ChecksumError, match="sha256"):
        fetch.verify(p, _spec(b"official bytes"))


def test_truncated_file_fails(tmp_path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"official")
    with pytest.raises(fetch.ChecksumError, match="bytes"):
        fetch.verify(p, _spec(b"official bytes"))


def test_every_source_is_fully_pinned():
    for name, spec in config.sources()["sources"].items():
        assert spec["url"].startswith("https://"), name
        assert len(spec["sha256"]) == 64 and int(spec["sha256"], 16) >= 0, name
        assert spec["bytes"] > 0, name
