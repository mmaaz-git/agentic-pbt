import troposphere.ecr as ecr

# The boolean function accepts mixed case but not all uppercase
print("Testing case sensitivity in boolean function:")
print(f"ecr.boolean('true') = {ecr.boolean('true')}")
print(f"ecr.boolean('True') = {ecr.boolean('True')}")

try:
    result = ecr.boolean('TRUE')
    print(f"ecr.boolean('TRUE') = {result}")
except ValueError:
    print("ecr.boolean('TRUE') raises ValueError!")

print(f"\necr.boolean('false') = {ecr.boolean('false')}")  
print(f"ecr.boolean('False') = {ecr.boolean('False')}")

try:
    result = ecr.boolean('FALSE')
    print(f"ecr.boolean('FALSE') = {result}")
except ValueError:
    print("ecr.boolean('FALSE') raises ValueError!")