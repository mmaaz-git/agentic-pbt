import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
import troposphere.location
print('success - treating as module')
print(f"Module file: {troposphere.location.__file__}")