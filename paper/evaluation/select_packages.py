#!/usr/bin/env python3
"""
Generate packages.json with stdlib + popular + random PyPI packages.
Each package includes discovered testable modules.
"""

import importlib
import argparse
import json
import random
import statistics
import subprocess
import tempfile
import venv
from pathlib import Path
from typing import Dict, List

# 15 hand-selected standard library packages
STDLIB_PACKAGES = [
    "json",
    "pathlib",
    "collections",
    "itertools",
    "functools",
    "datetime",
    "re",
    "os",
    "urllib",
    "dataclasses",
    "decimal",
    "base64",
    "statistics",
    "uuid",
    "html",
]

# 15 hand-selected popular PyPI packages
POPULAR_PACKAGES = [
    "numpy",
    "pandas",
    "requests",
    "flask",
    "django",
    "python-dateutil",
    "cryptography",
    "lxml",
    "sqlalchemy",
    "beautifulsoup4",
    "pydantic",
    "click",
    "tqdm",
    "packaging",
    "scipy",
]

RANDOM_COUNT = 70
TOP_N_FOR_RANDOM = 5000
SEED = 42

# Module discovery settings
MAX_MODULE_DEPTH = 2  # package.submodule (adjust as needed)
SKIP_NAMES = {
    "version",
    "compat",
    "warnings",
    "exceptions",
    "errors",
    "config",
    "testing",
    "tests",
    "test",
    "deprecated",
    "legacy",
}


def should_skip_module(module_name: str) -> bool:
    parts = module_name.split(".")
    if any(part.startswith("_") for part in parts):
        return True
    if any(part in {"internals", "libs", "util", "compat"} for part in parts):
        return True
    if len(parts) > MAX_MODULE_DEPTH:
        return True
    return False


def bfs_discover_from_seeds(seeds: List[str]) -> List[str]:
    """Import seed modules and breadth-first discover submodules up to depth."""
    discovered: set[str] = set()
    to_explore: list[str] = list(dict.fromkeys(seeds))

    while to_explore:
        module_name = to_explore.pop(0)
        if module_name in discovered or should_skip_module(module_name):
            continue
        try:
            module = importlib.import_module(module_name)
            discovered.add(module_name)

            # Look for submodules using pkgutil
            if hasattr(module, "__path__"):
                try:
                    import pkgutil

                    for _, modname, _ in pkgutil.iter_modules(module.__path__):
                        full_name = f"{module_name}.{modname}"
                        if (
                            not modname.startswith("_")
                            and modname.lower() not in SKIP_NAMES
                            and full_name not in discovered
                        ):
                            to_explore.append(full_name)
                except Exception:
                    pass

            # Also check direct module attributes (e.g. urllib.parse)
            import inspect as _inspect

            for name, obj in _inspect.getmembers(module):
                if (
                    not name.startswith("_")
                    and _inspect.ismodule(obj)
                    and hasattr(obj, "__name__")
                    and obj.__name__.startswith(module_name + ".")
                    and name.lower() not in SKIP_NAMES
                ):
                    if obj.__name__ not in discovered:
                        to_explore.append(obj.__name__)
        except Exception:
            pass

    return sorted(discovered)


