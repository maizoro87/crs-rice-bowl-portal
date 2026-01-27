# CRS Rice Bowl / Lenten Almsgiving Portal - Implementation Plan

## Project Overview

A single-page Lenten Almsgiving Portal with:
- **Public Page:** Beautiful, responsive page displaying quizzes, leaderboards, totals, and CRS donation links
- **Admin Panel:** Full GUI for non-technical staff to manage all content

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Container                         │
│  ┌─────────────┐     ┌─────────────────────────────────┐   │
│  │   nginx     │────▶│  Flask Application               │   │
│  │  (port 80)  │     │  ├── /api/* (JSON API)          │   │
│  │             │     │  ├── /admin/* (Admin Panel)     │   │
│  │  static/    │     │  └── SQLite DB                  │   │
│  │  public/    │     └─────────────────────────────────┘   │
│  └─────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
```

**Tech Stack:**
- **Backend:** Python Flask + SQLite
- **Frontend (Public):** Vanilla HTML/CSS/JS with Alpine.js for interactivity
- **Frontend (Admin):** Flask templates with Bootstrap for forms
- **Deployment:** Docker (nginx + gunicorn)

---

## Phase 1: Project Setup & Database Schema

### 1.1 Directory Structure
```
crs-site/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Configuration
│   ├── models.py            # SQLAlchemy models
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── api.py           # JSON API for public page
│   │   └── admin.py         # Admin panel routes
│   ├── templates/
│   │   ├── admin/
│   │   │   ├── base.html
│   │   │   ├── login.html
│   │   │   ├── dashboard.html
│   │   │   ├── quizzes.html
│   │   │   ├── totals.html
│   │   │   ├── classes.html
│   │   │   ├── announcements.html
│   │   │   ├── design.html
│   │   │   └── account.html
│   │   └── components/
│   └── static/
│       └── admin/           # Admin CSS/JS
├── public/                  # Public website (served by nginx)
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── app.js
│   └── images/
├── data/
│   └── crs.db               # SQLite database
├── Dockerfile
├── docker-compose.yml
├── nginx.conf
├── requirements.txt
└── run.py
```

### 1.2 Database Schema

```sql
-- Users (Admin accounts)
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Quizzes (6 weeks)
CREATE TABLE quizzes (
    id INTEGER PRIMARY KEY,
    week_number INTEGER UNIQUE NOT NULL,
    country_name TEXT NOT NULL,
    description TEXT,
    forms_link TEXT,
    opens_at DATETIME,
    closes_at DATETIME,
    schedule_mode TEXT DEFAULT 'auto',  -- 'auto' or 'manual'
    manual_visible BOOLEAN DEFAULT FALSE,
    participant_count INTEGER DEFAULT 0,
    participants_text TEXT,  -- Names, one per line
    winner_1 TEXT,
    winner_2 TEXT,
    winner_3 TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Classes
CREATE TABLE classes (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,  -- "Teacher + Period"
    rice_bowl_amount DECIMAL(10,2) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Settings (key-value store)
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
-- Keys: crs_donation_link, online_alms_total, show_grand_total,
--       theme, school_logo_url, enable_crs_imagery

-- Announcements
CREATE TABLE announcements (
    id INTEGER PRIMARY KEY,
    text TEXT NOT NULL,
    start_at DATETIME,
    end_at DATETIME,
    enabled BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## Phase 2: Backend Implementation (Flask)

### 2.1 Core Flask Setup
- [ ] Create Flask app with factory pattern
- [ ] Configure SQLAlchemy with SQLite
- [ ] Set up Flask-Login for authentication
- [ ] Create database models

### 2.2 Admin Authentication
- [ ] Login page with username/password
- [ ] Session-based authentication
- [ ] Password change functionality
- [ ] Protected routes decorator

### 2.3 Admin Routes & Templates

**Dashboard (`/admin/`)**
- Current week indicator
- Quick stats (totals, participant counts)
- Next quiz info

**Quizzes (`/admin/quizzes`)**
- List of 6 weeks with edit forms
- Fields: week, country, description, forms link, dates
- Schedule mode toggle (auto/manual)
- Participant count + paste names
- Winner selection (3 per week)

**Giving & Totals (`/admin/totals`)**
- CRS donation link field
- Online alms total input
- Rice bowl totals by class (table)
- Grand total toggle

**Classes (`/admin/classes`)**
- Add/edit/delete classes
- Class name (Teacher + Period format)

**Announcements (`/admin/announcements`)**
- Announcement text
- Start/end dates (optional)
- Enable/disable toggle

**Design (`/admin/design`)**
- Theme selector (Lenten Purple default)
- School logo upload
- CRS imagery toggle

**Account (`/admin/account`)**
- Change password form

### 2.4 JSON API for Public Page

```
GET /api/data
Response:
{
  "current_week": 3,
  "quizzes": [...],
  "classes": [...],
  "settings": {
    "crs_donation_link": "...",
    "online_alms_total": 1234.56,
    "show_grand_total": false,
    ...
  },
  "announcements": [...]
}
```

---

## Phase 3: Public Page Implementation

### 3.1 HTML Structure
Single page with sections:
- Header (title, description, CTA)
- Navigation (anchor links)
- Section A: Online Almsgiving
- Section B: This Week's Quiz (with countdown)
- Section C: Rice Bowl Info
- Section D: Class Leaderboard
- Section E: Totals & Updates
- Footer

### 3.2 CSS Styling
- Lenten purple color scheme (#4a0080, #6b2d9b)
- Mobile-first responsive design
- Clean, Catholic aesthetic
- Smooth scroll navigation
- Collapsible sections (past weeks)

### 3.3 JavaScript Functionality
- Fetch data from `/api/data`
- Countdown timer for quiz close
- Dynamic leaderboard rendering
- Collapsible past weeks accordion
- Auto-refresh totals (optional)

---

## Phase 4: Docker & Deployment

### 4.1 Update Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY public/ ./public/
COPY run.py .

EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
```

### 4.2 nginx Configuration
- Serve `/public/*` as static files
- Proxy `/api/*` and `/admin/*` to Flask
- Gzip compression
- Cache headers for static assets

### 4.3 docker-compose.yml
- Flask app service
- nginx service
- Shared volume for database persistence
- Environment variables for secrets

---

## Phase 5: Testing & Polish

### 5.1 Admin Panel Testing
- [ ] All CRUD operations work
- [ ] Validation errors display correctly
- [ ] Password change works
- [ ] Data persists after restart

### 5.2 Public Page Testing
- [ ] All sections render correctly
- [ ] Countdown timer accurate
- [ ] Mobile responsive
- [ ] Leaderboard sorts correctly
- [ ] Collapsible sections work

### 5.3 Integration Testing
- [ ] Admin changes reflect on public page
- [ ] API returns correct data
- [ ] Docker container runs correctly

---

## File Manifest

| File | Purpose |
|------|---------|
| `app/__init__.py` | Flask app factory |
| `app/config.py` | Configuration (dev/prod) |
| `app/models.py` | SQLAlchemy database models |
| `app/routes/api.py` | JSON API endpoints |
| `app/routes/admin.py` | Admin panel routes |
| `app/templates/admin/*.html` | Admin panel templates |
| `public/index.html` | Public portal page |
| `public/css/style.css` | Public page styles |
| `public/js/app.js` | Public page JavaScript |
| `requirements.txt` | Python dependencies |
| `run.py` | Application entry point |
| `nginx.conf` | nginx configuration |
| `Dockerfile` | Container build |
| `docker-compose.yml` | Container orchestration |

---

## Timeline Estimate

| Phase | Description |
|-------|-------------|
| Phase 1 | Project setup, database schema |
| Phase 2 | Flask backend, admin panel |
| Phase 3 | Public page (HTML/CSS/JS) |
| Phase 4 | Docker configuration |
| Phase 5 | Testing & polish |

---

## Default Admin Credentials

**Username:** `admin`
**Password:** `lent2026` (user should change on first login)

---

## Key Features Summary

**Public Page:**
- ✅ Header with CRS branding and CTA
- ✅ Online Almsgiving section with highlighted dates
- ✅ Weekly Quiz with countdown timer
- ✅ Participants list and winners display
- ✅ Past weeks collapsible accordion
- ✅ Rice Bowl information and due date
- ✅ Class Leaderboard (sortable)
- ✅ Totals display (with optional grand total reveal)
- ✅ Announcements bar
- ✅ Mobile responsive design
- ✅ Lenten purple theme

**Admin Panel:**
- ✅ Secure login
- ✅ Dashboard overview
- ✅ Quiz management (6 weeks)
- ✅ Participant/winner management
- ✅ Class management
- ✅ Totals management
- ✅ Announcements
- ✅ Theme/design settings
- ✅ Password change
