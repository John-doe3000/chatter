set shell := ["bash", "-c"]

venv-create:
	@echo "Creating Python virtual environment..."
	cd backend && python -m venv .venv
	@echo "Virtual environment created. Activate it with:"
	@echo "  Windows: backend\\.venv\\Scripts\\activate"
	@echo "  Unix/Mac: source backend/.venv/bin/activate"

venv-activate:
	@echo "Opening a shell with the backend virtual environment activated..."
	cd backend && if [[ ! -f .venv/bin/activate ]]; then echo "Virtual environment not found. Run: just venv-create"; exit 1; fi; source .venv/bin/activate && exec ${SHELL:-bash} -i

setup: venv-create
	@echo "Setting up development environment..."
	@echo "Then run: just install"

install:
	@echo "Installing dependencies..."
	cd backend && .venv/bin/python -m pip install -r requirements.txt

# Project maintenance
update-reqs:
	@echo "Updating requirements.txt..."
	cd backend && .venv/bin/python -m pip freeze > requirements.txt

# Backend Django development
backend-dev:
	@echo "Starting Django development server..."
	cd backend && .venv/bin/python manage.py runserver

backend-test:
	@echo "Running tests with pytest..."
	cd backend && .venv/bin/python -m pytest

backend-lint:
	@echo "Running backend lint checks..."
	cd backend && .venv/bin/python -m ruff check .

backend-lint-fix:
	@echo "Running backend lint checks..."
	cd backend && .venv/bin/python -m ruff check . --fix

backend-migrations:
	@echo "Applying database migrations..."
	cd backend && .venv/bin/python manage.py migrate

backend-superuser:
	@echo "Creating superuser..."
	cd backend && .venv/bin/python manage.py createsuperuser

backend-shell:
	@echo "Opening Django shell..."
	cd backend && .venv/bin/python manage.py shell

# Frontend (if applicable)
frontend-dev:
	@echo "Starting frontend development server..."
	npm start

frontend-build:
	@echo "Building frontend for production..."
	npm run build

clean:
	@echo "Cleaning up..."
	cd backend && find . -type f -name "*.pyc" -delete
	cd backend && find . -type d -name "__pycache__" -exec rm -rf {} +
	cd backend && find . -type f -name "*.pyo" -delete
	cd backend && find . -type f -name "*~" -delete
	cd backend && find . -type f -name ".coverage" -delete
	cd backend && find . -type d -name "*.egg-info" -exec rm -rf {} +
	cd backend && find . -type d -name ".pytest_cache" -exec rm -rf {} +
	cd backend && find . -type d -name ".coverage" -exec rm -rf {} +

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