def find_import_name(package_name: str) -> List[str]:
    """Find the actual import name(s) for a PyPI package using metadata."""
    try:
        import importlib.metadata as md

        dist = md.distribution(package_name)

        top_level_names = set()

        # 1) Use top_level.txt if available
        try:
            tl = dist.read_text("top_level.txt")
            if tl:
                for line in tl.splitlines():
                    name = line.strip()
                    if name:
                        top_level_names.add(name)
        except Exception:
            pass

        # 2) Infer from installed files
        skip_first_parts = {
            "__pycache__",
            "EGG-INFO",
            "bin",
            "include",
            "lib",
            "Scripts",
            ".data",
            ".libs",
            "data",
            "platlib",
            "purelib",
        }
        if dist.files:
            import re

            for file_path in dist.files:
                parts = str(file_path).split("/")
                if not parts:
                    continue
                first = parts[0]
                if first.endswith(".dist-info") or first in skip_first_parts:
                    continue
                m = re.match(r"^[A-Za-z_][A-Za-z0-9_]*", first)
                if not m:
                    continue
                name = m.group(0)
                if name and not name.startswith("_"):
                    top_level_names.add(name)

        # Try each discovered top-level name
        import_candidates = (
            sorted(top_level_names)
            if top_level_names
            else [
                package_name,
                package_name.replace("-", "_"),
                package_name.replace("-", ""),
                package_name.split("-")[0],
            ]
        )

    except Exception:
        import_candidates = [
            package_name,
            package_name.replace("-", "_"),
            package_name.replace("-", ""),
            package_name.split("-")[0],
        ]

    # Find working import names
    working_names = []
    for candidate in import_candidates:
        try:
            importlib.import_module(candidate)
            working_names.append(candidate)
        except ImportError:
            continue

    return working_names if working_names else [package_name]


