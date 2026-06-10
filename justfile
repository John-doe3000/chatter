set shell := ["bash", "-c"]

# Example task
hello:
    echo "No"

# Chatter Backend Tasks

# Install dependencies
install:
    cd backend && pip install -r requirements.txt

# Run all tests
test:
    cd backend && pytest -v

# Run tests with coverage
test-coverage:
    cd backend && pytest --cov=accounts --cov=groups --cov-report=html

# Run specific test file
test-file FILE:
    cd backend && pytest {{FILE}} -v

# Create migrations
makemigrations APP="":
    if [ -z "{{APP}}" ]; then \
        cd backend && python manage.py makemigrations; \
    else \
        cd backend && python manage.py makemigrations {{APP}}; \
    fi

# Apply migrations
migrate:
    cd backend && python manage.py migrate

# Start development server
runserver HOST="0.0.0.0" PORT="8000":
    cd backend && python manage.py runserver {{HOST}}:{{PORT}}

# Create superuser
createsuperuser:
    cd backend && python manage.py createsuperuser

# Shell
shell:
    cd backend && python manage.py shell

# Format code with black (if installed)
format:
    cd backend && black accounts groups

# Lint with flake8 (if installed)
lint:
    cd backend && flake8 accounts groups

# Clean up pycache and db
clean:
    find backend -type d -name __pycache__ -exec rm -rf {} +
    find backend -type f -name "*.pyc" -delete
    rm -f backend/db.sqlite3

# Help
help:
    @just --list