import os
import click.shell_completion as shell_completion

# Debug what happens
os.environ["COMP_WORDS"] = "\r\n\t "
os.environ["COMP_CWORD"] = "1"

bash_complete = shell_completion.BashComplete(None, {}, "mycmd", "TEST")

cwords = shell_completion.split_arg_string(os.environ["COMP_WORDS"])
cword = int(os.environ["COMP_CWORD"])

print(f"cwords = {cwords}")
print(f"cword = {cword}")
print(f"len(cwords) = {len(cwords)}")

args = cwords[1:cword]
print(f"args = cwords[1:{cword}] = {args}")

# Now the part that might fail:
print(f"\nTrying to access cwords[{cword}]...")
try:
    incomplete = cwords[cword]
    print(f"Success: incomplete = {repr(incomplete)}")
except IndexError:
    incomplete = ""
    print(f"IndexError caught, using empty string: incomplete = {repr(incomplete)}")

# Check the actual implementation 
print("\n\nActual implementation result:")
args, incomplete = bash_complete.get_completion_args()
print(f"args={args}, incomplete={repr(incomplete)}")