import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/spacy-wordnet_env/lib/python3.13/site-packages')

from spacy_wordnet.__utils__ import fetch_wordnet_lang

# Test with normal unsupported language
try:
    result = fetch_wordnet_lang("xyz")
except Exception as e:
    print(f"Normal case - Error message: {repr(str(e))}")

# Test with newline character
try:
    result = fetch_wordnet_lang("\n")
except Exception as e:
    print(f"Newline case - Error message: {repr(str(e))}")
    print(f"Error message bytes: {str(e).encode()}")

# Test with other whitespace characters
for char, name in [("\t", "tab"), ("\r", "carriage return"), (" ", "space")]:
    try:
        result = fetch_wordnet_lang(char)
    except Exception as e:
        print(f"{name} case - Error message: {repr(str(e))}")