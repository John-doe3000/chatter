# Chatter — Step-by-Step Build Guide (with Gemini)

This guide walks a new developer through building **Chatter** end-to-end using **Gemini** (e.g. Gemini Code Assist in your IDE, or the Gemini CLI/web app) as a pair-programmer. It assumes you have already read [IMPLEMENTATION_OVERVIEW.md](IMPLEMENTATION_OVERVIEW.md) for the high-level design and [notes.md](notes.md) for context.

> **How to use this guide.** Each step has:
> - **Goal** — what you should have at the end of the step.
> - **Prompt to Gemini** — copy/paste this into Gemini, then iterate.
> - **Verify** — how to confirm the step works before moving on.
>
> Always read what Gemini produces before applying it. Run tests after every step.

## 0. Prerequisites

Install once on your machine:

- Python 3.11+ and `pip`
- Android Studio (Hedgehog or newer), Android SDK with API 24+
- Git
- Docker + Docker Compose (optional, for the dual-server setup)
- A Gemini interface — e.g. Gemini Code Assist in VS Code / Android Studio, or the Gemini web app

Clone the repo and create a working branch:

```bash
git clone <repo-url> chatter
cd chatter
git checkout -b feat/initial-build
```

## Working Effectively With Gemini

Use these habits at every step:

1. **Anchor Gemini to the plan.** Start each new chat with: *"Read `docs/IMPLEMENTATION_OVERVIEW.md` in this repo. We are now on Step N."*
2. **Ask for one file at a time** when generating code; review and commit before moving on.
3. **Always ask for tests** alongside code: *"Also generate pytest / JUnit tests covering …"*.
4. **Reject and refine.** If output drifts from the plan (wrong DB, websockets, etc.), reply: *"Stick to SQLite and 30-second polling. Regenerate."*
5. **Commit small.** One logical step = one commit. This makes it easy to revert if Gemini hallucinates.

---

# Part A — Backend (Django + DRF)

## Step A1. Bootstrap the Django project

**Goal:** `backend/` contains a runnable Django project named `chatter` with DRF and authtoken installed.

**Prompt to Gemini:**
> Generate the commands and file contents to bootstrap a Django 5 project in `backend/` named `chatter`, using a virtualenv and `requirements.txt`. Include `djangorestframework`, `djangorestframework-authtoken`, `gunicorn`, `daphne`, and `pytest-django`. Configure `INSTALLED_APPS`, `REST_FRAMEWORK` defaults (TokenAuthentication, IsAuthenticated), and SQLite. Show me the final `settings.py`, `requirements.txt`, and the exact terminal commands.

**Verify:**

```bash
cd backend
source .venv/bin/activate
python manage.py migrate
python manage.py runserver
# Visit http://127.0.0.1:8000/admin/ — Django admin login should load.
```

Commit: `chore(backend): bootstrap django project`.

## Step A2. `accounts` app — custom user and token auth

**Goal:** Users can register, log in, log out, and fetch their profile.

**Prompt to Gemini:**
> In the `backend/` Django project, create an `accounts` app with a custom `User` model extending `AbstractUser`. Add DRF endpoints `POST /api/auth/register/`, `POST /api/auth/login/` (returns token), `POST /api/auth/logout/`, and `GET /api/users/me/`. Use `djangorestframework-authtoken`. Wire the custom user with `AUTH_USER_MODEL`. Generate serializers, views, urls, and pytest-django tests for each endpoint.

**Verify:**

```bash
pytest accounts -q
# Manual: register a user and hit /api/users/me/ with Authorization: Token <token>.
```

Commit: `feat(accounts): custom user + token auth`.

## Step A3. `groups` app — models and personal-group signal

**Goal:** Models for `Group`, `Membership`, `Invitation`, `Ban`, and a signal that creates a personal group on user creation.

