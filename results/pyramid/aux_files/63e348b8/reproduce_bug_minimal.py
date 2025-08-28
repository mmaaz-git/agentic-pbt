#!/usr/bin/env python3
"""Minimal reproduction of RequestContext leak bug in pyramid.scripting"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.scripting import prepare
from pyramid.threadlocal import get_current_request
from pyramid.config import Configurator
from pyramid.interfaces import IRootFactory


def main():
    # Setup
    config = Configurator()
    registry = config.registry
    
    # Register a root factory that always fails
    def failing_root_factory(request):
        raise ValueError("Simulated failure")
    
    registry.registerUtility(failing_root_factory, IRootFactory)
    
    # Check initial state - should be no request in threadlocal
    try:
        initial = get_current_request()
        print(f"Initial request in threadlocal: {initial}")
    except:
        print("Initial: No request in threadlocal (expected)")
    
    # Call prepare() which will fail
    try:
        env = prepare(registry=registry)
        print("ERROR: prepare() should have raised ValueError")
    except ValueError as e:
        print(f"prepare() failed as expected: {e}")
    
    # Check final state - should still be no request
    try:
        leaked = get_current_request()
        print(f"BUG: Request leaked in threadlocal: {leaked}")
        print("The RequestContext was not cleaned up after exception!")
        return True
    except:
        print("Final: No request in threadlocal (correct)")
        return False


if __name__ == "__main__":
    has_bug = main()
    sys.exit(1 if has_bug else 0)