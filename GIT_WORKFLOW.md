# Deployment

Source branch main; origin is GitHub source storage, vps is the home bare mirror. GitHub Pages is disabled. Production source is /opt/rex-status and Nginx serves /var/www/rex-status.

Commit and push reviewed source, transfer only changed source files to /opt/rex-status, then run rex-status-refresh.service and verify strict HTTPS. Never deploy credentials or alter live application data. Timer rex-status-refresh.timer performs later refreshes autonomously.
