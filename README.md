# Flask Chat App

This repository is a small Flask + Flask-SocketIO chat application.

## Local development

1. Create a virtualenv and activate it:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the app in debug mode:

```powershell
python debug_start.py
```

4. Visit `http://localhost:5000`.

## Deployment (Render)

Use the provided `render.yaml` or a Procfile. Recommended start command:

```text
web: gunicorn --worker-class eventlet -w 1 wsgi:app --bind 0.0.0.0:$PORT
```

Set these environment variables in Render:
- SECRET_KEY (generate a secure value)
- DATABASE_URL (Postgres recommended for production)
- REDIS_URL (optional) — required if you scale to multiple instances

If Render's build fails on eventlet, ensure your buildCommand installs setuptools/wheel first:

```yaml
buildCommand: pip install 'setuptools>=68.0.0' wheel && pip install -r requirements.txt
```

## Notes
- SQLite is fine for local dev or single-instance deploys, but use Postgres for production.
- When scaling to multiple instances, configure `REDIS_URL` and the Socket.IO `message_queue`.

If you want, I can add example `docker-compose` and a `Procfile` for Heroku-like setups.