**Prompt to Gemini:**
> Create a `groups` Django app with models:
> - `Group(name, owner, created_at)`
> - `Membership(user, group, role)` where `role` is one of `member`, `admin`, `head_admin` (use `TextChoices`)
> - `Invitation(group, invited_user, invited_by, status, created_at)`
> - `Ban(group, user, banned_by, created_at)`
>
> Add a `post_save` signal on the user model so that when a new user is created, a personal `Group` is created and the user is added as `head_admin`. Include migrations and tests proving the signal fires.

**Verify:**

```bash
python manage.py makemigrations && python manage.py migrate
pytest groups -q
```

Commit: `feat(groups): models + personal-group signal`.

## Step A4. `groups` app — permissions, invites, kick, promote

**Goal:** Endpoints to manage group membership with proper permissions.

**Prompt to Gemini:**
> Add to the `groups` app the DRF endpoints described in `docs/IMPLEMENTATION_OVERVIEW.md` section 4.4 for groups, invitations, kick, and promote. Implement permission classes `IsGroupMember`, `IsGroupAdmin`, `IsGroupHeadAdmin`. A user that is `banned` from a group must not be able to be invited again. Generate tests covering each permission boundary (member tries admin action → 403, admin tries head-admin action → 403, head admin succeeds).

**Verify:**

```bash
pytest groups -q
```

Commit: `feat(groups): membership management endpoints`.

## Step A5. Head-admin ban flow

**Goal:** Head admins can permanently ban a member; banned users cannot rejoin.

**Prompt to Gemini:**
> Implement `POST /api/groups/{id}/members/{user}/ban/` restricted to `IsGroupHeadAdmin`. Banning must remove the membership and create a `Ban` record. Update the invitation flow to refuse invites for users who have an active `Ban` for the group. Add tests for: head admin bans member (success), admin tries to ban (403), banned user re-invited (400).

**Verify:** `pytest groups -q`. Commit: `feat(groups): head-admin ban flow`.

## Step A6. `messaging` app — text messages with `since` polling

**Goal:** Endpoints to send and poll text messages.

**Prompt to Gemini:**
> Create a `messaging` Django app with:
> - `Message(group, sender, body, created_at)`
> - `Attachment(message, file, kind)` where `kind` is `image|video|voice`
>
> Add endpoints:
> - `GET /api/groups/{id}/messages/?since=<iso8601>` — returns messages newer than `since`, ordered by `created_at`, paginated cursor-style.
> - `POST /api/groups/{id}/messages/` — multipart, accepts optional `body` and optional `attachment` + `kind`.
>
> Restrict both to `IsGroupMember`. Generate tests for sending text and polling with `since`.

**Verify:** `pytest messaging -q`. Commit: `feat(messaging): text messages and polling`.

## Step A7. Media attachments (image, video, voice)

**Goal:** Validated upload of images, videos, and voice notes.

**Prompt to Gemini:**
> Extend the `Attachment` flow to validate MIME type and size per `kind`:
> - `image`: `image/jpeg`, `image/png`, max 10 MB
> - `video`: `video/mp4`, max 50 MB
> - `voice`: `audio/aac`, `audio/mp4`, `audio/mpeg`, max 10 MB
>
> Configure `MEDIA_ROOT`, serve `/media/` only to authenticated users that are members of the message's group. Add tests for each kind, oversize rejection, and unauthorized access.

**Verify:** `pytest messaging -q`. Commit: `feat(messaging): media attachments`.

## Step A8. Dual server: gunicorn (WSGI) + daphne (ASGI)

**Goal:** Both servers run; `docker compose up` works.

**Prompt to Gemini:**
> Generate a `Dockerfile` for the backend, a root `docker-compose.yml` that runs gunicorn (`chatter.wsgi:application`) and daphne (`chatter.asgi:application`) as separate services with a shared volume for SQLite and `MEDIA_ROOT`, plus an nginx service that reverse-proxies them and serves `/media/`. Include a healthcheck on both.

