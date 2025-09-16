import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

from tokenizers import ByteLevelBPETokenizer

# Reproduce the vocab size issue
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

# Check if '0' is already in vocabulary
vocab = tokenizer.get_vocab()
print(f"Is '0' in vocabulary before adding? {'0' in vocab}")
print(f"Token ID for '0': {tokenizer.token_to_id('0')}")

# Get initial vocab size
size_before = tokenizer.get_vocab_size(with_added_tokens=True)
print(f"Vocab size before adding: {size_before}")

# Try to add '0' as a token
num_added = tokenizer.add_tokens(['0'])
print(f"Number of tokens added: {num_added}")

# Get new vocab size
size_after = tokenizer.get_vocab_size(with_added_tokens=True)
print(f"Vocab size after adding: {size_after}")

print(f"Expected: {size_before + num_added}")
print(f"Actual: {size_after}")
print(f"Bug? {size_after != size_before + num_added}")