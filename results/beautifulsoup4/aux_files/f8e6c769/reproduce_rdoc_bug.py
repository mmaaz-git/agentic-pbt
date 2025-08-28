"""Reproduce the rdoc() bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/beautifulsoup4_env/lib/python3.13/site-packages')

import bs4.diagnose as diagnose
import random

# Set seed for reproducibility
random.seed(42)

# Test rdoc with small values
for num_elements in range(0, 10):
    result = diagnose.rdoc(num_elements)
    content = result[6:-7]  # Skip '<html>' and '</html>'
    print(f"num_elements={num_elements}: content_length={len(content)}, content={repr(content[:50])}")

# Let's also understand what happens inside rdoc for num_elements=1
print("\n--- Detailed analysis for num_elements=1 ---")
random.seed(42)
result = diagnose.rdoc(1)
print(f"Full result: {repr(result)}")
print(f"Starts with '<html>': {result.startswith('<html>')}")
print(f"Ends with '</html>': {result.endswith('</html>')}")

# Let's trace through the logic manually
print("\n--- Manual trace of rdoc(1) logic ---")
random.seed(42)
elements = []
for i in range(1):
    choice = random.randint(0, 3)
    print(f"Iteration {i}: choice={choice}")
    if choice == 0:
        # New tag
        tag_names = ["p", "div", "span", "i", "b", "script", "table"]
        tag_name = random.choice(tag_names)
        element = f"<{tag_name}>"
        print(f"  Adding opening tag: {element}")
        elements.append(element)
    elif choice == 1:
        # Sentence
        sentence = diagnose.rsentence(random.randint(1, 4))
        print(f"  Adding sentence: {sentence}")
        elements.append(sentence)
    elif choice == 2:
        # Close tag
        tag_names = ["p", "div", "span", "i", "b", "script", "table"]
        tag_name = random.choice(tag_names)
        element = f"</{tag_name}>"
        print(f"  Adding closing tag: {element}")
        elements.append(element)
    else:
        # choice == 3, nothing added
        print(f"  Choice 3: nothing added to elements")

print(f"\nElements list: {elements}")
joined = "\n".join(elements)
print(f"Joined elements: {repr(joined)}")
final = "<html>" + joined + "</html>"
print(f"Final result: {repr(final)}")