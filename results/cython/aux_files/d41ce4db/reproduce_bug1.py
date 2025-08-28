"""Reproduction script for CythonDebugWriter XML attribute bug"""

import tempfile
import Cython.Debugger.DebugWriter as DebugWriter

# Bug 1: Invalid XML attribute names cause crash
with tempfile.TemporaryDirectory() as tmpdir:
    writer = DebugWriter.CythonDebugWriter(tmpdir)
    writer.module_name = "test"
    writer.start('Module', {'name': 'test'})
    
    # This crashes with ValueError: Invalid attribute name '0'
    writer.add_entry('TestEntry', **{'0': 'value'})
    writer.serialize()