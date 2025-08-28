#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

import sudachipy.tokenizer
print('success - treating as module')
print(f"Module path: {sudachipy.tokenizer.__file__}")