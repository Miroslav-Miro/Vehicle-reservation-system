# Vehicle Reservation System

A full‑stack vehicle reservation system with a Django backend (Django REST Framework, JWT auth, Channels websockets, Celery) and an Angular frontend. Local development runs via Docker Compose with PostgreSQL, Redis, and pgAdmin.

## Repository Layout

- `project_vrs/docker-compose.yml` – Local dev orchestration for backend, frontend, Postgres, Redis, pgAdmin, Celery worker.
- `project_vrs/.env.example` – Example environment variables. Copy to `.env` and adjust.
- `project_vrs/app/` – Application sources (backend + frontend).
  - `backend/` – Django project (settings, urls, ASGI/WSGI, Celery).
  - `api/` – Main API app (models, views, serializers, permissions, websocket consumers).
  - `frontend/` – Angular app served on port 4200 in dev.
  - `Dockerfile.backend` / `Dockerfile.frontend` – Images for backend and frontend.
  - `entrypoint.sh` – Backend container entrypoint: wait for DB, migrate, collectstatic, start ASGI (Daphne).
  - `manage.py` – Django management CLI.

## Backend Files (What’s What)

- `project_vrs/app/backend/settings.py`
  - Django configuration: DEBUG, ALLOWED_HOSTS, database (`SQL_*`), CORS/CSRF, DRF, JWT, Channels (Redis), Celery, email backend, static files.
- `project_vrs/app/backend/urls.py`
  - Root URLs: `admin/`, `api/` include, JWT endpoints (`api/auth/login`, `api/auth/refresh`), and API docs (`/swagger/`, `/redoc/`).
- `project_vrs/app/backend/asgi.py`
  - ASGI entrypoint. Routes HTTP to Django and websockets to Channels using custom token auth middleware. Loads `api.routing.websocket_urlpatterns`.
- `project_vrs/app/backend/wsgi.py`
  - WSGI entrypoint for traditional servers (not used in ASGI/websocket flow).
- `project_vrs/app/backend/celery.py`
  - Celery application bootstrap. Loads settings via `CELERY_*` and autodiscovers tasks.
- `project_vrs/app/entrypoint.sh`
  - Container startup: optionally wait for Postgres, run `migrate`, `collectstatic`, then launch Daphne (`backend.asgi:application`) on `:8000`.

## API App Files (What’s What)

Core app: `project_vrs/app/api`

- Core
  - `models.py` – Database models: `User` (custom auth), `Role`, `Brand`, `Model`, `EngineType`, `VehicleType`, `Vehicle`, `Location`, `PhysicalVehicle`, `ReservationStatus`, `Reservation`, `Notification`, and audit models.
  - `urls.py` – API routes with DRF router: vehicles, users, reservations, filtering endpoints, notifications, admin ops, registration, mock payment validation.
  - `views/*.py` – ViewSets/Views for each domain area:
    - `login_view.py` – JWT login (custom serializer).
    - `registration_view.py` – User registration.
    - `vehicle_view.py`, `public_vehicle_view.py`, `availability_view.py` – Vehicles and public availability.
    - `reservation_view.py` – Reservation CRUD and transitions.
    - `user_view.py`, `admin_ops_view.py`, `role_view.py` – Profiles, KPIs, roles.
    - `payment_view.py` – Mock card validation endpoint for dev/testing.
    - `notification_view.py` – Notification listing/mark-as-read.
  - `serializers/*.py` – DRF serializers for request/response shapes (users, roles, vehicles, reservations, payments, notifications, etc.).
  - `migrations/` – Schema and seed data migrations (initial roles/statuses, etc.).

- Auth, permissions, middleware
  - `custom_permissions/*.py` – Role-based access controls for admin/manager/user.
  - `middleware/token_auth.py` – Channels middleware that authenticates websockets using JWT from `?token=` and exposes `scope["user"]` and `scope["user_role"]`.

- Realtime (websockets)
  - `consumers.py` – `NotificationConsumer` subscribes users and role groups; receives group messages and pushes to clients.
  - `routing.py` – Websocket route patterns (e.g., `^ws/notifications/?$`).
  - `utils/broadcast.py` – Helper to persist `Notification` rows and broadcast via Channels groups on transaction commit.

- Other
  - `constants.py` – Shared status names and allowed transitions used across the API.
  - `email_sender/tasks.py` – Celery tasks for email notifications.

## Frontend

- `project_vrs/app/frontend/` – Angular application. In dev, served by `ng serve` on `http://localhost:4200/` and configured to call the backend on `http://localhost:8000/`.
- if running locally change the public/env.js varialbes to `http://localhost:8000/` and localhost:8000

## Running Locally (Docker Compose)

Prerequisites:
- Docker Desktop (or Docker Engine) and Docker Compose.

Steps:
1) Copy the example env file and fill in values:
   - From the repo root:
     - `cd project_vrs`
     - Copy: `.env.example` → `.env`
2) Set minimum variables in `project_vrs/.env` (example dev values):

```
# pgAdmin
PGADMIN_DEFAULT_EMAIL=admin@example.com
PGADMIN_DEFAULT_PASSWORD=admin

# Django
SECRET_KEY=change_me_to_random_long_string
DEBUG=1

# Database (match docker-compose service names)
SQL_ENGINE=django.db.backends.postgresql
SQL_DATABASE=vrs
SQL_USER=vrs
SQL_PASSWORD=vrs
SQL_HOST=db
SQL_PORT=5432
DATABASE=postgres

# Optional: CORS/CSRF for Angular dev
CORS_ALLOWED_ORIGINS=http://localhost:4200
CSRF_TRUSTED_ORIGINS=http://localhost:4200

# Redis/Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=django-db
```

3) Build and start all services:

```
cd project_vrs
docker-compose up --build
```

The backend container will run migrations and collect static files on startup.

## Service Endpoints

- Backend API: `http://localhost:8000/`
  - Swagger UI: `http://localhost:8000/swagger/`
  - ReDoc: `http://localhost:8000/redoc/`
  - JWT login: `POST http://localhost:8000/api/auth/login/` (returns access/refresh)
  - JWT refresh: `POST http://localhost:8000/api/auth/refresh/`
- Frontend (Angular): `http://localhost:4200/`
- pgAdmin: `http://localhost:5050/` (login with `PGADMIN_DEFAULT_*`)
- Postgres: `localhost:5432` (service name `db` inside Compose network)
- Redis: `localhost:6379` (service name `redis` inside Compose network)

## Websocket Notifications

- URL: `ws://localhost:8000/ws/notifications/?token=<JWT_ACCESS_TOKEN>`
- Auth: pass the JWT access token via `token` query param (middleware validates and adds user/role to appropriate channels).

## Notes & Tips

- Run inside `project_vrs/` because `docker-compose.yml` lives there.
- The backend image entrypoint runs Daphne (ASGI) to support websockets; the compose `command` is not used.
- If Celery logs an error about a missing broker, ensure `CELERY_BROKER_URL=redis://redis:6379/0` is set in `.env`.
- To create a Django superuser from inside the backend container:
  - `docker compose exec backend python manage.py createsuperuser`


