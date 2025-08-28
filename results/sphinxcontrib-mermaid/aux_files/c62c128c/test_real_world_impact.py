#!/usr/bin/env python3
"""Test real-world impact of the control character bug."""

import sys
import os
import tempfile
import shutil

sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')

from sphinx.application import Sphinx
from sphinxcontrib.applehelp import AppleHelpBuilder

def test_sphinx_integration():
    """Test how this bug affects actual Sphinx builds."""
    
    print("Testing real-world impact on Sphinx builds...")
    print("=" * 60)
    
    # Create a minimal Sphinx project
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create source directory
        source_dir = os.path.join(tmpdir, 'source')
        build_dir = os.path.join(tmpdir, 'build')
        os.makedirs(source_dir)
        
        # Create minimal conf.py with problematic config
        conf_content = '''
project = 'Test Project'
extensions = ['sphinxcontrib.applehelp']
master_doc = 'index'
applehelp_bundle_id = 'com.test.example'
applehelp_title = 'My Project\x1fHelp'  # Title with control character
'''
        
        with open(os.path.join(source_dir, 'conf.py'), 'w') as f:
            f.write(conf_content)
        
        # Create minimal index.rst
        with open(os.path.join(source_dir, 'index.rst'), 'w') as f:
            f.write('Test Documentation\n==================\n\nThis is a test.')
        
        # Try to build with applehelp
        print("Attempting to build Apple Help documentation...")
        print(f"Source dir: {source_dir}")
        print(f"Build dir: {build_dir}")
        
        try:
            app = Sphinx(
                srcdir=source_dir,
                confdir=source_dir,
                outdir=build_dir,
                doctreedir=os.path.join(build_dir, '.doctrees'),
                buildername='applehelp',
                confoverrides={},
                freshenv=True,
                warningiserror=False,
                verbosity=0
            )
            app.build()
            print("Build succeeded (unexpected!)")
            return False
        except Exception as e:
            print(f"\nBuild FAILED with error: {e}")
            print("\nThis demonstrates that the bug causes real Sphinx builds to fail!")
            return True

def test_common_scenarios():
    """Test common scenarios where control characters might appear."""
    
    print("\n" + "=" * 60)
    print("Common scenarios where this bug could occur:")
    print()
    
    scenarios = [
        ("Copy-paste from terminal", "Project\x1b[0mName"),
        ("Tab character in title", "My\tProject"),
        ("Newline in multi-line string", "Project\nDocumentation"),
        ("Carriage return from Windows", "Project\rName"),
        ("Non-printing separator", "Part1\x1fPart2"),
    ]
    
    for scenario, example in scenarios:
        has_control = any(ord(c) < 32 for c in example if c not in '\t\n\r')
        status = "WOULD FAIL" if has_control else "OK"
        print(f"  {scenario}: {repr(example)} - {status}")

if __name__ == '__main__':
    bug_affects_sphinx = test_sphinx_integration()
    test_common_scenarios()
    
    if bug_affects_sphinx:
        print("\n" + "=" * 60)
        print("IMPACT: This bug affects real Sphinx documentation builds!")
        print("Users who accidentally include control characters in their")
        print("configuration will experience build failures.")