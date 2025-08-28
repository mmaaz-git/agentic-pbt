from sqlalchemy.engine.url import make_url, URL

print("Bug 1: Query parameter with empty string value gets lost")
print("="*60)

# Create URL with empty string query parameter value
original_url = URL.create(
    drivername="postgresql",
    host="localhost",
    database="db",
    query={'key': ''}  # Empty string value
)

url_string = original_url.render_as_string(hide_password=False)
print(f"Original query: {original_url.query}")
print(f"URL string: {url_string}")

parsed_url = make_url(url_string)
print(f"Parsed query: {parsed_url.query}")

print(f"\nBug: Query parameter with empty value lost!")
print(f"Expected: {original_url.query}")
print(f"Got: {parsed_url.query}")

print("\n" + "="*60)
print("Bug 2: Password without username gets lost")
print("="*60)

# Create URL with password but no username
created_url = URL.create(
    drivername="postgresql",
    username=None,
    password="mypassword",
    host="localhost",
    database="db"
)

url_string = created_url.render_as_string(hide_password=False)
print(f"Created URL password: {created_url.password}")
print(f"URL string: {url_string}")

parsed_url = make_url(url_string)
print(f"Parsed URL password: {parsed_url.password}")

print(f"\nBug: Password without username is lost!")
print(f"Expected password: {created_url.password}")
print(f"Got password: {parsed_url.password}")