from bs4 import BeautifulSoup
from bs4.filter import SoupStrainer

# Minimal reproduction of the case sensitivity bug

# User creates a strainer to find tags with CLASS attribute
strainer = SoupStrainer(attrs={'CLASS': 'highlight'})

# Parse HTML that has a CLASS attribute
html = '<div CLASS="highlight">Important text</div>'
soup = BeautifulSoup(html, 'html.parser')

# The parsed tag has lowercase attributes
div_tag = soup.find('div')
print(f"Parsed tag: {div_tag}")
print(f"Tag attributes: {div_tag.attrs}")  # Shows {'class': 'highlight'}

# The strainer fails to match because it's looking for uppercase 'CLASS'
matches = strainer.matches_tag(div_tag)
print(f"Strainer matches: {matches}")  # False (should be True)

# This also affects find_all with SoupStrainer
results = soup.find_all(strainer)
print(f"find_all results: {results}")  # [] (should find the div)

# The workaround is to use lowercase in the strainer
strainer_lowercase = SoupStrainer(attrs={'class': 'highlight'})
print(f"Lowercase strainer matches: {strainer_lowercase.matches_tag(div_tag)}")  # True