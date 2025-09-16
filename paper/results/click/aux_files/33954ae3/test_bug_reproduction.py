from hypothesis import given, strategies as st
import click
import click.decorators as decorators


@given(st.lists(st.sampled_from(["_cmd", "_command", "_grp", "_group"]), min_size=2, max_size=4, unique=True))
def test_empty_name_collision_property(func_names):
    """Property test: Commands with names that produce empty strings cause collisions in groups"""
    
    # Create commands with these function names
    commands = []
    for name in func_names:
        def dummy():
            pass
        dummy.__name__ = name
        cmd = decorators.command()(dummy)
        assert cmd.name == ""
        commands.append(cmd)
    
    # Add them to a group
    grp = click.Group()
    for cmd in commands:
        grp.add_command(cmd)
    
    # Bug: All commands have empty name, so only one remains!
    assert len(grp.commands) == 1
    assert "" in grp.commands
    assert grp.commands[""] is commands[-1]


def test_minimal_reproduction():
    """Minimal test case demonstrating the bug"""
    
    @click.command()
    def _cmd():
        """First command"""
        return "first"
    
    @click.command()
    def _command():
        """Second command"""
        return "second"
    
    # Both have empty names
    assert _cmd.name == ""
    assert _command.name == ""
    
    # Create a group and add both
    cli = click.Group()
    cli.add_command(_cmd)
    cli.add_command(_command)
    
    # Only one command remains due to name collision
    assert len(cli.commands) == 1
    assert cli.commands[""] is _command


if __name__ == "__main__":
    print("Running property test...")
    test_empty_name_collision_property(["_cmd", "_command", "_grp", "_group"])
    print("Property test passed - bug confirmed")
    
    print("\nRunning minimal reproduction...")
    test_minimal_reproduction()
    print("Minimal test passed - bug confirmed")