**Verify:**

```bash
docker compose up --build
curl -s http://localhost:8000/api/users/me/ -H "Authorization: Token <t>"
```

Commit: `chore(backend): gunicorn + daphne via docker compose`.

## Step A9. Backend CI

**Goal:** GitHub Actions runs tests on every PR.

**Prompt to Gemini:**
> Generate `.github/workflows/backend.yml` that sets up Python 3.11, caches pip, installs `backend/requirements.txt`, runs `pytest` and Django's `check`. Trigger on pushes and PRs that touch `backend/**`.

Commit: `ci(backend): pytest on PR`.

---

# Part B — Android Client (Kotlin)

Run the backend locally before starting Part B so you can hit it from the emulator at `http://10.0.2.2:8000/`.

## Step B1. Bootstrap the Android project

**Goal:** A Kotlin Android project in `mobile/` with min SDK 24, Hilt, Retrofit, OkHttp, Moshi, Coroutines, Coil, Media3, and Room set up.

**Prompt to Gemini:**
> Generate an Android Studio project at `mobile/` (Kotlin, min SDK 24, target SDK latest, Gradle Kotlin DSL). Add dependencies: Hilt, Retrofit + OkHttp + Moshi converter, Coroutines, Coil, Media3 ExoPlayer, Room, WorkManager. Show me `app/build.gradle.kts`, root `build.gradle.kts`, and a Hilt `Application` class. Also configure `BASE_URL` to be read from `local.properties` and exposed via `BuildConfig`.

**Verify:** Project builds in Android Studio (`./gradlew :app:assembleDebug`). Commit: `chore(mobile): bootstrap android project`.

## Step B2. API layer

**Goal:** Retrofit services, models, and an auth interceptor matching the backend.

**Prompt to Gemini:**
> Generate Retrofit interfaces in `data/api/` matching the API in `docs/IMPLEMENTATION_OVERVIEW.md` section 4.4 (auth, groups, invitations, members, messages). Generate Moshi data classes for requests and responses. Add an OkHttp `AuthInterceptor` that injects `Authorization: Token <token>` from a `TokenStore` backed by `EncryptedSharedPreferences`. Provide everything via Hilt modules.

**Verify:** Unit-test the interceptor with a `MockWebServer`. Commit: `feat(mobile): retrofit + auth`.

## Step B3. Auth screens

**Goal:** Register, log in, and a "logged in" landing screen.

**Prompt to Gemini:**
> Build Compose screens for register and login under `ui/auth/`. Use a `ViewModel` with `StateFlow`. On successful login, save the token via `TokenStore` and navigate to a placeholder "Groups" screen. Include input validation and error display.

**Verify:** Manual run on emulator against the local backend. Commit: `feat(mobile): auth screens`.

## Step B4. Groups list & detail

**Goal:** Display the groups the user belongs to and members of a selected group.

**Prompt to Gemini:**
> Build `ui/groups/` Compose screens: a `GroupsScreen` listing the user's groups and a `GroupDetailScreen` showing members and roles. Wire repositories that hit `/api/groups/` and `/api/groups/{id}/`. Cache results in Room so the list works offline.

**Verify:** Groups appear; pulling to refresh fetches new data. Commit: `feat(mobile): groups list + detail`.

## Step B5. Chat screen + 30-second polling

**Goal:** Open a group, see its messages, and have new messages appear within 30 s.

**Prompt to Gemini:**
> Build `ui/chat/ChatScreen` showing messages bottom-up. The `ChatViewModel` should:
> - On open, call `GET /api/groups/{id}/messages/?since=<lastSeen>` and store messages in Room.
> - Start a coroutine that re-polls every 30 seconds while the screen is in the foreground.
> - Persist `lastSeen` per group so polling resumes correctly after process death.
>
> Implement `POST /api/groups/{id}/messages/` for sending text. Add unit tests for the polling logic using a fake clock.

