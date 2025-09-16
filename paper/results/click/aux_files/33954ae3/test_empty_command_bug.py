import click
from hypothesis import given, strategies as st, example, settings
import subprocess
import tempfile
import os


def test_empty_command_name_bug():
    """Test that functions with names like '_cmd' create commands with empty names"""
    
    # Create a test script with a command that has an empty name
    script_content = '''
import click

@click.command()
def _cmd():
    """This command will have an empty name"""
    click.echo("Hello from empty command")

@click.command()  
def _command():
    """This command will also have an empty name"""
    click.echo("Hello from another empty command")

@click.group()
def cli():
    pass

# These will have empty names
cli.add_command(_cmd)
cli.add_command(_command)

if __name__ == "__main__":
    # Print the command names for debugging
    for name, cmd in cli.commands.items():
        print(f"Command name: '{name}' -> {cmd.name}")
    cli()
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script_content)
        script_path = f.name
    
    try:
        # Run the script to see what happens
        result = subprocess.run(
            ['python3', script_path],
            capture_output=True,
            text=True
        )
        
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        print("Return code:", result.returncode)
        
        # Test that we can actually invoke these commands
        result2 = subprocess.run(
            ['python3', script_path, '--help'],
            capture_output=True,
            text=True
        )
        
        print("\nHelp output:", result2.stdout)
        
        return result
        
    finally:
        os.unlink(script_path)


def test_empty_name_causes_issues():
    """Demonstrate that empty command names can cause issues"""
    
    @click.command()
    def _cmd():
        """Command with empty name"""
        pass
    
    @click.command()
    def _command():
        """Another command with empty name"""
        pass
    
    assert _cmd.name == ""
    assert _command.name == ""
    
    # Both commands have the same empty name!
    # This could cause issues when registering them in a group
    
    @click.group()
    def cli():
        pass
    
    # Add both commands - they have the same name!
    cli.add_command(_cmd)
    cli.add_command(_command)
    
    # Check what happens - the second one overwrites the first!
    assert len(cli.commands) == 1
    assert "" in cli.commands
    assert cli.commands[""] is _command  # The last one wins
    
    print("BUG CONFIRMED: Commands with empty names overwrite each other in groups!")
    return True


if __name__ == "__main__":
    print("Testing empty command name bug...")
    test_empty_command_name_bug()
    print("\nTesting empty name collision...")
    test_empty_name_causes_issues()