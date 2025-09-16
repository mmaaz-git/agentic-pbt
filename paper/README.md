This is the supplementary data for the paper.

* `hypo.md` is the final claude code command. It can be placed under `~/.claude/commands/` and invoked with `/hypo <file or directory>`. It corresponds to Appendix A of the paper.
* `reported_bugs/` contains the bug reports written by the agent for the 5 bugs which we manually reported to maintainers. It corresponds to Appendix B of the paper.
* `results/` is the full data written by `python run.py selected_packages.json` for the run included in the paper. It includes all written bug reports, api logs, and files written by the agent.
* `evaluation/` contains the scripts necessary to reproduce our evaluation.
* `score_rubric_initial.md` is the initial rubric we used to score bug reports. `score_rubric_initial` is the less polished form of `score_rubric_final`, and is only provided here for full transparency and reproducibility of the paper. We do not recommend using it in practice.
* `score_results_initial.csv` is the results of `score_rubric_initial`, as graded by Claude Opus 4.1.
* `score_rubric_final.md` is the final rubric we used to score bug reports. This is the prompt we recommend using in practice, over `score_rubric_initial`.
* `score_results_final.csv` is the results of `score_rubric_final`, as graded by Claude Opus 4.1.

## Evaluation

To reproduce our evaluation, follow these steps:

* Run `python pypi_packages.py`.
  * The output will be a `pypi_packages.json` file in the current working directory.
  * The output of this script as of August 13th, 2025 is included in this supplementary materials as `pypi_packages.json`.
* Run `python select_packages.py pypi_packages.json selected_packages.json` to reproduce the paper's sample of repositories.
  * 15 hardcoded pypi packages, 15 hardcoded stdlib packages, and 70 randomly sampled pypi packages.
* Run `python run.py selected_packages.json` to run the evaluation.
  * `run.py` takes two arguments: `--max-workers` (defaulting to 20), and `--model` (defaulting to opus). See `python run.py --help`.
  * The output of `run.py` will be a `results/` directory. Each subdirectory in `results/` will be the the stdlib or pypi package's name, and have the following format:
    * `bug_reports/`
      * `bug_report_$package_$description_$date_$id.md`
    * `logs/`
      * `claude_call_$id.json`
    * `written_files/`
      * `$id`
        * \<arbitrary files written by claude during the anthropic api call corresponding to this id>
    * `call_mappings.jsonl`, with the following format:
      * `call_id`: the anthropic call id
      * `testable_path`: the file or module tested
      * `timestamp`: date executed
      * `bug_reports`: the filename of any bug reports in the `bug_reports` directory written by this api call
* As a post-processing step, run `python clean_data.py results/`. This will clean the data and put the final results in a sibling `clean_results` directory.
