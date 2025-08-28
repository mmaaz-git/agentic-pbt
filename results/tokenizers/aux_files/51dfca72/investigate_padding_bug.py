import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

from tokenizers import ByteLevelBPETokenizer

# Reproduce the padding issue
tokenizer = ByteLevelBPETokenizer()

# Train on sample data
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

# Test inputs from the failing test
texts = ['', '000\x80\x80𐀀']
pad_length = 10

# Enable padding
tokenizer.enable_padding(length=pad_length)

# Encode texts
encodings = tokenizer.encode_batch(texts)

# Check lengths
for i, (text, enc) in enumerate(zip(texts, encodings)):
    print(f"Text {i}: {repr(text)}")
    print(f"  IDs: {enc.ids}")
    print(f"  Tokens: {enc.tokens}")
    print(f"  Length: {len(enc.ids)}")
    print()

lengths = [len(enc.ids) for enc in encodings]
print(f"Lengths: {lengths}")
print(f"Expected all to be: {pad_length}")
print(f"Bug? {not all(l == pad_length for l in lengths)}")