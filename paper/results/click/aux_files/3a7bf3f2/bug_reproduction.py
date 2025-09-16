#!/usr/bin/env python3
"""Standalone reproduction of the bugs found in click.formatting"""

import click.formatting


def bug1_iter_rows_no_truncation():
    """iter_rows doesn't truncate rows to requested column count"""
    print("Bug 1: iter_rows doesn't truncate")
    print("-" * 40)
    
    rows = [('col1', 'col2', 'col3')]
    col_count = 2
    
    result = list(click.formatting.iter_rows(rows, col_count))
    
    print(f"Input: rows={rows}")
    print(f"Requested col_count: {col_count}")
    print(f"Expected output: [('col1', 'col2')]")
    print(f"Actual output: {result}")
    print(f"Bug: Row has {len(result[0])} columns instead of {col_count}")
    print()


def bug2_write_usage_empty_args():
    """write_usage loses program name when args is empty"""
    print("Bug 2: write_usage loses program name with empty args")
    print("-" * 40)
    
    formatter = click.formatting.HelpFormatter()
    prog = 'mycommand'
    args = ''  # Empty arguments
    
    formatter.write_usage(prog, args)
    output = formatter.getvalue()
    
    print(f"Program name: '{prog}'")
    print(f"Arguments: '{args}' (empty)")
    print(f"Expected output to contain: '{prog}'")
    print(f"Actual output: {repr(output)}")
    print(f"Bug: Program name is missing from output!")
    print()


if __name__ == "__main__":
    bug1_iter_rows_no_truncation()
    bug2_write_usage_empty_args()