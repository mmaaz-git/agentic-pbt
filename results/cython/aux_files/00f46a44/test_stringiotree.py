import Cython.StringIOTree as StringIOTree

# Test StringIOTree
tree = StringIOTree.StringIOTree()

# Try basic operations
print("Initial empty:", tree.empty())
print("Initial getvalue:", repr(tree.getvalue()))

# Write some data
tree.write("Hello")
print("\nAfter writing 'Hello':")
print("  empty:", tree.empty())
print("  getvalue:", repr(tree.getvalue()))

# Try insertion point
insertion = tree.insertion_point()
print("\nCreated insertion point")

tree.write(" World")
print("After writing ' World':")
print("  getvalue:", repr(tree.getvalue()))

insertion.write("[INSERTED]")
print("After writing to insertion point:")
print("  getvalue:", repr(tree.getvalue()))

# Try reset
tree.reset()
print("\nAfter reset:")
print("  empty:", tree.empty())
print("  getvalue:", repr(tree.getvalue()))