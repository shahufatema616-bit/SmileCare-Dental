# SmileCare Dental booking system

Web app for a dental clinic appointment booking and reminder system (student project).

**Developer:** Fatemazahera Mahammadhasam Shahu (1216169)  
**Course:** SCI701 Research/Industry Dissertation 2  
**Supervisor:** Wasif Husain

## Features

- Patient booking: clinician → date → time → confirm
- Confirmation email + simulated SMS log
- Scheduled 48-hour and 2-hour reminder records
- Manage booking (cancel / reschedule) with reference + email
- Clinic reports page for staff
- Branded Django admin (SmileCare Dental)

## Recommended: run with Docker (best for client handoff)

```bash
cd project21-dental-booking
docker compose up --build
```

Open http://localhost:8091/  
Full instructions: see `DOCKER.md`

## Run locally (without Docker)

```bash
cd project21-dental-booking
python3 -m pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py seed_data
python3 manage.py runserver
```

Open http://127.0.0.1:8000/

## Useful pages

| Page | URL |
|---|---|
| Home | `/` |
| Book | `/book/` |
| Manage booking | `/manage/` |
| Clinic reports (staff) | `/admin/reports/` |
| Developer credits | `/developer/` |
| Admin | `/admin/` |

## Admin login

- Username: `admin`
- Password: `SmileCare@2026`

## Email / reminders

**Default:** confirmation emails print in the terminal (console backend).

**Optional Mailtrap:**

```bash
export MAILTRAP_USER="your_username"
export MAILTRAP_PASS="your_password"
python3 manage.py runserver
```

See `.env.example`.

**Send due reminders:**

```bash
python3 manage.py send_due_reminders
```

This marks due email/SMS reminder logs as sent (email via configured backend; SMS stays simulated in the log).

## Demo walkthrough

1. Book an appointment and note the reference number  
2. Check terminal (or Mailtrap) for confirmation email  
3. Open `/manage/`, enter reference + email  
4. Try reschedule or cancel  
5. Login as admin → `/reports/` for clinic overview  
6. In admin, open Reminder logs to see confirmation + pending reminders  
