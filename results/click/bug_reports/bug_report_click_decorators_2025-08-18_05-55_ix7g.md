# Bug Report: click.decorators Empty Command Name Collision

**Target**: `click.decorators.command`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

Function names that end with `_cmd`, `_command`, `_grp`, or `_group` produce commands with empty names, causing silent overwrites when multiple such commands are added to the same group.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import click
import click.decorators as decorators

@given(st.lists(st.sampled_from(["_cmd", "_command", "_grp", "_group"]), min_size=2, max_size=4, unique=True))
def test_empty_name_collision_property(func_names):
    """Commands with names that produce empty strings cause collisions in groups"""
    
    commands = []
    for name in func_names:
        def dummy():
            pass
        dummy.__name__ = name
        cmd = decorators.command()(dummy)
        assert cmd.name == ""
        commands.append(cmd)
    
    grp = click.Group()
    for cmd in commands:
        grp.add_command(cmd)
    
    assert len(grp.commands) == 1
    assert "" in grp.commands
    assert grp.commands[""] is commands[-1]
```

**Failing input**: `["_cmd", "_command"]`

## Reproducing the Bug

```python
import click

@click.command()
def _cmd():
    """First command"""
    click.echo("First")

@click.command()
def _command():
    """Second command"""
    click.echo("Second")

@click.group()
def cli():
    pass

cli.add_command(_cmd)
cli.add_command(_command)

print(f"Number of commands in group: {len(cli.commands)}")
print(f"Command names: {list(cli.commands.keys())}")
print(f"The second command silently overwrote the first!")

assert _cmd.name == ""
assert _command.name == ""
assert len(cli.commands) == 1
assert cli.commands[""] is _command
```

## Why This Is A Bug

The command name transformation logic strips suffix keywords (`cmd`, `command`, `grp`, `group`) from function names. When a function is named exactly as one of these suffixes with a leading underscore (e.g., `_cmd`), the transformation produces an empty string as the command name. 

This violates the expectation that:
1. Each uniquely named function should produce a unique command
2. Adding multiple commands to a group should not silently overwrite previous commands
3. Command names should be non-empty to avoid collision issues

The bug causes silent data loss - when multiple commands with these special names are added to a group, only the last one remains, and previous commands are lost without warning.

## Fix

```diff
--- a/click/decorators.py
+++ b/click/decorators.py
@@ -241,8 +241,12 @@ def command(
         else:
             cmd_name = f.__name__.lower().replace("_", "-")
             cmd_left, sep, suffix = cmd_name.rpartition("-")
 
             if sep and suffix in {"command", "cmd", "group", "grp"}:
                 cmd_name = cmd_left
+                # Ensure command name is not empty
+                if not cmd_name:
+                    cmd_name = suffix
 
         cmd = cls(name=cmd_name, callback=f, params=params, **attrs)
```