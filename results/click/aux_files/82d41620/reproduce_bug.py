import click.termui

# Minimal reproduction
text = '\x1b'
styled = click.termui.style(text, fg='red')
unstyled = click.termui.unstyle(styled)

print(f"Input text: {repr(text)}")
print(f"After style + unstyle: {repr(unstyled)}")
print(f"Are they equal? {text == unstyled}")
print(f"Bug confirmed: Escape character remains after unstyle")