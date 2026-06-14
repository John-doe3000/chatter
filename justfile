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

# Run all tests (local + docker)
test-all:
    cd backend && pytest -v
    docker compose exec gunicorn pytest -v

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

# Start development environment (Docker with hot-reload)
dev:
    docker compose up

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

# Docker Compose Tasks

# Build Docker images
docker-build:
    docker compose build

# Build Docker images without cache
docker-build-nocache:
    docker compose build --no-cache

# Start all services in background
docker-up:
    docker compose up -d

# Start all services in foreground (for development)
docker-up-fg:
    docker compose up

# Stop and remove containers
docker-down:
    docker compose down

# Stop and remove containers with volumes
docker-down-volumes:
    docker compose down -v

# View logs for all services
docker-logs:
    docker compose logs -f

# View logs for specific service
docker-logs-service SERVICE:
    docker compose logs -f {{SERVICE}}

# Restart services
docker-restart:
    docker compose restart

# Run Django management command in gunicorn container
docker-manage CMD:
    docker compose exec gunicorn python manage.py {{CMD}}

# Run Django migrations
docker-migrate:
    docker compose exec gunicorn python manage.py migrate

# Create superuser
docker-createsuperuser:
    docker compose exec gunicorn python manage.py createsuperuser

# Collect static files
docker-collectstatic:
    docker compose exec gunicorn python manage.py collectstatic --noinput

# Open shell in gunicorn container
docker-shell:
    docker compose exec gunicorn bash

# Run tests in container
docker-test:
    docker compose exec gunicorn pytest -v

# Health check status
docker-health:
    docker compose ps

# Help
help:
    @just --list
