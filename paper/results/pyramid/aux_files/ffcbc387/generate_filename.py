#!/usr/bin/env python3
import random
import string
from datetime import datetime

# Generate filename for bug report
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
hash_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
filename = f"bug_report_pyramid_encode_urlencode_{timestamp}_{hash_chars}.md"
print(filename)