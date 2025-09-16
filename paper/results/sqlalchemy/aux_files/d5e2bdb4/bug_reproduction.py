"""Minimal reproduction of SQLAlchemy not_ simplification bug."""

import sqlalchemy.sql as sql

# Bug: sql.not_() doesn't simplify Python booleans
print("BUG DEMONSTRATION")
print("=" * 50)

# The issue
print("\n1. not_ with Python booleans creates parameters instead of constants:")
print(f"   sql.not_(True):  {str(sql.not_(True))}")
print(f"   sql.not_(False): {str(sql.not_(False))}")

print("\n2. not_ with SQL constants works correctly:")
print(f"   sql.not_(sql.true()):  {str(sql.not_(sql.true()))}")
print(f"   sql.not_(sql.false()): {str(sql.not_(sql.false()))}")

print("\n3. This breaks logical simplification:")
buggy_expr = sql.or_(sql.false(), sql.not_(False))
print(f"   sql.or_(sql.false(), sql.not_(False))")
print(f"   Result:   '{str(buggy_expr)}'")
print(f"   Expected: 'true'")
print(f"   Reason:   false OR true should simplify to true")

print("\n4. Real-world impact:")
print("   Users mixing Python booleans with SQL expressions get unexpected results.")
print("   Logical simplifications don't work as expected.")

# Additional test case
print("\n5. Another failing case:")
expr = sql.and_(sql.true(), sql.not_(False))
print(f"   sql.and_(sql.true(), sql.not_(False))")
print(f"   Result:   '{str(expr)}'")
print(f"   Expected: 'true'")
print(f"   Reason:   true AND true should simplify to true")