# KlaSim

KlaSim is a small Django application for uploading exam files and generating simulated student answers with the help of OpenAI.

## Installation

1. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
2. Install the requirements:
   ```bash
   pip install -r requirements.txt
   ```

## Environment variables

Set the following variables before starting the app (for example in your shell or in a `.env` file):

- `OPENAI_API_KEY` – required OpenAI API token used for text generation.
- `OPENAI_MODEL` – optional model name (default `gpt-4-1106-preview`).
- `SESSION_LIFETIME_DAYS` – how many days uploaded files are kept (default `7`).

## Running the development server

Run the initial migrations and start Django's development server:

```bash
python manage.py migrate
python manage.py runserver
```

Static files are served automatically in development. For production you should run `python manage.py collectstatic` and serve the generated files from the `static` directory.

### Deployment hints

A simple `Procfile` can be used for platforms like Heroku:

```
web: gunicorn KlaSim.wsgi
```

Use environment variables or a `.env` file to provide configuration. Remember to run `collectstatic` before deployment so your static files are available.

## Cleaning up old sessions

Uploaded files and generated results can fill up storage over time. Use the management command `clean_sessions` to remove old session data. The lifetime in days is configured via the `SESSION_LIFETIME_DAYS` setting (default is `7`).

Run the command manually:

```bash
python manage.py clean_sessions
```

### Automating via cron

On a Linux server you can schedule this cleanup daily using `cron`. Example crontab entry:

```
0 3 * * * /path/to/venv/bin/python /path/to/manage.py clean_sessions >> /var/log/klasim_clean.log 2>&1
```

Adjust the paths for your environment. Any task scheduler (e.g. systemd timers, Windows Task Scheduler) can call the same command.

