#!/usr/bin/env python3
"""Minimal reproduction of SetupCfgParser bug in dparse"""

from dparse.dependencies import DependencyFile
from dparse import filetypes

setup_cfg_content = """
[options]
install_requires = 
    requests>=2.28.0
"""

dep_file = DependencyFile(
    content=setup_cfg_content,
    file_type=filetypes.setup_cfg
)

# This will raise AttributeError: 'str' object has no attribute 'name'
dep_file.parse()