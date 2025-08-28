import click

text = ''
styled = click.style(text, fg='red', bg='blue', bold=True)

print(f"Input: {repr(text)}")
print(f"Output: {repr(styled)}")
print(f"Expected: ''")
print(f"Actual length: {len(styled)} characters")

assert styled == '', f"Expected empty string, got {repr(styled)}"