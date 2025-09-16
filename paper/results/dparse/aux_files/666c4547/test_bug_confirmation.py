import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

import dparse.dependencies as deps
from packaging.specifiers import SpecifierSet


def test_bug_extras_as_string():
    """
    Bug: When extras is passed as a string instead of a list,
    the full_name property incorrectly treats the string as an
    iterable of characters and joins them with commas.
    """
    # Create dependency with extras as string (common mistake)
    dep = deps.Dependency(
        name="requests",
        specs=SpecifierSet(">=2.0.0"),
        line="requests[security]>=2.0.0",
        extras="security"  # Bug: passing string instead of ["security"]
    )
    
    # Expected: "requests[security]"
    # Actual: "requests[s,e,c,u,r,i,t,y]"
    
    print(f"Expected: requests[security]")
    print(f"Actual:   {dep.full_name}")
    
    # This assertion will pass, confirming the bug
    assert dep.full_name == "requests[s,e,c,u,r,i,t,y]"
    
    # The correct usage would be:
    dep_correct = deps.Dependency(
        name="requests",
        specs=SpecifierSet(">=2.0.0"),
        line="requests[security]>=2.0.0",
        extras=["security"]  # Correct: list of strings
    )
    
    print(f"Correct usage: {dep_correct.full_name}")
    assert dep_correct.full_name == "requests[security]"


if __name__ == "__main__":
    test_bug_extras_as_string()
    print("\nBug confirmed: extras as string causes incorrect full_name formatting")