def discover_modules(package_name: str, package_type: str) -> List[str]:
    """Unified discovery for both stdlib and pypi packages."""
    with tempfile.TemporaryDirectory() as temp_dir:
        venv_path = Path(temp_dir) / "test_venv"

        try:
            # Create temporary venv
            venv.create(venv_path, with_pip=True)
            python_path = venv_path / "bin" / "python"

            if package_type == "pypi":
                # Install the package
                pip_path = venv_path / "bin" / "pip"
                result = subprocess.run(
                    [str(pip_path), "install", package_name],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )

                if result.returncode != 0:
                    print(f"  Warning: Failed to install {package_name}")
                    return None  # Signal installation failure

            # Use the same discovery logic for both!
            discovery_script = Path(__file__).parent / "generate_packages.py"
            discovery_code = f"""
import sys
sys.path.insert(0, "{discovery_script.parent}")
from generate_packages import find_import_name, bfs_discover_from_seeds

package_name = "{package_name}"
package_type = "{package_type}"

if package_type == "stdlib":
    import_names = [package_name]
else:
    import_names = find_import_name(package_name)

if import_names:
    modules = bfs_discover_from_seeds(import_names)
    print("|||".join(modules))
else:
    print(package_name)
"""

            result = subprocess.run(
                [str(python_path), "-c", discovery_code],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0 and result.stdout.strip():
                modules = [m for m in result.stdout.strip().split("|||") if m]
                if not modules:
                    print(f"  Warning: No valid modules found for {package_name}")
                    return None if package_type == "pypi" else [package_name]
                return modules
            else:
                print(f"  Warning: Module discovery failed for {package_name}")
                return None if package_type == "pypi" else [package_name]

        except Exception as e:
            print(f"  Warning: Failed to discover modules for {package_name}: {e}")
            return None if package_type == "pypi" else [package_name]


def find_package_by_name(packages: List[Dict], name: str) -> Dict:
    """Find a package by pypi_name."""
    for pkg in packages:
        if pkg["pypi_name"] == name:
            return pkg
    return None


def generate_packages_dict(top_pypi_packages_path: Path) -> Dict:
    """Generate the complete packages dictionary."""
    packages_dict = {}

    print("🔧 Generating packages dictionary...\n")

    # 1. Add stdlib packages
    print("📦 Processing standard library packages:")
    for pkg_name in STDLIB_PACKAGES:
        print(f"  Discovering modules for {pkg_name}...")
        modules = discover_modules(pkg_name, "stdlib")
        packages_dict[pkg_name] = {"type": "stdlib", "modules": modules}
        print(f"    Found {len(modules)} modules: {modules}")

    # 2. Add popular PyPI packages
    print(f"\n📦 Processing {len(POPULAR_PACKAGES)} popular PyPI packages:")
    for pkg_name in POPULAR_PACKAGES:
        print(f"  Discovering modules for {pkg_name}...")
        modules = discover_modules(pkg_name, "pypi")
        packages_dict[pkg_name] = {"type": "pypi", "modules": modules}
        print(f"    Found {len(modules)} modules: {modules}")

    # 3. Add random PyPI packages
    print(
        f"\n📦 Processing {RANDOM_COUNT} random PyPI packages from top {TOP_N_FOR_RANDOM}:"
    )

    with open(top_pypi_packages_path) as f:
        pypi_packages = json.load(f)

    if not pypi_packages:
        print(f"  Warning: No PyPI packages loaded, skipping random selection")
        return packages_dict

    # Exclude already selected packages
    excluded_names = set(POPULAR_PACKAGES + STDLIB_PACKAGES)
    candidates = [
        pkg
        for pkg in pypi_packages[:TOP_N_FOR_RANDOM]
        if pkg["pypi_name"] not in excluded_names
    ]

    random.seed(SEED)
    selected_packages = []
    available_candidates = candidates.copy()

    # Keep drawing until we have enough successful packages
    attempts = 0
    max_attempts = RANDOM_COUNT * 3  # Allow 3x attempts to account for failures

    while (
        len(selected_packages) < RANDOM_COUNT
        and available_candidates
        and attempts < max_attempts
    ):
        attempts += 1

        # Pick a random package
        pkg = random.choice(available_candidates)
        available_candidates.remove(pkg)
        pkg_name = pkg["pypi_name"]

        print(
            f"  [{len(selected_packages)+1:2d}/{RANDOM_COUNT}] Discovering modules for {pkg_name}..."
        )
        modules = discover_modules(pkg_name, "pypi")

        # Check if installation/discovery succeeded
        if modules is not None:
            # Success - pip install worked (even if only 1 module)
            selected_packages.append((pkg_name, modules))
            print(
                f"    ✅ Found {len(modules)} modules: {modules[:3]}{'...' if len(modules) > 3 else ''}"
            )
        else:
            # Failed - pip install or discovery failed, redraw
            print(f"    ❌ Installation failed, redrawing...")
            continue

    # Add successful packages to the dictionary
    for pkg_name, modules in selected_packages:
        packages_dict[pkg_name] = {"type": "pypi", "modules": modules}

    return packages_dict


def main():
    """Generate packages.json file."""
    parser = argparse.ArgumentParser(
        description="Generate packages.json with stdlib + popular + random PyPI packages."
    )
    parser.add_argument(
        "in_json",
        help="Path to input JSON listing top PyPI packages (expects objects with 'pypi_name').",
    )
    parser.add_argument(
        "out_json",
        nargs="?",
        default=str(Path(__file__).parent / "packages.json"),
        help="Output JSON path (default: packages.json)",
    )
    args = parser.parse_args()

    top_pypi_packages_path = Path(args.in_json)
    output_file = Path(args.out_json)

    packages_dict = generate_packages_dict(top_pypi_packages_path)

    # Statistics
    total_packages = len(packages_dict)
    total_modules = sum(len(info["modules"]) for info in packages_dict.values())
    stdlib_count = sum(1 for info in packages_dict.values() if info["type"] == "stdlib")
    pypi_count = sum(1 for info in packages_dict.values() if info["type"] == "pypi")

    print(f"\n📊 Summary:")
    print(f"   Total packages: {total_packages}")
    print(f"   Standard library: {stdlib_count}")
    print(f"   PyPI packages: {pypi_count}")
    print(f"   Total modules to test: {total_modules}")
    print(
        f"   Median modules per package: {statistics.median(len(info['modules']) for info in packages_dict.values()):.1f}"
    )

    # Save to specified output path
    with open(output_file, "w") as f:
        json.dump(packages_dict, f, indent=2)

    print(f"\n✅ Saved to {output_file}")


if __name__ == "__main__":
    main()
