# Chatter — Implementation Plan

This document describes the implementation plan for **Chatter**, a private group-messaging application consisting of a Django REST Framework (DRF) backend and a native Android client. The repository is organized as a monorepo with the backend in `/backend` and the Android app in `/mobile`.

## 1. Goals & Scope

Build a messaging platform that supports:

- Private 1:1 text messaging between users.
- Group messaging with role-based permissions.
- Automatic provisioning of a personal group for every new user (user is admin of their own group).
- User-created groups, with the creator automatically becoming **head admin**.
- Group membership management: admins can invite and kick members.
- Two-tier admin hierarchy:
  - **Admin** — can invite, kick, and promote other members to admin.
  - **Head admin** — has all admin powers plus the ability to **permanently ban** users from a group.
- Rich media messages: images, videos, and voice notes.
- Message delivery via **polling on a 30-second interval** (no websockets in v1).

## 2. Architecture Overview

```
┌──────────────────────┐         HTTPS / JSON         ┌──────────────────────────┐
│  Android client      │  ───── REST (Retrofit) ────▶ │  Django + DRF backend    │
│  (/mobile)           │  ◀──── 30s polling ───────── │  (/backend)              │
│                      │                              │  • WSGI: gunicorn        │
│  Kotlin + Retrofit   │                              │  • ASGI: daphne          │
│  ExoPlayer / Media3  │                              │  • SQLite database       │
└──────────────────────┘                              │  • Local media storage   │
                                                      └──────────────────────────┘
```

- **Backend** runs both a **WSGI** server (gunicorn) for standard HTTP request/response traffic and an **ASGI** server (daphne) for any async-capable endpoints and future real-time extensions.
- **Database**: SQLite (single file, suitable for v1 scale).
- **Transport**: REST/JSON over HTTPS. Clients poll the messages endpoint every 30 seconds.
- **Media**: uploaded to the backend and stored on the server filesystem under Django's `MEDIA_ROOT`; served via authenticated URLs.

## 3. Repository Layout

```
chatter/
├── backend/              # Django + DRF project
│   ├── manage.py
│   ├── chatter/          # Django project (settings, urls, wsgi, asgi)
│   ├── accounts/         # User model & auth
│   ├── groups/           # Groups, memberships, roles, bans
│   ├── messaging/        # Messages and media attachments
│   ├── requirements.txt
│   └── Dockerfile
├── mobile/               # Android Studio project (Kotlin)
│   ├── app/
│   └── build.gradle(.kts)
├── docs/
│   ├── IMPLEMENTATION.md
│   └── notes.md
├── docker-compose.yml    # Orchestrates gunicorn + daphne
└── README.md
```

## 4. Backend Implementation (`/backend`)

### 4.1 Tech Stack

| Concern              | Choice                                |
| -------------------- | ------------------------------------- |
| Framework            | Django 5.x + Django REST Framework    |
| Auth                 | Token authentication (DRF authtoken)  |
| Database             | SQLite                                |
| WSGI server          | gunicorn                              |
| ASGI server          | daphne                                |
| Media handling       | Django `FileField` / `ImageField`     |
| Dependency mgmt      | pip + `requirements.txt`              |

### 4.2 Django Apps

1. **accounts**
   - Custom `User` model (extends `AbstractUser`).
   - Registration, login, logout, token issuance.
   - Signal on user creation → auto-create personal group with the user as head admin.

2. **groups**
   - Models: `Group`, `Membership`, `Invitation`, `Ban`.
   - `Membership.role` ∈ { `member`, `admin`, `head_admin` }.
   - Endpoints: list/create groups, invite, accept/decline invite, kick, promote, ban (head admin only), leave.
   - Permission classes:
     - `IsGroupMember` — read messages and member list.
     - `IsGroupAdmin` — invite, kick, promote.
     - `IsGroupHeadAdmin` — permanently ban.

3. **messaging**
   - Models: `Message`, `Attachment` (type ∈ { `image`, `video`, `voice` }).
   - Endpoints:
     - `GET /api/groups/{id}/messages/?since=<iso8601>` — used by 30s polling.
     - `POST /api/groups/{id}/messages/` — multipart for text + optional attachment.
   - Pagination: cursor on `created_at` to make polling efficient.

### 4.3 Data Model (high-level)

```
User (1) ───< Membership >─── (N) Group
Group (1) ───< Message
Message (1) ───< Attachment
Group (1) ───< Invitation
Group (1) ───< Ban >── User
```

### 4.4 REST API Surface (v1)

