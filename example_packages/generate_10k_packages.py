#!/usr/bin/env python3
"""
Make list of modules for 10k packages:
- Reads top-pypi-packages.min.json (or provided file) -- top 15k pypi packages
- Fetches GitHub repository URLs from PyPI project metadata to dedupe by repo
- For the first N deduped packages, downloads wheels
- Extracts top-level import names from top_level.txt and wheel contents

Outputs mapping: { pypi_name: { type: "pypi", modules: [top, top.sub1, ...] } }

Optional: write a GitHub mapping JSON after URLs are fetched using --out-gh.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from tqdm import tqdm

PATH_TO_TOP_PYPI_PACKAGES = Path("top-pypi-packages.min.json")


def run(cmd: list[str], timeout: int | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)


def load_top_packages(path: Path) -> list[dict]:
    """Load package list from either legacy paper JSON or min ClickHouse JSON.

    Returns list of dicts shaped like {"pypi_name": str, "github_url": Optional[str]}
    (github_url may be empty and filled later).
    """
    raw = json.loads(path.read_text())
    # Legacy format: list of {"pypi_name": ..., "github_url": ...}
    if isinstance(raw, list):
        out: list[dict] = []
        for obj in raw:
            if not isinstance(obj, dict):
                continue
            name = obj.get("pypi_name") or obj.get("project") or obj.get("name")
            if not name:
                continue
            out.append({"pypi_name": str(name), "github_url": obj.get("github_url")})
        return out

    # Min format: object with rows: [{"project": str, ...}]
    if isinstance(raw, dict) and isinstance(raw.get("rows"), list):
        out: list[dict] = []
        for row in raw["rows"]:
            if not isinstance(row, dict):
                continue
            name = row.get("project")
            if name:
                out.append({"pypi_name": str(name), "github_url": None})
        return out

    raise ValueError("Unrecognized input JSON format for top packages")


def dedupe_by_github(packages: list[dict]) -> list[str]:
    """Deduplicate by normalized GitHub repo when available, otherwise by name."""
    seen: set[str] = set()
    out: list[str] = []
    for obj in packages:
        name = obj.get("pypi_name")
        url = obj.get("github_url")
        if not name:
            continue
        key = (url or "").strip().lower() or f"no-gh:{name.lower()}"
        if key in seen:
            continue
        seen.add(key)
        out.append(name)
    return out


_GITHUB_RE = re.compile(r"https?://(?:www\.)?github\.com/([^/]+)/([^/#?]+)", re.I)
_PRIORITY_URL_KEYS = ["Repository", "Source", "Code", "Homepage", "Home", "Home-page", "Changelog"]


def _normalize_github(url: str | None) -> str | None:
    if not url:
        return None
    m = _GITHUB_RE.search(url)
    if not m:
        return None
    owner, repo = m.group(1), m.group(2)
    repo = re.sub(r"\.git/?$", "", repo, flags=re.I).strip("/")
    return f"https://github.com/{owner.lower()}/{repo.lower()}"


def _curl_pypi_json(name: str) -> dict | None:
    url = f"https://pypi.org/pypi/{name}/json"
    try:
        pr = run(["curl", "-sSL", "--max-time", "15", url])
        if pr.returncode != 0:
            return None
        return json.loads(pr.stdout or "{}")
    except Exception:
        return None


def _extract_project_urls(info: dict) -> list[str]:
    urls: list[str] = []
    proj = (info or {}).get("project_urls") or {}
    if isinstance(proj, dict):
        for k in _PRIORITY_URL_KEYS:
            v = proj.get(k)
            if isinstance(v, str):
                urls.append(v)
        for v in proj.values():
            if isinstance(v, str) and v not in urls:
                urls.append(v)
    for k in ("home_page", "download_url"):
        v = (info or {}).get(k)
        if isinstance(v, str):
            urls.append(v)
    return urls


def populate_github_urls(packages: list[dict], workers: int = 32) -> list[dict]:
    """Populate github_url for packages missing it via PyPI JSON metadata."""
    def task(obj: dict) -> dict:
        if obj.get("github_url"):
            return obj
        name = obj.get("pypi_name")
        if not name:
            return obj
        meta = _curl_pypi_json(name)
        if not meta or not isinstance(meta, dict):
            return obj
        info = meta.get("info") or {}
        gh: str | None = None
        for u in _extract_project_urls(info):
            gh = _normalize_github(u)
            if gh:
                break
        if gh:
            obj = dict(obj)
            obj["github_url"] = gh
        return obj

    out: list[dict] = []
    with ThreadPoolExecutor(max_workers=max(1, int(workers))) as ex:
        futures = [ex.submit(task, obj) for obj in packages]
        for fut in tqdm(as_completed(futures), total=len(futures), desc="Fetching GitHub", unit="pkg"):
            try:
                out.append(fut.result())
            except Exception:
                out.append(obj)
    return out


SKIP_NAMES = {
    "test", "tests", "testing",
    "example", "examples",
    "doc", "docs",
    "script", "scripts",
    "tool", "tools",
    "benchmark", "benchmarks",
    "sample", "samples",
}


def is_public_name(name: str) -> bool:
    if not name or name.startswith('_'):
        return False
    if name in SKIP_NAMES:
        return False
    return bool(re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', name))


def read_top_levels_from_wheel(wheel_path: Path) -> list[str]:
    top_levels: list[str] = []
    with zipfile.ZipFile(wheel_path) as zf:
        names = zf.namelist()
        # From *.dist-info/top_level.txt
        distinfo_top = [n for n in names if n.endswith('.dist-info/top_level.txt')]
        if distinfo_top:
            data = zf.read(distinfo_top[0]).decode('utf-8', errors='ignore')
            for ln in data.splitlines():
                ln = ln.strip()
                if is_public_name(ln):
                    top_levels.append(ln)

        # From *.dist-info/namespace_packages.txt (explicit namespace packages)
        distinfo_ns = [n for n in names if n.endswith('.dist-info/namespace_packages.txt')]
        if distinfo_ns:
            try:
                ns_data = zf.read(distinfo_ns[0]).decode('utf-8', errors='ignore')
                for ln in ns_data.splitlines():
                    ns = ln.strip()
                    if not ns:
                        continue
                    root = ns.split('.')[0]
                    if is_public_name(root):
                        top_levels.append(root)
            except Exception:
                pass

        # Classic packages: top-level dirs that have __init__.py
        root_entries = set(p.split('/')[0] for p in names if '/' in p)
        for root in sorted(root_entries):
            if not is_public_name(root):
                continue
            if f"{root}/__init__.py" in names:
                top_levels.append(root)

        # Implicit namespace roots: paths like X/Y/__init__.py but missing X/__init__.py
        for path in names:
            if path.count('/') >= 2 and path.endswith('/__init__.py'):
                root = path.split('/')[0]
                if is_public_name(root) and f"{root}/__init__.py" not in names:
                    top_levels.append(root)

        # Single-file modules at wheel root (e.g., typing_extensions.py)
        for name in names:
            if '/' in name or not name.endswith('.py'):
                continue
            stem = name[:-3]
            if stem == "__init__":
                continue
            if is_public_name(stem):
                top_levels.append(stem)
    # Deduplicate
    seen, uniq = set(), []
    for t in top_levels:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq


def list_first_level_subpackages_from_wheel(wheel_path: Path, top: str) -> list[str]:
    subs: set[str] = set()
    with zipfile.ZipFile(wheel_path) as zf:
        prefix = f"{top}/"
        prefix_len = len(prefix)
        # Collect immediate child dirs
        child_dirs = set()
        for name in zf.namelist():
            if not name.startswith(prefix):
                continue
            rest = name[prefix_len:]
            if '/' in rest:
                child = rest.split('/')[0]
                if is_public_name(child):
                    child_dirs.add(child)
        for child in sorted(child_dirs):
            if f"{top}/{child}/__init__.py" in zf.namelist():
                subs.add(f"{top}.{child}")
    return sorted(subs)


def process_one(pkg: str, download_dir: Path, pip: str = "python3") -> dict:
    tmp_dir = download_dir / pkg.replace('/', '_')
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # Download wheel only, no deps
    cmd = [pip, "-m", "pip", "download", "--only-binary", ":all:", "--no-deps", "-d", str(tmp_dir), pkg]
    pr = run(cmd, timeout=300)
    if pr.returncode != 0:
        return {"type": "pypi", "modules": [], "error": pr.stderr.strip()[:4000]}

    wheels = list(tmp_dir.glob("*.whl"))
    if not wheels:
        # No wheel found; skip (sdist would be slower to analyze reliably)
        return {"type": "pypi", "modules": []}

    wheel_path = wheels[0]
    tops = read_top_levels_from_wheel(wheel_path)
    mods: list[str] = []
    for top in tops:
        mods.append(top)
        mods.extend(list_first_level_subpackages_from_wheel(wheel_path, top))

    # Dedup preserve order
    seen, uniq = set(), []
    for m in mods:
        if m not in seen:
            seen.add(m)
            uniq.append(m)

    # Cap number of modules per package
    # note that 99%ile is 21 (over top 15k pypi packages)
    # so this is a reasonable cap
    if len(uniq) > 20:
        uniq = uniq[:20]

    # Cleanup wheel files to save disk
    shutil.rmtree(tmp_dir, ignore_errors=True)
    return {"type": "pypi", "modules": uniq}


def main():
    parser = argparse.ArgumentParser(description="Scan wheels to list modules without installing.")
    parser.add_argument("--out", default=str(Path("packages.json")), help="Output JSON path")
    parser.add_argument("--out-gh", default=str(Path("github_map.json")), help="Optional path to write {pypi_name: github_url} mapping")
    parser.add_argument("--count", type=int, default=None, help="How many packages to process from the original list")
    parser.add_argument("--finalcount", type=int, default=10000, help="Max final number of packages to output")
    parser.add_argument("--workers", type=int, default=100, help="Concurrent scans")
    args = parser.parse_args()

    raw_pkgs = load_top_packages(PATH_TO_TOP_PYPI_PACKAGES)
    pkgs = raw_pkgs[: min(args.count or len(raw_pkgs), len(raw_pkgs))]
    pkgs = populate_github_urls(pkgs, workers=args.workers)

    # Optionally write GitHub mapping before heavy work
    if args.out_gh:
        gh_map = {obj["pypi_name"]: obj.get("github_url") for obj in pkgs if obj.get("pypi_name")}
        Path(args.out_gh).write_text(json.dumps(gh_map, indent=2))
        print(f"Wrote GitHub map to {args.out_gh}")
    names = dedupe_by_github(pkgs)

    results: dict[str, dict] = {}
    download_root = Path(tempfile.mkdtemp(prefix="wheel-scan-"))
    try:
        with ThreadPoolExecutor(max_workers=max(1, int(args.workers))) as ex:
            futures = {ex.submit(process_one, name, download_root): name for name in names}
            for fut in tqdm(as_completed(futures), total=len(futures), desc="Scanning", unit="pkg"):
                name = futures[fut]
                try:
                    results[name] = fut.result()
                except Exception as e:
                    results[name] = {"type": "pypi", "modules": [], "error": str(e)}

        # Filter out entries with empty or missing modules, preserve original order
        ordered_names = [n for n in names if n in results]
        filtered_names = [n for n in ordered_names if results.get(n, {}).get("modules")]
        limited_names = filtered_names[: max(0, int(args.finalcount))]

        output = {n: results[n] for n in limited_names}

        Path(args.out).write_text(json.dumps(output, indent=2))
        print(f"Wrote {args.out}")
    finally:
        shutil.rmtree(download_root, ignore_errors=True)


if __name__ == "__main__":
    main()


