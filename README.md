# KlaSim

This project is a simple Django application for uploading exam files and generating simulated answers. 

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
