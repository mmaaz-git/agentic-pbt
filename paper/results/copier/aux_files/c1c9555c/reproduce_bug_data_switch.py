#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')
from copier._cli import _Subcommand

subcommand = _Subcommand(executable="copier")
subcommand.data_switch(["MY_VAR"])