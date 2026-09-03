# Install and start School Day Grid

> Looking for the everyday overview and onboarding walkthrough? Go back to the [main README](../README.md).

This guide is for the person setting up the application on a computer or server. Once it is running, the first screen will guide you through creating a calendar.

## Before you begin

You need one of the following:

- Python 3.12 or newer, for a local installation; or
- Docker Desktop, for a container-based installation.

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
