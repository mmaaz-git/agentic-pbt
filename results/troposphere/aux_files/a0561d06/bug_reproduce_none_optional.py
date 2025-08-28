import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.codeguruprofiler as cgp

# This should work since ComputePlatform is optional (False in props definition)
pg = cgp.ProfilingGroup(
    "MyProfilingGroup",
    ProfilingGroupName="TestGroup",
    ComputePlatform=None  # Optional field set to None
)

# This raises TypeError but shouldn't
print(pg.to_dict())