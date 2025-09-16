import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

import tokenizers.decoders as decoders

# Minimal reproduction of the Strip decoder bug
strip_decoder = decoders.Strip(left=2, right=1)
tokens = ["hello", "world"]
result = strip_decoder.decode(tokens)

print(f"Input tokens: {tokens}")
print(f"Strip(left=2, right=1).decode(tokens)")
print(f"Expected: 'lloor' (strip 2 from left, 1 from right of each token)")
print(f"Actual:   '{result}'")
print(f"Bug: The Strip decoder does not strip any characters!")