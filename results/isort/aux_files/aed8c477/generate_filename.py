import random
import string
from datetime import datetime

# Generate filename for bug report
target_name = "isort_identify"
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
hash_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))

filename = f"bug_report_{target_name}_{timestamp}_{hash_str}.md"
print(filename)