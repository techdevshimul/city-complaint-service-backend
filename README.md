# CityCare Complaint Service Backend

CityCare is a FastAPI REST API for reporting, tracking, and managing city
complaints. It uses SQLAlchemy for database access, PostgreSQL for persistence,
and JWT bearer tokens for authentication.

## What It Provides

- User registration, login, profile updates, and password changes
- Citizen complaint creation and management
- Admin complaint review, assignment, priority, and status updates
- Complaint status history and resolution notes
- Category management and active-user management for administrators
- Search, filtering, sorting, and pagination for complaint lists
- OpenAPI documentation through Swagger UI and ReDoc
- CORS support for local frontend development servers

## Technology

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic
- `python-jose` for JWT tokens
- `passlib` and `bcrypt` for password hashing
- Uvicorn

## Project Layout

```text
city-complaint-service-backend/
├── main.py                 # FastAPI app, routers, and CORS configuration
├── database.py             # SQLite engine, session factory, and DB dependency
├── models.py               # SQLAlchemy models
├── schemas.py              # Pydantic request and response schemas
├── requirements.txt        # Python dependencies
├── README.md
└── router/
    ├── auth.py             # Authentication and user endpoints
    ├── complaints.py       # Categories and citizen complaint endpoints
    └── admin.py            # Administrator endpoints
```

The application connects to the configured PostgreSQL database when it starts.

## Setup

Python 3.9 or newer is recommended.

```bash
cd city-complaint-service-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell, activate the environment with:

```powershell
.\venv\Scripts\Activate.ps1
```

## Run the Server

```bash
uvicorn main:app --reload
```

The API runs at `http://127.0.0.1:8000` by default.

Useful URLs:

- Health check: `GET http://127.0.0.1:8000/`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Authentication

Register with `POST /createuser`, then log in with
`POST /login`. The login request uses form fields named `username` and
`password` and returns an access token.

Send the token to protected endpoints as:

```text
Authorization: Bearer <access_token>
```

The supported roles are `user` and `admin`. Admin-only endpoints reject users
without the `admin` role.

## API Reference

### Authentication and users

| Method | Endpoint          | Access        | Description                                        |
| ------ | ----------------- | ------------- | -------------------------------------------------- |
| POST   | `/createuser`     | Public        | Create a user or admin account                     |
| POST   | `/login`          | Public        | Authenticate with username and password            |
| GET    | `/user`           | Authenticated | Get the current user's profile                     |
| PUT    | `/edituser`       | Authenticated | Update the current user's email, username, or name |
| PUT    | `/passwordchange` | Authenticated | Change the current user's password                 |
| POST   | `/forgotpassword` | Public        | Submit a password recovery request                 |

### Categories and citizen complaints

| Method | Endpoint                     | Access         | Description                            |
| ------ | ---------------------------- | -------------- | -------------------------------------- |
| GET    | `/categories`                | Public         | List active categories                 |
| GET    | `/complaints/my`             | Authenticated  | List the current user's complaints     |
| POST   | `/complaints`                | Authenticated  | Submit a new complaint                 |
| GET    | `/complaints/{complaint_id}` | Owner or admin | View a complaint and its history       |
| PUT    | `/complaints/{complaint_id}` | Owner          | Edit a complaint while it is pending   |
| DELETE | `/complaints/{complaint_id}` | Owner          | Delete a complaint while it is pending |

### Administrator operations

Every endpoint in this section requires the `admin` role.

| Method | Endpoint                           | Description                                           |
| ------ | ---------------------------------- | ----------------------------------------------------- |
| GET    | `/admin/dashboard`                 | Return complaint totals by status                     |
| GET    | `/admin/complaints`                | List and filter all complaints                        |
| PUT    | `/admin/complaints/{complaint_id}` | Update status, priority, assignee, or resolution note |
| POST   | `/admin/categories`                | Create a category                                     |
| PUT    | `/admin/categories/{category_id}`  | Update a category                                     |
| DELETE | `/admin/categories/{category_id}`  | Deactivate a category                                 |
| GET    | `/admin/users`                     | List all users                                        |
| PATCH  | `/admin/users/{user_id}/toggle`    | Activate or deactivate a user                         |

## Complaint Data

Complaint priorities are:

```text
low, medium, high, urgent
```

Complaint statuses are:

```text
pending, in_progress, resolved, rejected
```

New complaints start as `pending`. Citizens can edit and delete only their own
pending complaints. Administrators can view and manage every complaint.

### List query parameters

The `/complaints/my` and `/admin/complaints` endpoints support these filters:

- `search`: match the title, description, or location
- `category_id`: filter by category
- `status`: filter by complaint status
- `date_from`: include complaints created on or after this date
- `date_to`: include complaints created on or before this date
- `sort`: `newest`, `oldest`, or `alphabetical`
- `page`: page number, starting at 1
- `page_size`: number of results per page, from 1 to 50

### Status history

Each complaint response includes a `history` array. The API creates the first
`pending` entry when the complaint is submitted. When an administrator changes
the status, it appends a new entry. Entries are ordered from oldest to newest
and contain `id`, `status`, `note`, and `created_at`.

Update a complaint status with:

```http
PUT /admin/complaints/{complaint_id}
Content-Type: application/json
Authorization: Bearer <admin_access_token>
```

```json
{
  "status": "resolved",
  "resolution_note": "Pothole repaired"
}
```

The `resolution_note` is saved on the complaint and is used as the note for the
new history entry when the status changes. The same admin endpoint can also
update `priority` and `assigned_to_id`.

## Database Models

- `User`: credentials, profile data, role, and active state
- `Category`: complaint category name, description, and active state
- `Complaint`: report details, priority, status, assignment, and resolution note
- `StatusHistory`: audit entries for complaint status changes

## Configuration and Security Notes

- CORS allows local frontend origins on ports `3000`, `5173`, `5174`, and any
  localhost or `127.0.0.1` port through the configured regex.
- The JWT secret is currently hard-coded in `router/auth.py` for development.
  Move it to an environment variable and rotate it before production use.
- The registration endpoint currently accepts the `user` or `admin` role from
  the request body. Restrict admin account creation before deploying publicly.
- Tables are created with `Base.metadata.create_all()` at application startup.
  There is currently no migration workflow.

This project is intended for educational use.
