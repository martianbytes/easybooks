# EasyBooks

A Django-based web application for managing books.

------------------------------------------------------------
PROJECT SETUP
------------------------------------------------------------

1. Create virtual environment
   python -m venv .venv

2. Activate virtual environment

   Windows:
   .venv\Scripts\activate

   Linux / macOS:
   source .venv/bin/activate

3. Install dependencies
   `pip install -r requirements.txt`

4. Apply migrations (first time setup)
   python manage.py migrate

------------------------------------------------------------
CODE FORMATTING
------------------------------------------------------------

This project uses Black for Python code formatting.

Format entire project from the terminal:
   `black .`

Recommended usage:
- Run before committing code
- Keeps Python code style consistent across team members

Install Black (if not already installed):
   pip install black

------------------------------------------------------------
TECH STACK
------------------------------------------------------------

- Django
- Python
- HTML / CSS (Django templates)

------------------------------------------------------------
NOTES
------------------------------------------------------------

- Always activate the virtual environment before working
- Do not commit .venv/ or db.sqlite3 to version control
- After installing new packages, update requirements.txt:
  pip freeze > requirements.txt