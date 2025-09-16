#!/usr/bin/env python3
import sys
import tempfile
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')
from copier._cli import _Subcommand

with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml') as f:
    f.flush()
    subcommand = _Subcommand(executable="copier")
    subcommand.data_file_switch(f.name)