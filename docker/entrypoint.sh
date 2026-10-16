#!/bin/sh
set -e

mkdir -p /app/data

# First boot: load demo database (bookings, patients, admin user, reminders)
if [ ! -f "$SQLITE_PATH" ]; then
  if [ -f /app/seed/demo.sqlite3 ]; then
    echo "[SmileCare] Loading demo database with sample bookings..."
    cp /app/seed/demo.sqlite3 "$SQLITE_PATH"
  elif [ -f /app/db.sqlite3 ]; then
    echo "[SmileCare] Loading project database..."
    cp /app/db.sqlite3 "$SQLITE_PATH"
  fi
fi

python manage.py migrate --noinput

echo "[SmileCare] Starting on http://0.0.0.0:8000"
echo "[SmileCare] Admin: admin / SmileCare@2026"
echo "[SmileCare] Reports: /admin/reports/"

exec python manage.py runserver 0.0.0.0:8000
