#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.traversal
print('Module file:', pyramid.traversal.__file__)