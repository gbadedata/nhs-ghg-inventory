"""Download pinned sources and refuse anything whose bytes have changed."""
from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path

from . import config


class ChecksumError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(path: Path, spec: dict) -> None:
    size = path.stat().st_size
    if size != spec["bytes"]:
        raise ChecksumError(f"{path.name}: {size} bytes, expected {spec['bytes']}")
    digest = sha256_file(path)
    if digest != spec["sha256"]:
        raise ChecksumError(f"{path.name}: sha256 {digest}, expected {spec['sha256']}")


def fetch(name: str, force: bool = False) -> Path:
    spec = config.sources()["sources"][name]
    dest = config.raw_path(name)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not force:
        verify(dest, spec)
        return dest
    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(spec["url"], headers={"User-Agent": "nhs-ghg-inventory/0.1"})
    with urllib.request.urlopen(req, timeout=120) as resp, tmp.open("wb") as out:
        while chunk := resp.read(1 << 20):
            out.write(chunk)
    try:
        verify(tmp, spec)
    except ChecksumError:
        tmp.unlink(missing_ok=True)
        raise
    tmp.replace(dest)
    return dest


def fetch_all(force: bool = False) -> dict[str, Path]:
    return {name: fetch(name, force) for name in config.sources()["sources"]}
