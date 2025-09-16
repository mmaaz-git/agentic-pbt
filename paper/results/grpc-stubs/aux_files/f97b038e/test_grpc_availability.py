#!/usr/bin/env python3
"""Test if grpc.beta module is available or needs to be installed."""

import sys

# Try to import grpc
try:
    import grpc
    print("grpc module found")
    print(f"grpc location: {grpc.__file__}")
    
    # Try to access grpc.beta
    try:
        import grpc.beta
        print("grpc.beta submodule found")
        print(f"grpc.beta location: {grpc.beta.__file__}")
    except ImportError as e:
        print(f"grpc.beta not found: {e}")
        
    # Check what's in grpc
    print("\nAttributes in grpc module:")
    for attr in dir(grpc):
        if not attr.startswith('_'):
            print(f"  - {attr}")
            
except ImportError:
    print("grpc module not installed")
    print("To test grpc.beta, you need to install grpcio package:")
    print("  pip install grpcio")
    sys.exit(1)