**Verify:** Send a message from the Django admin or curl; it appears within 30 s. Commit: `feat(mobile): chat + 30s polling`.

## Step B6. Image attachments

**Goal:** Send and view images in chat.

**Prompt to Gemini:**
> Add image sending: a "+" button opens a chooser between camera and gallery. Compress to JPEG at max 1920px long edge, then upload via multipart with `kind=image`. Render image attachments inline using Coil with a tap-to-zoom dialog.

Commit: `feat(mobile): image attachments`.

## Step B7. Video attachments

**Goal:** Record/select and play back videos.

**Prompt to Gemini:**
> Add video sending: capture or pick an MP4 (cap at 30 s). Upload via multipart with `kind=video`. Render video attachments inline with a Media3 ExoPlayer using a thumbnail until tapped.

Commit: `feat(mobile): video attachments`.

## Step B8. Voice messages

**Goal:** Hold-to-record voice notes, preview, send, and play back.

**Prompt to Gemini:**
> Add voice messages: a hold-to-record button uses `MediaRecorder` to produce AAC/M4A. Show a preview with play/discard/send. Upload with `kind=voice`. In the chat list, render a compact playback row with a waveform placeholder, duration, and a play/pause button.

Commit: `feat(mobile): voice messages`.

## Step B9. Admin actions UI

**Goal:** Admins and head admins see actions appropriate to their role.

**Prompt to Gemini:**
> In `GroupDetailScreen`, show invite/kick/promote buttons for admins and an additional ban button for head admins. Wire each to the corresponding endpoint. Refresh membership after every action. Hide actions for the current user's own row.

Commit: `feat(mobile): admin actions`.

## Step B10. Background polling and notifications

**Goal:** Users get a local notification for new messages while the app is backgrounded.

**Prompt to Gemini:**
> Add a `WorkManager` `PeriodicWorkRequest` (15-minute interval — Android's minimum) that polls each group's messages endpoint with the saved `lastSeen` and posts a local notification per group with new messages. Tapping a notification deep-links into the matching `ChatScreen`.

Commit: `feat(mobile): background polling + notifications`.

## Step B11. Mobile CI

**Prompt to Gemini:**
> Generate `.github/workflows/mobile.yml` that sets up JDK 17, caches Gradle, runs `./gradlew :app:lintDebug :app:testDebugUnitTest :app:assembleDebug`. Trigger on pushes and PRs that touch `mobile/**`.

Commit: `ci(mobile): lint + tests on PR`.

---

# Part C — Putting it Together

## Step C1. End-to-end smoke test

Run `docker compose up` for the backend and the app on an emulator. Verify:

1. Register two users (A and B).
2. A creates a group and invites B.
3. B accepts; both see the group.
4. A sends text, image, video, and voice; both see them within 30 seconds.
5. A promotes B to admin. B invites a third user C.
6. A (head admin) bans C. C can no longer be invited.

If any step fails, paste the failing log into Gemini with the relevant file open and ask for a fix — but always re-read [IMPLEMENTATION_OVERVIEW.md](IMPLEMENTATION_OVERVIEW.md) first so the fix matches the design.

## Step C2. Open a pull request

```bash
git push -u origin feat/initial-build
```

Open a PR into `main`. CI must pass on both `backend.yml` and `mobile.yml` before merging.

---

# Troubleshooting Tips

- **Gemini suggests websockets / Channels.** Reject — the design uses 30-second polling.
- **Gemini suggests Postgres / MySQL.** Reject — v1 uses SQLite.
- **Emulator can't reach backend.** Use `http://10.0.2.2:8000/`, not `localhost`.
- **`401 Unauthorized` on every call.** Check that the `AuthInterceptor` is reading a freshly stored token and that the header is `Token <…>`, not `Bearer`.
- **Media file 403 in the app.** Confirm the authenticated `/media/` view checks the requesting user's group membership.
