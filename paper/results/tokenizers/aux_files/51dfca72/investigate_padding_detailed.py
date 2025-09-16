import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

from tokenizers import ByteLevelBPETokenizer

# Create and train tokenizer
tokenizer = ByteLevelBPETokenizer()
training_data = [
    "Hello world",
    "This is a test",
    "Testing tokenizers",
    "The quick brown fox jumps over the lazy dog",
    "1234567890",
    "Special characters: !@#$%^&*()",
    "Unicode: café, naïve, résumé",
    "Emojis: 😀 🎉 🚀",
    "Mixed case: HeLLo WoRLd",
    "Punctuation: Hello, world! How are you?",
    "Numbers and text: 42 is the answer",
]
tokenizer.train_from_iterator(training_data, vocab_size=500, min_frequency=1)

# Test the problematic text without padding first
text = '000\x80\x80𐀀'
print("WITHOUT PADDING:")
encoding = tokenizer.encode(text)
print(f"Text: {repr(text)}")
print(f"IDs: {encoding.ids}")
print(f"Tokens: {encoding.tokens}")
print(f"Length: {len(encoding.ids)}")
print()

# Now with padding
print("WITH PADDING (length=10):")
tokenizer.enable_padding(length=10)
encoding_padded = tokenizer.encode(text)
print(f"Text: {repr(text)}")
print(f"IDs: {encoding_padded.ids}")
print(f"Tokens: {encoding_padded.tokens}")
print(f"Length: {len(encoding_padded.ids)}")
print()

# Check if truncation needs to be enabled separately
print("WITH PADDING AND TRUNCATION (max_length=10):")
tokenizer.enable_truncation(max_length=10)
encoding_both = tokenizer.encode(text)
print(f"Text: {repr(text)}")
print(f"IDs: {encoding_both.ids}")
print(f"Tokens: {encoding_both.tokens}")
print(f"Length: {len(encoding_both.ids)}")
print()

# Test with a simpler long text
print("SIMPLE LONG TEXT WITH PADDING (length=5):")
tokenizer2 = ByteLevelBPETokenizer()
tokenizer2.train_from_iterator(["a b c d e f g h"], vocab_size=50, min_frequency=1)
tokenizer2.enable_padding(length=5)
long_text = "a b c d e f g h"
enc = tokenizer2.encode(long_text)
print(f"Text: {repr(long_text)}")
print(f"IDs: {enc.ids}")
print(f"Tokens: {enc.tokens}")
print(f"Length: {len(enc.ids)} (expected 5)")