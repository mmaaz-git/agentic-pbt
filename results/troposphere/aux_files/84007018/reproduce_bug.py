import troposphere.transfer as transfer
import json

# Arabic-Indic digits that Python accepts but AWS CloudFormation does not
arabic_number = "١٢٣"  # Arabic-Indic for "123"

# The validator accepts it
result = transfer.double(arabic_number)
print(f"Input: {arabic_number!r}")
print(f"Output: {result!r}")
print(f"Type: {type(result)}")

# When serialized for CloudFormation, it remains as Unicode
cloudformation_json = json.dumps({"Value": result})
print(f"CloudFormation JSON: {cloudformation_json}")

# AWS expects "123" but gets "\u0661\u0662\u0663"