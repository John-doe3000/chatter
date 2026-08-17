# Android frontend setup notes

## Current repo status

This repo is already aligned with the correct Android emulator pattern for local Windows development.

Relevant details in the project:

- `mobile/app/build.gradle.kts` reads `BASE_URL` from `mobile/local.properties` and defaults to `http://10.0.2.2:8000/`
- `mobile/app/src/main/AndroidManifest.xml` includes `android:usesCleartextTraffic="true"`
- `mobile/local.properties` already contains `BASE_URL=http://10.0.2.2:8000/`
- the app manifest also declares `INTERNET` permission

This means the repo already has the expected Android-side configuration for the emulator workflow.

## Backend requirements for local Android development

The backend should be run through Docker Desktop on Windows, and the Android emulator must reach the host machine rather than itself.

Important rules:

- Do not use `127.0.0.1` or `localhost` in Android code
- Use `10.0.2.2` for the Android emulator
- Expose the Django backend on host port `8000`
- Keep the service bound to `0.0.0.0` inside Docker
- Use `android:usesCleartextTraffic="true"` for local HTTP development

The repo already follows that pattern:

- `docker-compose.yml` exposes gunicorn on `8000:8000`
- `docker-compose.yml` exposes daphne on `8001:8001`
- the Django app listens on `0.0.0.0` inside Docker
- nginx is still mapped to `8080:80`, which is a separate host/browser reverse proxy and is not the Android emulator endpoint

## Why this is necessary

The Android emulator runs inside a virtual machine, so it has a special host alias:

- `10.0.2.2` = the Windows host machine from the emulator
- `localhost` = the emulator itself, not the PC

If the app calls `localhost`, it will fail even when the backend is running correctly.

## Recommended local workflow

On Windows:

1. Start Docker Desktop
2. From the project root, run `just docker-up`
3. Confirm the backend responds at `http://localhost:8000/health/` from the host machine
4. In Android Studio, run the app on the emulator
5. Keep the app configured to use `http://10.0.2.2:8000/` as the backend base URL

## Real device note

If the team uses a real Android device instead of the emulator, replace `10.0.2.2` with the host machine's LAN IP such as `192.168.x.x`, and ensure the Windows firewall allows the port.

## Practical takeaway

This is the correct dev setup for this repo:

- Windows 11 + Docker Desktop
- Django backend exposed at `localhost:8000` from the host
- Android emulator reaching `10.0.2.2:8000`
- local HTTP allowed in Android for development

This matches the same emulator-safe setup pattern described in the other project, and in this repo the Android configuration is already in place.
