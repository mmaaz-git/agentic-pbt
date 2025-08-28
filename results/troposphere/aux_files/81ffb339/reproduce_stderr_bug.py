#!/usr/bin/env python3
"""Minimal reproduction of stderr pollution bug in troposphere."""

import sys
import io
from contextlib import redirect_stderr

sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.mediastore import MetricPolicy

# Capture stderr
captured_stderr = io.StringIO()

with redirect_stderr(captured_stderr):
    try:
        # This should raise ValueError for invalid status
        policy = MetricPolicy(ContainerLevelMetrics="INVALID")
    except ValueError as e:
        # Exception is properly caught
        pass

# Check what was written to stderr
stderr_output = captured_stderr.getvalue()

if stderr_output:
    print("BUG CONFIRMED: Library writes to stderr before raising exception")
    print(f"Stderr output: {repr(stderr_output)}")
else:
    print("No bug: Clean exception handling")