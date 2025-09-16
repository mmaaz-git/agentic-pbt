import dataclasses
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
import trio

DATASET_URL = (
    "https://hugovk.github.io/top-pypi-packages/top-pypi-packages-30-days.min.json"
)
dataset_path = Path(__file__).parent / "pypi_packages.json"

# TODO: it would be nice to support non-github git providers as well. Shouldn't
# be too hard, just requires investigating the string format in the dataset


@dataclass
class Package:
    pypi_name: str
    github_url: str


def _normalize_github_url(raw_url: str) -> Optional[str]:
    # this function was written by claude, I'm not going to question it too much
    # since it seems fine
    if not raw_url:
        return None

    url = raw_url.strip()
    url = re.sub(r"^(git\+|git://)", "", url)
    ssh_match = re.match(r"^git@github\.com:(?P<owner>[^/]+?)/(?P<repo>[^/\s]+)$", url)
    if ssh_match:
        owner = ssh_match.group("owner")
        repo = ssh_match.group("repo")
        if repo.endswith(".git"):
            repo = repo[:-4]
        return f"https://github.com/{owner}/{repo}"
    if url.startswith("github.com/"):
        url = f"https://{url}"

    try:
        parsed = urlparse(url)
    except Exception:
        return None

    host = (parsed.hostname or "").lower()
    if not host.endswith("github.com"):
        return None
    path_parts = [p for p in parsed.path.split("/") if p]
    if len(path_parts) < 2:
        return None

    owner, repo = path_parts[0], path_parts[1]
    if repo.endswith(".git"):
        repo = repo[:-4]

    if not owner or not repo:
        return None

    return f"{parsed.scheme or 'https'}://github.com/{owner}/{repo}"


def _github_url(info: dict) -> Optional[str]:
    # this function was also (mostly) written by claude
    project_urls = info.get("project_urls") or {}
    preferred_keys = [
        "Source",
        "Source Code",
        "Code",
        "Homepage",
        "Home",
        "Repository",
        "GitHub",
    ]
    for key in preferred_keys:
        val = project_urls.get(key)
        if url := _normalize_github_url(val):
            return url
    for val in project_urls.values():
        if url := _normalize_github_url(val):
            return url

    home_page = info.get("home_page")
    if isinstance(home_page, str):
        if url := _normalize_github_url(home_page):
            return url

    return None


def _get_github_url(package: str) -> Optional[str]:
    api_url = f"https://pypi.org/pypi/{package}/json"
    data = None
    for _ in range(10):
        try:
            data = requests.get(api_url, timeout=10).json()
        except requests.RequestException:
            time.sleep(0.5)
        except ValueError:
            # invalid json
            time.sleep(0.5)

    if data is None:
        return None
    info = data.get("info") or {}
    return _github_url(info)


async def _top_urls(packages: list[str]) -> list[Package]:
    results: list[Package] = []
    # this is basically using trio as a nice api around threadpoolexecutor. we
    # could have just used the latter instead
    limiter = trio.CapacityLimiter(16)

    async def worker(package: str) -> None:
        url = await trio.to_thread.run_sync(
            _get_github_url,
            package,
            limiter=limiter,
        )
        if url:
            results.append(Package(pypi_name=package, github_url=url))

    async with trio.open_nursery() as nursery:
        for package in packages:
            nursery.start_soon(worker, package)

    return results


def top_urls(*, limit: Optional[int]) -> list[Package]:
    dataset = requests.get(DATASET_URL, timeout=20.0).json()
    packages = [row["project"] for row in dataset["rows"]]
    if limit is not None:
        packages = packages[:limit]
    return trio.run(_top_urls, packages)


def update_top_urls(limit: Optional[int] = None):
    url_data = top_urls(limit=limit)
    url_data = [dataclasses.asdict(package) for package in url_data]
    with open(dataset_path, "w+") as f:
        json.dump(url_data, f, indent=2)


def load_dataset(custom_path=None) -> list[Package]:
    path = custom_path if custom_path else dataset_path
    assert path.exists(), f"Dataset file not found: {path}"
    with open(path) as f:
        return [Package(**row) for row in json.load(f)]


# run this file to update the pypi_packages.json dataset
if __name__ == "__main__":
    update_top_urls(limit=None)
