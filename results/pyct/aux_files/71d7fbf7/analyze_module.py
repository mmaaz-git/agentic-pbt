import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyct_env/lib/python3.13/site-packages')

import pyct.build
import inspect

for name, obj in inspect.getmembers(pyct.build):
    if not name.startswith('_'):
        print(f'{name}: {type(obj).__name__}')

print('\nexamples signature:', inspect.signature(pyct.build.examples))
print('get_setup_version signature:', inspect.signature(pyct.build.get_setup_version))