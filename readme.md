# FinSight AI

A Flask personal-finance application under active development. The current
release includes the application factory, database migrations, secure account
registration, login/logout, CSRF protection, an authenticated dashboard, and
per-user expense, income, monthly budget tracking, reports, profile editing,
dashboard charts, and an AI Budget Advisor with an offline fallback.

## Local setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask --app app db upgrade
flask --app app run
```

Set a strong random `SECRET_KEY` in `.env` before starting the application.
Generate one with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

The AI Budget Advisor works without external services by using local finance
rules. To enable Gemini-generated advice, set `GEMINI_API_KEY` and optionally
`GEMINI_MODEL` in `.env`.

## Tests

```bash
python -m unittest discover -v
flask --app app db check
```
