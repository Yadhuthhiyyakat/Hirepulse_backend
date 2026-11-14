# HirePulse Backend

Django REST Framework backend for the **HirePulse** recruitment management platform. Built with Python, Django, DRF, SimpleJWT, Channels, and cloud integrations for **Supabase PostgreSQL** and **Supabase Storage Buckets**.

---

## Features
- **Custom User Model**: `accounts.User` with UUID primary keys and email-based authentication.
- **JWT Authentication**: Pair creation, refresh token rotation, blacklisting via `djangorestframework-simplejwt`.
- **Role-Based Access Control**: Strict permissions for `JOB_SEEKER`, `RECRUITER`, and `ADMIN`.
- **Job Discovery & Search**: Faceted search powered by `django-filter` (role type, remote/onsite/hybrid, salary bounds, experience level).
- **Application Funnel**: Pipeline stages (`applied`, `reviewing`, `shortlisted`, `interview`, `hired`, `rejected`) with duplicate submission prevention and confidential internal recruiter notes.
- **Real-time Notifications**: WebSockets powered by Django Channels & Daphne ASGI with live in-app updates.
- **Native Supabase Storage**: Connects directly to Supabase Storage buckets using **only `SUPABASE_URL` and `SUPABASE_KEY`** (no complex AWS S3 credentials needed).
- **Supabase PostgreSQL**: Native support for pooled and direct connections with automatic SSL enforcement.
- **API Documentation**: Automated OpenAPI 3.0 schema and interactive Swagger UI via `drf-spectacular`.

---

## Supabase Configuration

HirePulse connects to Supabase with minimal configuration:

### 1. Supabase Storage (Buckets) — Only 2 Variables!

In your Supabase project dashboard (**Project Settings -> API**):
- **Project URL**: e.g., `https://[PROJECT-REF].supabase.co`
- **Project API Keys**: anon key (public) or service_role key

Add to your `backend/.env`:
```bash
SUPABASE_URL=https://[YOUR-PROJECT-REF].supabase.co
SUPABASE_KEY=[YOUR-SUPABASE-ANON-OR-SERVICE-KEY]
SUPABASE_BUCKET_NAME=hirepulse  # Optional (defaults to 'hirepulse')
```
> **How it works**: HirePulse interacts directly with the Supabase Storage REST API. Profile pictures and company logos are given public URLs, while applicant resumes are served with **secure signed URLs** expiring after 1 hour. No AWS keys, regions, or endpoint URLs required!

---

### 2. Supabase PostgreSQL Database

In Supabase Dashboard (**Project Settings -> Database -> Connection string -> URI**):

Copy the URI (Transaction Pooler on port 6543 recommended) and paste as `DATABASE_URL`:
```bash
DATABASE_URL=postgresql://postgres.[YOUR-PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require
```

*(Alternatively, you can simply set `SUPABASE_DB_PASSWORD=[YOUR-PASSWORD]` and HirePulse will auto-derive the database host directly from `SUPABASE_URL`!)*

---

### Local Development Fallback
If neither `SUPABASE_URL` nor `DATABASE_URL` is set, HirePulse defaults seamlessly to local SQLite (`db.sqlite3`) and local file storage (`backend/media/`) for instant development and automated testing.

---

## Running Locally

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply database migrations
python manage.py migrate

# 4. Seed initial mock data (recruiters, candidates, jobs, applications)
python manage.py seed_data

# 5. Start ASGI server with Channels support
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

API Server: `http://localhost:8000`
Swagger UI: `http://localhost:8000/api/docs/`
OpenAPI Schema: `http://localhost:8000/api/schema/`
Django Admin: `http://localhost:8000/admin/`

---

## Running Automated Tests

```bash
python manage.py test
```

All 12 test suites cover authentication, role permissions, jobs filtering, and application pipelines.
# Hirepulse_backend
