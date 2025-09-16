"""Build input files for the Qt collection generator - Simplified for testing."""

import html
import os
import posixpath
import re

__version__ = '2.0.0'
__version_info__ = (2, 0, 0)

_idpattern = re.compile(
    r'(?P<title>.+) \(((class in )?(?P<id>[\w\.]+)( (?P<descr>\w+))?\))$')

section_template = '<section title="%(title)s" ref="%(ref)s"/>'
keyword_item_template = '<keyword name="%(keyword)s" id="%(id)s" ref="%(ref)s"/>'

# Simplified make_filename function
def make_filename(name: str) -> str:
    """Create a safe filename from a name."""
    # Remove/replace unsafe characters
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '-', name)
    return name.lower()

# Simplified canon_path function
def canon_path(path: str) -> str:
    """Canonicalize a path."""
    # Simple normalization
    return os.path.normpath(path).replace('\\', '/')

# Key utility functions that we can test
def _make_filename(name: str) -> str:
    """Create a filename from a document name."""
    return make_filename(name) + '.html'

def _idpattern_match(text: str) -> dict[str, str] | None:
    """Match and extract components from index pattern."""
    match = _idpattern.match(text)
    if match:
        return match.groupdict()
    return None

def escape_for_xml(text: str) -> str:
    """Escape text for safe XML inclusion."""
    return html.escape(text, quote=True)

def build_section_xml(title: str, ref: str, indent: int = 0) -> str:
    """Build a section XML element."""
    spaces = ' ' * (4 * indent)
    return spaces + section_template % {
        'title': escape_for_xml(title),
        'ref': escape_for_xml(ref)
    }

def build_keyword_xml(keyword: str, id: str, ref: str, indent: int = 0) -> str:
    """Build a keyword XML element."""
    spaces = ' ' * (4 * indent)
    return spaces + keyword_item_template % {
        'keyword': escape_for_xml(keyword),
        'id': escape_for_xml(id),
        'ref': escape_for_xml(ref)
    }

def normalize_namespace(namespace: str) -> str:
    """Normalize a namespace for Qt help."""
    # Ensure it starts with correct prefix
    if not namespace.startswith('org.sphinx.'):
        namespace = 'org.sphinx.' + namespace
    # Remove any invalid characters
    namespace = re.sub(r'[^a-zA-Z0-9.]', '', namespace)
    return namespace

def split_index_entry(entry: str) -> tuple[str, str | None]:
    """Split an index entry into main text and parenthetical content."""
    match = _idpattern.match(entry)
    if match:
        return match.group('title'), match.group('id')
    return entry, None

def canonicalize_path(base_path: str, rel_path: str) -> str:
    """Canonicalize a path relative to a base path."""
    if os.path.isabs(rel_path):
        return rel_path
    return canon_path(posixpath.join(base_path, rel_path))

def merge_keywords(keywords1: list[tuple[str, str, str]], 
                  keywords2: list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
    """Merge two lists of keyword tuples, removing duplicates."""
    seen = set()
    result = []
    for kw in keywords1 + keywords2:
        if kw not in seen:
            seen.add(kw)
            result.append(kw)
    return result