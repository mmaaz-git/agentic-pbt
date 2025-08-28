import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.codeguruprofiler as cgp

# AgentPermissions is also optional (False in props definition)
pg = cgp.ProfilingGroup(
    "MyProfilingGroup",
    ProfilingGroupName="TestGroup",
    AgentPermissions=None  # Optional field set to None
)

# This should also raise TypeError
print(pg.to_dict())