# Agentic Property-Based Testing

This is the code to run our property-based testing agent.

For the artifacts from the paper, including bug reports and human evaluations, see the `paper` directory.

## Running the agent

The agent is a Claude Code command. You will need to have Claude Code [installed](https://docs.anthropic.com/en/docs/claude-code/install-claude-code) to run it.

The command is contained in the `hypo.md` file. You will need to place this file in the `.claude/commands/` directory, which can either be in `~` or in whichever directory you are running the agent from. The agent can then be invoked with `/hypo <target>`.

You will need `pytest`, `hypothesis`, and the package you are testing installed.

The agent takes one argument, which is the target to test. This can be a file, a function, or a module. Ifno argument is given, it will test the entire codebase, i.e., the current working directory. You can pass whichever other arguments that Claude Code supports, like the model, permissions, etc.

Example usage:

```bash
claude "/hypo numpy"
claude "/hypo statistics.median" --model opus
```

You can also just start Claude Code, and then invoke the agent.

## Agent runner

The `run.py` script is a wrapper around the agent to test multiple packages, in parallel. It is what was used in the paper. This script does not require any other requirements beyond the standard library (of course, you still need to have Claude Code installed).

Note that the runner operates at the *module* level.

The only required argument is the path to a json file containing the packages to test, and which modules to test within each package. It looks like:

```json
{
    "pathlib": {
        "type": "stdlib",
        "modules": ["pathlib"]
    },
  "numpy": {
        "type": "pypi",
        "modules": ["numpy"]
  }
}
```

The keys in the json file are the package names, either the standard library name or the PyPI name. For standard library packages, specify "stdlib", and for PyPI packages, specify "pypi". This is important so the runner knows how to set up the virtual environment.

The runner takes two optional arguments:
- `--max-workers`: the number of parallel workers to use. Default is 20.
- `--model`: the model to use. Default is "opus".

The runner will output all bug reports in the `results/` directory.

Example usage:

```bash
python run.py packages.json
```

In the `example_packages/` directory, there are some example package json files to test:
- `packages_mini.json`: a mini set of packages to test (1 stdlib package, 1 pypi package)
- `packages_10000.json`: top 10,000 pypi packages, with the main module and all submodules one level deep

The packages tested in the paper are in the `paper/` directory.

### How the agent works

The runner sets up virtual environments, with `venv` for each package. Standard library packages just use the same virtual environment, and PyPI packages get their own virtual environment. The runner will also install `pytest` and `hypothesis` in each virtual environment.

It then then sets up `MAX_WORKERS` directories, which is a "sandbox" for the agent to run in. It only has permission to edit files within this sandbox. Each worker directory also contains `.claude/commands/hypo.md`, so that the agent can run. The runner parallelizes across modules.

Note that the runner also checks if the module has already been tested, and skips it if so. So, you can easily resume a run by just running the runner again.

### Security

The runner calls the agent with restricted permissions. It only has permission to read/write/edit files in the sandbox in which it is called, and it also has read permission to the virtual environment, so that it can read the source code of the package. Furthermore, it can only write/edit `.py` and `.md` files. The only bash commands it can run are `python` and `pytest`. Note that because of how the virtual environments are set up, the Python command will be `python`. Lastly, it also has access to the `Todo` and `WebFetch` tools.

You should still be careful with the runner, because running arbitrary code is dangerous!

### Outputs

In the `results/` directory, there will be a directory named after the package. Each of these will have the following structure:
- `bug_reports/`
    - \<all bug reports written by the agent>
- `logs/`
    - `claude_call_$id.json` \<the log of the Claude Code call corresponding to this id>
- `aux_files/`
    - `$id`
        - \<all other files written by Claude Code during the Claude Code call corresponding to this id, e.g., Python files>
- `call_mappings.jsonl`, with the following format:
    - `call_id`: the Claude Code call id
    - `module`: the module tested
    - `timestamp`: date executed
    - `bug_reports`: the filename of any bug reports in the `bug_reports` directory written by this Claude Code call
    - `aux_files_dir`: the directory containing all files written by the agent during the Claude Code call corresponding to this id

### Ranking the bug reports

To score the bug reports, you can run `python scoring.py results/`. This uses the rubric contained in that file, and passes it to Claude (not Claude Code, just the Claude API). This script outputs a CSV file containing the scores for each bug report, as well as the reasoning.

It takes the following arguments:
- `--retry-failures`: if set, it will retry the bug reports that failed to score. This requires the CSV file to already exist, as it checks for failed scores in the CSV file.
- `reports_dir`: the directory containing the bug reports to score. Default is "results/".
- `--max-workers`: the number of parallel workers to use. Default is 20.
- `--model`: the model to use. Default is "claude-opus-4-1" (note model names are different when using the Claude API directly)
- `--csv-path`: the path to the CSV file to write the results to. Default is "scoring_results.csv".

Example usage:

```bash
python scoring.py results/
```
