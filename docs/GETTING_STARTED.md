# Install and start School Day Grid

> Looking for the everyday overview and onboarding walkthrough? Go back to the [main README](../README.md).

This guide is for the person setting up the application on a computer or server. Once it is running, the first screen will guide you through creating a calendar.

## Recommended installation: Docker Desktop on Windows

For most people running School Day Grid on their own Windows computer, Docker Desktop is the easiest and recommended installation. It avoids installing and maintaining Python packages yourself, and it keeps the calendar data in the app folder.

Docker Desktop may use the Windows Subsystem for Linux (WSL 2) behind the scenes, but you do **not** need to open, use, or configure WSL yourself. Install Docker Desktop using its normal Windows installer, accept its recommended defaults, then use PowerShell for the steps below.

1. Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/).
2. Download or extract the School Day Grid folder.
3. Open PowerShell in that folder and run:

   ```powershell
   docker compose up -d --build
   ```

4. Open [http://localhost:8088](http://localhost:8088) and follow the setup wizard.

Your calendar is stored locally in the `data` folder. To stop the app later, run `docker compose down` from the same folder. Starting it again uses the same calendar data.

## Before you begin

You need one of the following:

- Docker Desktop (recommended for Windows and the simplest local setup); or
- Python 3.12 or newer, for a developer-style local installation.

You do not need Home Assistant, MQTT, or an external calendar account.

## Local installation

Open a terminal in the School Day Grid folder and use the instructions for your system.

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
python -m uvicorn product_app:app --reload --host 0.0.0.0 --port 8088
```

### macOS, Linux, or Windows Git Bash

```bash
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
# source .venv/Scripts/activate # Windows Git Bash
python -m pip install -e '.[dev]'
cp .env.example .env
python -m uvicorn product_app:app --reload --host 0.0.0.0 --port 8088
```

Then visit [http://localhost:8088](http://localhost:8088). The setup wizard opens automatically on a new installation.

## Docker installation

The Windows instructions above are the recommended Docker installation. On macOS or Linux, install Docker Desktop (or Docker Engine with the Compose plugin), then run the same command from the project folder:

From the project folder, run:

```bash
docker compose up -d --build
```

Open [http://localhost:8088](http://localhost:8088) when the container has started.

## Your first calendar

The wizard lets you either start with your own calendar or load a sample school year. The sample is a good no-pressure way to see the finished calendar before entering real dates. You can update the setup later from the calendar interface.

## Keep your calendar safe

The application stores its calendar locally. Use the backup option in the calendar interface to make a full backup, or export an individual calendar as JSON before moving computers or making major changes.

For production hosting, security settings and deployment details are in the [technical reference](TECHNICAL_REFERENCE.md).