| Method | Path                                       | Purpose                          |
| ------ | ------------------------------------------ | -------------------------------- |
| POST   | `/api/auth/register/` | Create account                   |
| POST   | `/api/auth/login/`                         | Obtain token                     |
| POST   | `/api/auth/logout/`                        | Revoke token                     |
| GET    | `/api/users/me/`                           | Current user                     |
| GET    | `/api/groups/`                             | Groups the user belongs to       |
| POST   | `/api/groups/`                             | Create group (creator = head admin) |
| GET    | `/api/groups/{id}/`                        | Group detail + members           |
| POST   | `/api/groups/{id}/invitations/`            | Invite a user (admin+)           |
| POST   | `/api/invitations/{id}/accept/`            | Accept invite                    |
| POST   | `/api/groups/{id}/members/{user}/kick/`    | Kick member (admin+)             |
| POST   | `/api/groups/{id}/members/{user}/promote/` | Promote to admin (admin+)        |
| POST   | `/api/groups/{id}/members/{user}/ban/`     | Permanently ban (head admin)     |
| GET    | `/api/groups/{id}/messages/?since=`        | Poll messages                    |
| POST   | `/api/groups/{id}/messages/`               | Send message (multipart)         |

### 4.5 Serving Stack

- `gunicorn chatter.wsgi:application` for synchronous request handling.
- `daphne chatter.asgi:application` for ASGI-capable endpoints.
- A reverse proxy (nginx in production) routes between the two and serves `/media/`.

### 4.6 Milestones

1. Project bootstrap, custom `User`, token auth.
2. `groups` app with roles, invitations, kick, promote.
3. Head-admin ban flow.
4. `messaging` app with text messages and `since` polling.
5. Attachments (image, video, voice) with size/MIME validation.
6. Dual-server config (gunicorn + daphne) and Docker Compose.
7. Test suite (pytest-django) and CI.

## 5. Android Client Implementation (`/mobile`)

### 5.1 Tech Stack

| Concern              | Choice                                |
| -------------------- | ------------------------------------- |
| Language             | Kotlin                                |
| Min SDK              | 24 (Android 7.0)                      |
| Networking           | Retrofit + OkHttp + Moshi             |
| Image loading        | Coil                                  |
| Video playback       | Media3 / ExoPlayer                    |
| Audio capture        | `MediaRecorder`                       |
| Async                | Kotlin Coroutines + Flow              |
| Polling scheduler    | `WorkManager` + in-foreground coroutine timer |
| DI                   | Hilt                                  |
| Local cache          | Room                                  |

### 5.2 Module Structure

```
mobile/app/src/main/java/com/chatter/
├── data/
│   ├── api/           # Retrofit interfaces
│   ├── db/            # Room entities and DAOs
│   └── repo/          # Repositories
├── domain/            # Use cases, models
├── ui/
│   ├── auth/
│   ├── groups/
│   ├── chat/
│   └── media/
└── di/                # Hilt modules
```

### 5.3 Polling Strategy

- While a chat screen is open: a coroutine timer calls `GET /messages/?since=<lastSeen>` every 30 seconds.
- In the background: a `PeriodicWorkRequest` (15 min minimum, Android limitation) refreshes message lists and shows local notifications.
- Persist `lastSeen` per group in Room so polling resumes exactly where it left off.

### 5.4 Media Capture & Upload

- **Images**: system camera intent or gallery picker → compressed to JPEG.
- **Videos**: system camera intent capped at a configurable duration; uploaded as MP4.
- **Voice**: in-app recorder using `MediaRecorder` (AAC/M4A); preview before send.
- All uploads are multipart `POST /messages/` with the binary in `attachment` and `kind` field.

### 5.5 Milestones

1. Project skeleton, Hilt, Retrofit base, auth screens.
2. Group list + group detail screens.
3. Chat screen with text-only messages and 30s polling.
4. Image attachments.
5. Video attachments.
6. Voice messages.
7. Admin actions UI (invite, kick, promote, ban).
8. Background polling + notifications.

## 6. Cross-Cutting Concerns

- **Authentication**: DRF token in `Authorization: Token <…>` header on every request.
- **Authorization**: enforced server-side via DRF permission classes; client UI only hides admin actions for non-admins as a UX nicety.
- **Validation**: file size and MIME type checks both client- and server-side.
- **Error handling**: standard problem-style JSON responses (`{ "detail": "..." }`).
- **Testing**:
  - Backend: pytest-django, factory-boy, coverage on permissions and ban flow.
  - Android: JUnit + Turbine for Flow, Espresso for critical screens.
- **CI**: GitHub Actions running backend tests, Android `assembleDebug`, and lint on every PR.
- **Branching**: trunk-based development, PR reviews required before merge to `main`.

## 7. Local Development

- Backend: `python -m venv .venv && pip install -r requirements.txt && python manage.py migrate && python manage.py runserver`.
- Dual-server (closer to prod): `docker compose up` runs gunicorn and daphne behind a single proxy.
- Android: open `/mobile` in Android Studio, set `BASE_URL` in `local.properties` to the backend address (`http://10.0.2.2:8000/` for the emulator).

## 8. Out of Scope (v1)

- Real-time push (websockets, FCM) — polling only.
- End-to-end encryption.
- iOS client.
- Horizontal scaling / non-SQLite databases.
