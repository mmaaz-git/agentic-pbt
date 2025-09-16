#!/usr/bin/env python3
"""
Agent runner
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from tqdm import tqdm

# Configuration
RESULTS_DIR = Path(__file__).parent / "results"
ENVS_DIR = Path(__file__).parent / "envs"
WORKER_DIR_PREFIX = Path(__file__).parent / "worker_"
HYPO_COMMAND = Path(__file__).parent / "hypo.md"
MAX_WORKERS = 20

RESULTS_DIR.mkdir(exist_ok=True)
ENVS_DIR.mkdir(exist_ok=True)

# Progress tracking
progress_lock = threading.Lock()
completed_count = 0
total_count = 0


def load_packages(packages_file: Path) -> dict[str, dict]:
    """Load packages from the specified packages file."""
    if not packages_file.exists():
        print(f"Error: Packages file {packages_file} does not exist")
        sys.exit(1)

    try:
        with open(packages_file) as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {packages_file}: {e}")
        sys.exit(1)


def setup_stdlib_venv() -> Path:
    """Set up a shared virtual environment for stdlib packages."""
    venv_path = ENVS_DIR / "stdlib_env"
    print("Setting up stdlib venv...")

    # Create venv if it doesn't exist
    if not venv_path.exists():
        subprocess.run(["python3", "-m", "venv", str(venv_path)], check=True)
        pip_path = venv_path / "bin" / "pip"
        # Install only testing dependencies (stdlib packages are built-in)
        subprocess.run([str(pip_path), "install", "hypothesis", "pytest"], check=True)
        print("✅ stdlib_env created with hypothesis and pytest")
    else:
        print("✅ stdlib_env already exists")

    return venv_path


def _pip_install_with_fallback(pip_path: Path, packages_to_install: list[str]) -> None:
    """Install packages, optionally preferring wheels then falling back to normal install."""
    base_cmd = [str(pip_path), "install"]
    # First attempt: prefer wheels for speed
    try:
        subprocess.run(base_cmd + ["--only-binary", ":all:"] + packages_to_install, check=True)
        return
    except subprocess.CalledProcessError:
        pass
    # Fallback: normal install (may build sdists)
    subprocess.run(base_cmd + packages_to_install, check=True)


def setup_package_venv(package_name: str, packages: dict[str, dict]) -> Path:
    """Set up a virtual environment for a PyPI package."""
    package_info = packages[package_name]
    if package_info["type"] == "stdlib":
        # Use shared stdlib environment
        return setup_stdlib_venv()

    # Handle PyPI packages
    venv_path = ENVS_DIR / f"{package_name}_env"
    print(f"Setting up venv for {package_name}...")

    # Create venv if it doesn't exist
    if not venv_path.exists():
        subprocess.run(["python3", "-m", "venv", str(venv_path)], check=True)
        pip_path = venv_path / "bin" / "pip"
        # Install testing dependencies first
        _pip_install_with_fallback(pip_path, ["hypothesis", "pytest"])
        # Install the target package from PyPI
        _pip_install_with_fallback(pip_path, [package_name])

        print(
            f"✅ {package_name} venv created with hypothesis, pytest, and {package_name}"
        )
    else:
        print(f"✅ {package_name} venv already exists")

    return venv_path


def get_worker_dir(worker_id: int) -> Path:
    """Get or create worker directory with Claude commands setup."""
    worker_dir = WORKER_DIR_PREFIX / str(worker_id)
    worker_dir.mkdir(parents=True, exist_ok=True)

    # Set up .claude/commands/hypo.md once per worker
    claude_dir = worker_dir / ".claude" / "commands"
    hypo_command_file = claude_dir / "hypo.md"

    if not hypo_command_file.exists():
        claude_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(HYPO_COMMAND, hypo_command_file)

    return worker_dir


def call_claude(
    module_name: str,
    venv_path: Path,
    worker_dir: Path,
    package_name: str,
    timeout: int = 3600,
    model: str = "opus",
) -> str:
    """Run Claude hypo command and return call_id."""
    call_id = str(uuid.uuid4())[:8]
    venv_python = venv_path / "bin" / "python3"

    # Set up environment
    env = {
        "PYTHON": str(venv_python),  # Tell hypo.md which Python to use
        **dict(subprocess.os.environ),
    }

    # Run Claude with restricted permissions
    try:
        result = subprocess.run(
            [
                "claude",
                "--output-format",
                "json",
                "-p",
                f"/hypo {module_name}",
                "--allowedTools",
                "Bash(python:*)",
                "Bash(pytest:*)",
                "Edit(*.py)",
                "Edit(*.md)",
                "Write(*.py)",
                "Write(*.md)",
                "Update(*.py)",
                "Update(*.md)",
                "Todo",
                "WebFetch",
                "--add-dir",
                # Add the entire venv as accessible so it can read source code
                str(venv_path),
                "--permission-mode",
                "acceptEdits",
                "--model",
                model,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(worker_dir),
            env=env,
        )

        # Parse result
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            data = {
                "error": "Claude failed or returned invalid JSON",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

    except subprocess.TimeoutExpired:
        data = {
            "error": "Claude call timed out",
            "timeout": timeout,
            "module": module_name,
        }

    # Log the call
    data["call_id"] = call_id
    data["module"] = module_name
    data["timestamp"] = datetime.now().isoformat()

    log_dir = RESULTS_DIR / package_name / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    with open(log_dir / f"claude_call_{call_id}.json", "w") as f:
        json.dump(data, f, indent=2)

    return call_id


def collect_results(
    worker_dir: Path, package_name: str, call_id: str, module_name: str
):
    """Collect bug reports and auxiliary files from worker directory."""
    package_results = RESULTS_DIR / package_name
    bug_reports_dir = package_results / "bug_reports"
    aux_files_dir = package_results / "aux_files" / call_id

    bug_reports_dir.mkdir(parents=True, exist_ok=True)
    aux_files_dir.mkdir(parents=True, exist_ok=True)

    # Collect bug reports
    bug_reports = list(worker_dir.glob("bug_report_*.md"))
    bug_report_names = []

    for bug_report in bug_reports:
        shutil.move(str(bug_report), str(bug_reports_dir / bug_report.name))
        bug_report_names.append(bug_report.name)

    # Collect all other generated files (test files, etc.)
    for item in worker_dir.iterdir():
        if item.name.startswith("."):
            continue  # Skip .claude directory
        if item.is_file():
            shutil.copy(str(item), str(aux_files_dir / item.name))
        elif item.is_dir() and item.name != ".claude":
            shutil.copytree(str(item), str(aux_files_dir / item.name))

    # Log call mapping
    mapping_file = package_results / "call_mappings.jsonl"
    mapping_data = {
        "call_id": call_id,
        "module": module_name,
        "timestamp": datetime.now().isoformat(),
        "bug_reports": bug_report_names,
        "aux_files_dir": str(aux_files_dir.relative_to(package_results)),
    }

    with open(mapping_file, "a") as f:
        json.dump(mapping_data, f)
        f.write("\n")

    # Clean worker directory for next use
    for item in worker_dir.iterdir():
        if item.name == ".claude":
            continue  # Keep the .claude directory
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)

    # Extract cost/duration info from the logged Claude call
    cost_str = "N/A"
    duration_str = "N/A"
    error_info = ""

    log_file = RESULTS_DIR / package_name / "logs" / f"claude_call_{call_id}.json"
    if log_file.exists():
        try:
            with open(log_file) as f:
                log_data = json.load(f)

                # Check if there was an error
                if "error" in log_data:
                    error_info = f" [ERROR: {log_data['error'][:60]}]"
                elif log_data.get("is_error", False):
                    result = log_data.get("result", "Unknown error")
                    error_info = f" [ERROR: {result[:60]}]"

                cost = log_data.get("total_cost_usd", 0)
                duration_api_ms = log_data.get("duration_api_ms", 0)

                if cost > 0:
                    cost_str = f"${cost:.4f}"
                if duration_api_ms > 0:
                    duration_str = f"{duration_api_ms/1000:.1f}s"
        except Exception as e:
            error_info = f" [LOG_READ_ERROR: {str(e)[:40]}]"
    else:
        error_info = " [NO_LOG_FILE]"

    # Update progress
    global completed_count
    with progress_lock:
        completed_count += 1
        progress = f"[{completed_count}/{total_count}]"

    print(
        f"✅ {progress} Results collected for {module_name} ({cost_str}, {duration_str}, call_id: {call_id}){error_info}"
    )
    if bug_report_names:
        print(f"   🐛 Found {len(bug_report_names)} bug reports!")


def test_module(task_info: tuple, packages: dict[str, dict], *, model: str = "opus") -> None:
    """Test a single module - designed to run in a thread."""
    worker_id, package_name, module_name = task_info

    print(f"[Worker {worker_id}] Testing {module_name}")

    # Get paths
    package_info = packages[package_name]
    if package_info["type"] == "stdlib":
        venv_path = ENVS_DIR / "stdlib_env"
    else:
        venv_path = ENVS_DIR / f"{package_name}_env"
    worker_dir = get_worker_dir(worker_id)

    # Clean worker directory before starting (remove any stray files from previous runs)
    for item in worker_dir.iterdir():
        if item.name == ".claude":
            continue  # Keep the .claude directory
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)

    call_id = call_claude(module_name, venv_path, worker_dir, package_name, model=model)
    collect_results(worker_dir, package_name, call_id, module_name)


def get_completed_modules() -> set:
    """Get set of modules that have been successfully completed (latest attempt succeeded)."""
    completed = set()

    if not RESULTS_DIR.exists():
        return completed

    # Scan all package result directories
    for package_dir in RESULTS_DIR.iterdir():
        if not package_dir.is_dir():
            continue

        # Check call_mappings.jsonl for completed modules
        mappings_file = package_dir / "call_mappings.jsonl"
        if mappings_file.exists():
            try:
                # Track latest attempt per module
                latest_attempts = {}

                with open(mappings_file) as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            module = data.get("module")
                            timestamp = data.get("timestamp")
                            call_id = data.get("call_id")

                            if module and timestamp and call_id:
                                # Keep track of latest attempt per module
                                if (
                                    module not in latest_attempts
                                    or timestamp > latest_attempts[module]["timestamp"]
                                ):
                                    latest_attempts[module] = {
                                        "timestamp": timestamp,
                                        "call_id": call_id,
                                    }

                # Check if latest attempt for each module was successful
                for module, attempt_info in latest_attempts.items():
                    call_id = attempt_info["call_id"]
                    log_file = package_dir / "logs" / f"claude_call_{call_id}.json"

                    if log_file.exists():
                        try:
                            with open(log_file) as log_f:
                                log_data = json.load(log_f)
                                # Only consider successful calls (no error field, is_error=false, and type=result)
                                if (
                                    "error" not in log_data
                                    and not log_data.get("is_error", False)
                                    and log_data.get("type") == "result"
                                ):
                                    completed.add(module)
                        except Exception:
                            continue

            except Exception:
                continue

    return completed


def run_parallel_tests(
    packages: dict[str, dict], max_workers: int = MAX_WORKERS, *, model: str = "opus", preinstall_workers: int = 10
):
    """Run property-based tests on all packages in parallel."""

    # Setup phase - create all venvs first (parallelized)
    print("🔧 Setting up package environments...")
    pkg_names = list(packages.keys())
    with ThreadPoolExecutor(max_workers=preinstall_workers) as ex:
        futures = [ex.submit(setup_package_venv, name, packages) for name in pkg_names]
        for _ in tqdm(futures, total=len(futures), desc="Preinstall", unit="pkg"):
            _.result()

    # Check for already completed modules
    print("🔍 Checking for already completed modules...")
    completed_modules = get_completed_modules()
    if completed_modules:
        print(
            f"   Found {len(completed_modules)} already completed modules - skipping them"
        )

    # Build task list (skip already completed modules)
    tasks = []
    worker_id = 0
    skipped_count = 0

    for package_name, package_info in packages.items():
        modules = package_info["modules"]
        for module_name in modules:
            if module_name in completed_modules:
                skipped_count += 1
                continue
            tasks.append((worker_id % max_workers, package_name, module_name))
            worker_id += 1

    if skipped_count > 0:
        print(f"   Skipped {skipped_count} already completed modules")

    # Initialize progress tracking
    global total_count, completed_count
    total_count = len(tasks)
    completed_count = 0

    print(
        f"\n🚀 Starting parallel testing of {len(tasks)} modules using {max_workers} workers..."
    )

    # Run tests in parallel
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(test_module, task, packages, model=model) for task in tasks
        ]

        # Wait for all to complete
        for future in futures:
            future.result()

    elapsed = time.time() - start_time
    print(f"\n✅ All tests completed in {elapsed/60:.1f} minutes!")
    print(f"📊 Results saved to: {RESULTS_DIR}")


def main():
    parser = argparse.ArgumentParser(
        description="Parallel property-based testing runner"
    )
    parser.add_argument(
        "packages_file",
        type=Path,
        help="Path to packages JSON file (e.g., packages.json)",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=MAX_WORKERS,
        help=f"Number of parallel workers (default: {MAX_WORKERS})",
    )
    parser.add_argument(
        "--preinstall-workers",
        type=int,
        default=10,
        help="Parallel workers for venv setup (default: 10)",
    )
    parser.add_argument(
        "--model",
        type=str,
        choices=["opus", "sonnet", "haiku"],
        default="opus",
        help="Claude model to use (opus, sonnet, haiku)",
    )

    args = parser.parse_args()
    packages = load_packages(args.packages_file)

    total_packages = len(packages)
    total_modules = sum(len(info["modules"]) for info in packages.values())
    print(
        f"📦 Loaded {total_packages} packages with {total_modules} total modules to test"
    )

    run_parallel_tests(
        packages,
        args.max_workers,
        model=args.model,
        preinstall_workers=args.preinstall_workers
    )


# example usage: `python run.py packages.json --max-workers 1 --model sonnet`
if __name__ == "__main__":
    main()
