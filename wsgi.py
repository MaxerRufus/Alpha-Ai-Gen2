from pythonprojectsem1 import create_app

# Default values for development
app = create_app(
    name="default_user",
    dob="2000-01-01",
    email="default@example.com"
)