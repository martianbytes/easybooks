# 📚 EasyBooks

A peer-to-peer marketplace for buying and selling used books, built with Django. Users can list books, browse by genre, chat with sellers, pay via eSewa, and manage orders — all in one place.

---

## Features

- Browse, search, and filter books by genre, category, and condition
- List your own books for sale with multi-image uploads
- Shopping cart and direct checkout
- eSewa payment integration
- Real-time messaging between buyers and sellers
- Order tracking
- User profiles with avatars
- Email verification on signup
- Newsletter subscription

---

## Prerequisites

Make sure you have these installed before starting:

- [Python 3.10+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/)
- pip (comes with Python)


## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/easybooks.git
cd easybooks
```

### 2. Create a virtual environment

**Windows:**
```bash
python -m venv .venv
```

**Mac / Linux:**
```bash
python3 -m venv .venv
```

### 3. Activate the virtual environment

**Windows:**
```bash
.venv\Scripts\activate
```

**Mac / Linux:**
```bash
source .venv/bin/activate
```

You should see `(.venv)` appear at the start of your terminal line. Run this every time you open a new terminal to work on the project.


### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run database migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create a superuser (admin account)

```bash
python manage.py createsuperuser
```

Follow the prompts to set a username, email, and password.


### 7. Run the development server

```bash
python manage.py runserver
```

Open your browser and go to: **http://127.0.0.1:8000**


## Useful Commands

| `python manage.py runserver` | Start the dev server |
| `python manage.py makemigrations` | Generate migration files after model changes |
| `python manage.py migrate` | Apply migrations to the database |
| `python manage.py createsuperuser` | Create an admin user |


## Deactivating the Virtual Environment

```bash
deactivate
```

## License

This project was built for educational purposes. All rights reserved © 2026 EasyBooks.