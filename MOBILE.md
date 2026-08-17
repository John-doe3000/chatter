# Instructions for Gemini

✅ Status of the setup

I checked the project and the Android-side configuration is already aligned with the emulator pattern:

- `build.gradle.kts` reads BASE_URL from local.properties and defaults to `http://10.0.2.2:8000/`
- `AndroidManifest.xml` already includes `android:usesCleartextTraffic="true"`
- local.properties already contains `BASE_URL=http://10.0.2.2:8000/`

So for the Android Emulator on Windows 11, the main requirement is already in place.

I also updated `docker-compose.yml` so the backend is published on host ports:

- gunicorn: `8000:8000`
- daphne: `8001:8001`

This is important because the emulator must reach the host machine, not the device itself.

Will the plan work?

Yes — for an Android Emulator on Windows, this is the correct pattern:

- Use 10.0.2.2 in Android code, not localhost
- Keep the backend bound to 0.0.0.0 inside Docker
- Expose the Django service on a host port like 8000
- Keep usesCleartextTraffic="true" for dev HTTP traffic

This should work for:

- Android Emulator on Windows 11
- Docker Desktop running the backend
- Local development against the app in Android Studio

Important note

The project's nginx reverse proxy is intentionally using 8080:80 because Docker rootless does not allow binding to privileged ports below 1024. That is separate from the emulator backend connection.

For the Android app, they should target the backend directly at `http://10.0.2.2:8000/` not `http://localhost:8080/` unless they are intentionally hitting nginx from the host browser.

What they still need to do

1. Start Docker Desktop on Windows
2. From the project root, run `just docker-up`

In Android Studio, run the app on the emulator

Confirm the backend is healthy at http://localhost:8000/health/` from the host machine.

If they use a real Android device instead of the emulator, they must replace 10.0.2.2 with their host machine's LAN IP (for example `192.168.x.x`) and ensure the Windows firewall allows the port.

This is the correct dev setup for their scenario, and I did not find any additional code changes required in the mobile app itself.
