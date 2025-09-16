import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sqltrie_env/lib/python3.13/site-packages')

from sqltrie import SQLiteTrie

trie = SQLiteTrie()
trie[('other', 'key')] = b'should_not_appear'

view = trie.view(())

print("Testing view with prefix=()")
print("Added ('other', 'key') to main trie")
print(f"View items: {dict(view.items())}")

if ('other', 'key') in dict(view.items()):
    print("\nBUG CONFIRMED: view(()) should act as identity but changes behavior")
    print("The view should show all items when prefix is (), but it doesn't isolate correctly")
    
print("\n--- Testing actual isolation issue ---")
trie2 = SQLiteTrie()
trie2[('prefix', 'item')] = b'in_prefix'
trie2[('other', 'item')] = b'not_in_prefix'

view2 = trie2.view(('prefix',))
view2_items = dict(view2.items())
print(f"Main trie items: {dict(trie2.items())}")
print(f"View with prefix=('prefix',) items: {view2_items}")

if ('item',) not in view2_items:
    print("\nBUG: View doesn't properly show items under prefix")
if ('other', 'item') in view2_items:
    print("\nBUG: View shows items outside of prefix")