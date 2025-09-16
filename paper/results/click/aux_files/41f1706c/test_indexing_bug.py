import click.shell_completion as shell_completion
import os

# Simulate what happens in BashComplete.get_completion_args()
# when COMP_WORDS contains carriage returns

test_cases = [
    ("hello world", "1"),  # Normal case
    ("\r", "0"),           # Just carriage return  
    ("\r", "1"),           # Trying to access index 1 when only \r
    ("hello\rworld", "1"), # Carriage return in middle
    ("hello \r world", "2"), # Carriage return as separate "word"
]

for comp_words, comp_cword in test_cases:
    print(f"\nCOMP_WORDS={repr(comp_words)}, COMP_CWORD={comp_cword}")
    
    # This is what BashComplete.get_completion_args() does:
    cwords = shell_completion.split_arg_string(comp_words)
    cword = int(comp_cword)
    print(f"  cwords={cwords}")
    print(f"  cword={cword}")
    
    # Get args (from index 1 to cword)
    args = cwords[1:cword]
    print(f"  args={args}")
    
    # Try to get incomplete word
    try:
        incomplete = cwords[cword]
        print(f"  incomplete={repr(incomplete)}")
    except IndexError as e:
        print(f"  ERROR getting incomplete: {e}")

# Now test a more realistic case - what if the shell actually sends \r?
print("\n\n=== Testing realistic shell completion scenario ===")

# Shell command with carriage return (unlikely but possible)
os.environ["COMP_WORDS"] = "mycmd arg1\rarg2"
os.environ["COMP_CWORD"] = "2"

bash_complete = shell_completion.BashComplete(None, {}, "mycmd", "MYCMD_COMPLETE")

try:
    args, incomplete = bash_complete.get_completion_args()
    print(f"Success: args={args}, incomplete={repr(incomplete)}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

# Test edge case: COMP_CWORD pointing past the actual number of words
print("\n=== Testing COMP_CWORD out of bounds ===")
os.environ["COMP_WORDS"] = "mycmd \r"
os.environ["COMP_CWORD"] = "2"  # Only 1 word after split!

try:
    args, incomplete = bash_complete.get_completion_args()
    print(f"Success: args={args}, incomplete={repr(incomplete)}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")