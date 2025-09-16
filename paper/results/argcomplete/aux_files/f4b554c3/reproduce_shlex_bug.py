#!/usr/bin/env python3
"""
Minimal reproduction of shlex tokenization difference
"""

from argcomplete.packages._shlex import shlex
import shlex as stdlib_shlex

test_cases = ['0:', 'abc:def', 'test:123', 'file:/path', 'http://example.com']

print("Tokenization differences between argcomplete shlex and stdlib shlex:\n")

for test_input in test_cases:
    # argcomplete shlex
    lexer = shlex(test_input, posix=True)
    argcomplete_tokens = list(lexer)
    
    # stdlib shlex
    stdlib_tokens = stdlib_shlex.split(test_input, posix=True)
    
    if argcomplete_tokens != stdlib_tokens:
        print(f"Input: '{test_input}'")
        print(f"  argcomplete: {argcomplete_tokens}")
        print(f"  stdlib:      {stdlib_tokens}")
        print()

print("\nAnalysis:")
print("The argcomplete shlex does not include ':' in wordchars,")
print("causing it to tokenize strings with colons differently than stdlib shlex.")
print("This could break shell completions that involve colons (URLs, paths, etc.).")