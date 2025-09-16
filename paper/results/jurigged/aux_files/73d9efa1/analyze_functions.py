import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

import inspect
import jurigged.recode

# Look at specific functions
print("=== virtual_file function ===")
print("Source code:")
print(inspect.getsource(jurigged.recode.virtual_file))

print("\n=== make_recoder function ===")
print("Source code:")
print(inspect.getsource(jurigged.recode.make_recoder))

print("\n=== Recoder.patch method ===")
print("Source code:")
print(inspect.getsource(jurigged.recode.Recoder.patch))

print("\n=== Recoder.patch_module method ===")
print("Source code:")
print(inspect.getsource(jurigged.recode.Recoder.patch_module))

print("\n=== OutOfSyncException ===")
print("Base classes:", jurigged.recode.OutOfSyncException.__bases__)