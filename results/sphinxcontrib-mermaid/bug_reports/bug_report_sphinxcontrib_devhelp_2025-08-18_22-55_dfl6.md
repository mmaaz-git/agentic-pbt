# Bug Report: sphinxcontrib.devhelp Control Characters Cause Invalid XML

**Target**: `sphinxcontrib.devhelp`
**Severity**: High
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

Control characters in documentation titles or function names cause sphinxcontrib.devhelp to generate invalid XML files that cannot be parsed, making the devhelp documentation unusable.

## Property-Based Test

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')

import xml.etree.ElementTree as etree
from hypothesis import given, strategies as st

@given(st.text())
def test_xml_attribute_escaping(text):
    """Test that XML attributes handle all text properly without errors."""
    elem = etree.Element('test', name=text, link=text)
    xml_str = etree.tostring(elem, encoding='unicode')
    parsed = etree.fromstring(xml_str)
    expected_text = text.replace('\x00', ' ')
    assert parsed.get('name') == expected_text
    assert parsed.get('link') == expected_text
```

**Failing input**: `'\x08'` (and other control characters like `\x00`, `\x01`, `\x0B`, `\x0C`, `\x0E`, `\x1F`)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')

import xml.etree.ElementTree as etree
import gzip
import tempfile

# Create XML as sphinxcontrib.devhelp does
title_with_control_char = "Documentation\x08"  # Backspace character
root = etree.Element('book',
                     title=title_with_control_char,
                     name="Project",
                     link="index.html",
                     version="1.0")

# Add functions element
functions = etree.SubElement(root, 'functions')
etree.SubElement(functions, 'function', name="func\x0C", link='api.html')

# Write to gzipped file
tree = etree.ElementTree(root)
with tempfile.NamedTemporaryFile(suffix='.devhelp.gz', delete=False) as f:
    output_file = f.name

with gzip.GzipFile(filename=output_file, mode='w', mtime=0) as gz:
    tree.write(gz, 'utf-8')

# Try to read back - THIS FAILS
with gzip.open(output_file, 'rt', encoding='utf-8') as gz:
    xml_content = gz.read()

# This raises: xml.etree.ElementTree.ParseError: not well-formed (invalid token)
parsed = etree.fromstring(xml_content)
```

## Why This Is A Bug

Control characters are not valid in XML 1.0 and cause the generated devhelp files to be unparseable. This makes the documentation completely unusable in GNOME Devhelp or any XML-based documentation viewer. Control characters can enter documentation through copy-paste errors, encoding issues, or auto-generated content from source code.

## Fix

```diff
--- a/sphinxcontrib/devhelp/__init__.py
+++ b/sphinxcontrib/devhelp/__init__.py
@@ -61,10 +61,23 @@ class DevhelpBuilder(StandaloneHTMLBuilder):
     def handle_finish(self) -> None:
         self.build_devhelp(self.outdir, self.config.devhelp_basename)
 
+    def _sanitize_xml_text(self, text: str) -> str:
+        """Remove control characters that are invalid in XML 1.0."""
+        # XML 1.0 only allows: #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD]
+        # Remove all control characters except tab, newline, and carriage return
+        sanitized = []
+        for char in text:
+            code = ord(char)
+            if code in (0x09, 0x0A, 0x0D) or (0x20 <= code <= 0xD7FF) or (0xE000 <= code <= 0xFFFD):
+                sanitized.append(char)
+        return ''.join(sanitized)
+
     def build_devhelp(self, outdir: str | os.PathLike[str], outname: str) -> None:
         logger.info(__('dumping devhelp index...'))
 
         # Basic info
+        html_title = self._sanitize_xml_text(self.config.html_title)
+        project = self._sanitize_xml_text(self.config.project)
+        version = self._sanitize_xml_text(self.config.version)
         root = etree.Element('book',
-                             title=self.config.html_title,
-                             name=self.config.project,
+                             title=html_title,
+                             name=project,
                              link="index.html",
-                             version=self.config.version)
+                             version=version)
         tree = etree.ElementTree(root)
 
         # TOC
@@ -88,8 +101,8 @@ class DevhelpBuilder(StandaloneHTMLBuilder):
                     write_toc(subnode, item)
             elif isinstance(node, nodes.reference):
                 parent.attrib['link'] = node['refuri']
-                parent.attrib['name'] = node.astext()
+                parent.attrib['name'] = self._sanitize_xml_text(node.astext())
 
         matcher = NodeMatcher(addnodes.compact_paragraph, toctree=Any)
         for node in tocdoc.findall(matcher):
@@ -103,10 +116,10 @@ class DevhelpBuilder(StandaloneHTMLBuilder):
                 pass
             elif len(refs) == 1:
                 etree.SubElement(functions, 'function',
-                                 name=title, link=refs[0][1])
+                                 name=self._sanitize_xml_text(title), link=refs[0][1])
             else:
                 for i, ref in enumerate(refs):
                     etree.SubElement(functions, 'function',
-                                     name="[%d] %s" % (i, title),
+                                     name=self._sanitize_xml_text("[%d] %s" % (i, title)),
                                      link=ref[1])
 
             if subitems:
```