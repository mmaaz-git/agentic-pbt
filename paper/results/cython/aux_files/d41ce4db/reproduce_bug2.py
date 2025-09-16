"""Reproduction script for CythonDebugWriter XML element name bug"""

import tempfile
import Cython.Debugger.DebugWriter as DebugWriter

# Bug 2: Invalid XML element names cause crash
with tempfile.TemporaryDirectory() as tmpdir:
    writer = DebugWriter.CythonDebugWriter(tmpdir)
    writer.module_name = "test"
    writer.start('Module', {'name': 'test'})
    
    # This crashes with ValueError: Invalid tag name '0'
    writer.add_entry('0', value='test')
    writer.serialize()