#!/usr/bin/env python3
"""Check if paramiko is installed and usable."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/types-paramiko_env/lib/python3.13/site-packages')

try:
    import paramiko
    print(f"✓ paramiko module found at: {paramiko.__file__}")
    print(f"✓ paramiko version: {paramiko.__version__}")
    
    # Check if util module is accessible
    from paramiko import util
    print(f"✓ paramiko.util module found")
    
    # Check if the functions we want to test exist
    funcs_to_test = ['inflate_long', 'deflate_long', 'mod_inverse', 'clamp_value', 'constant_time_bytes_eq']
    for func_name in funcs_to_test:
        if hasattr(util, func_name):
            print(f"✓ Function {func_name} found in paramiko.util")
        else:
            print(f"✗ Function {func_name} NOT found in paramiko.util")
            
    # Check Message class
    from paramiko import Message
    print(f"✓ Message class found")
    
    # Check BER module
    try:
        from paramiko import ber
        print(f"✓ paramiko.ber module found")
    except ImportError as e:
        print(f"✗ paramiko.ber module not found: {e}")
        
except ImportError as e:
    print(f"✗ paramiko not installed: {e}")
    print("paramiko-stubs is a type stub package and needs the actual paramiko library")