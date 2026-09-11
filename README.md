# FISHER AI CCTV SYSTEM

AI-powered CCTV monitoring and surveillance backend built with **Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic, YOLO, and ByteTrack**.

The system is designed to detect, track, analyze, and record events from CCTV/IP camera streams.

---

## 🚀 Project Overview

FISHER AI CCTV SYSTEM provides an AI-powered surveillance platform with:

* CCTV/IP camera management
* Real-time video processing
* AI object detection
* Person and vehicle tracking
* Intrusion detection
* Crowd monitoring
* Loitering detection
* Restricted-area monitoring
* Event management
* Alert management
* Detection history
* Dashboard integration
* User management

---

## 🏗️ System Architecture

```text
                    FISHER AI CCTV SYSTEM
                             │
                             ▼
                    ┌─────────────────┐
                    │  Camera Layer   │
                    │ CCTV / IP Camera│
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Video Processing│
                    │ OpenCV / FFmpeg │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  AI Detection  │
                    │ YOLOv8 / YOLO11 │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    Tracking     │
                    │    ByteTrack    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   Analytics     │
                    │ Events / Rules  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │     Alerts      │
                    │ Telegram/Email  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    Database     │
                    │ Neon PostgreSQL │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    Dashboard    │
                    │ FastAPI / Web UI│
                    └─────────────────┘
```

---

# 🛠️ Technology Stack

### Backend

* Python
* FastAPI
* Uvicorn

### Database

* PostgreSQL
* Neon PostgreSQL
* SQLAlchemy
* Alembic

### AI / Computer Vision

* OpenCV
* FFmpeg
* YOLOv8 / YOLO11
* ByteTrack

### Authentication

* JWT
* Password hashing
* Role-based access

### Notifications

* Telegram
* Email
* SMS

---

# 📁 Project Structure

```text
fisher-ai-cctv/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── security.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   └── base.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── camera.py
│   │   ├── detection.py
│   │   ├── event.py
│   │   └── alert.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── camera.py
│   │   ├── detection.py
│   │   ├── event.py
│   │   └── alert.py
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── users.py
│   │   ├── cameras.py
│   │   ├── detections.py
│   │   ├── events.py
│   │   └── alerts.py
│   │
│   └── services/
│       ├── __init__.py
│       └── detection_service.py
│
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── .env
├── .env.example
├── .gitignore
├── alembic.ini
├── requirements.txt
└── README.md
```

---

# 🗄️ Database

The project uses **Neon PostgreSQL** as the shared cloud database.

Current database tables:

```text
users
cameras
detections
events
alerts
alembic_version
```

### Database relationships

```text
users
  │
  ├────────────── events
  │
  └────────────── alerts

cameras
  │
  ├────────────── detections
  │
  ├────────────── events
  │
  └────────────── alerts

events
  │
  └────────────── alerts
```

---

# 👥 Team Database Workflow

The database is hosted on Neon.

Team members **do not need PostgreSQL installed locally**.

Each developer runs the application on their own computer while connecting to the shared Neon database.

```text
Developer A ──┐
Developer B ──┤
Developer C ──┼────> Neon PostgreSQL
Developer D ──┘
```

All developers can work with the same database.

---

# 🔐 Environment Variables

Never commit the real `.env` file to GitHub.

Create:

```text
.env
```

locally.

Example:

```env
DATABASE_URL=postgresql+psycopg2://USERNAME:PASSWORD@HOST/DATABASE?sslmode=require

SECRET_KEY=your-secret-key

ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### `.env.example`

The repository should contain:

```env
DATABASE_URL=postgresql+psycopg2://USERNAME:PASSWORD@HOST/DATABASE?sslmode=require

SECRET_KEY=your-secret-key-here

ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Each developer creates their own `.env`.

---

# ⚠️ Security Rules

Never commit:

```text
.env
```

Never commit:

* Database passwords
* Neon credentials
* JWT secret keys
* API keys
* Telegram bot tokens
* Email passwords
* CCTV passwords
* Private camera URLs

The `.gitignore` should contain:

```gitignore
.env
.env.*
!.env.example
```

If a secret is accidentally pushed to GitHub, **rotate it immediately**.

---

# 💻 Installation

## 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

Enter the project:

```bash
cd fisher-ai-cctv
```

---

## 2. Create virtual environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

# 📦 Install Dependencies

```bash
pip install -r requirements.txt
```

---

# ⚙️ Configure Environment

Create:

```text
.env
```

Copy the structure from:

```text
.env.example
```

Then add the Neon database connection information provided securely by the project administrator.

---

# 🗃️ Database Migration

Alembic manages database schema changes.

Check the current migration:

```bash
alembic current
```

Check available migrations:

```bash
alembic history
```

Apply migrations:

```bash
alembic upgrade head
```

---

# 🔄 Database Development Workflow

When changing a SQLAlchemy model:

### 1. Modify the model

Example:

```python
class Camera(Base):
    ...
```

### 2. Generate migration

```bash
alembic revision --autogenerate -m "describe the change"
```

### 3. Apply migration

```bash
alembic upgrade head
```

### 4. Verify

```bash
alembic current
```

The migration should show:

```text
(head)
```

---

# 🚀 Run the Backend

Start FastAPI:

```bash
uvicorn app.main:app --reload
```

The API will run at:

```text
http://127.0.0.1:8000
```

---

# 📚 API Documentation

FastAPI automatically provides Swagger documentation.

Open:

```text
http://127.0.0.1:8000/docs
```

Alternative documentation:

```text
http://127.0.0.1:8000/redoc
```

---

# ❤️ Health Check

Open:

```text
http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "api": "running",
  "database": "connected"
}
```

---

# 📡 API Modules

The backend currently contains:

## Users

```text
/users
```

Used for:

* Creating users
* Listing users
* Getting user information
* User management

---

## Cameras

```text
/cameras
```

Used for:

* Adding cameras
* Listing cameras
* Getting camera information
* Removing cameras
* Camera configuration

---

## Detections

```text
/detections
```

Used for:

* Recording AI detections
* Getting detection history
* Filtering detections by camera

Example detection:

```json
{
  "camera_id": 1,
  "object_type": "person",
  "confidence": 0.94,
  "tracking_id": 12,
  "bounding_box": {
    "x1": 100,
    "y1": 120,
    "x2": 300,
    "y2": 500
  }
}
```

---

## Events

```text
/events
```

Used for:

* Intrusion events
* Loitering events
* Restricted-area events
* Crowd events
* Event resolution

---

## Alerts

```text
/alerts
```

Used for:

* Telegram alerts
* Email alerts
* SMS alerts
* Alert status
* Alert history

---

# 🤖 AI Processing

The planned AI pipeline is:

```text
CCTV Stream
     ↓
OpenCV / FFmpeg
     ↓
Frame Extraction
     ↓
YOLO
     ↓
Object Detection
     ↓
ByteTrack
     ↓
Object Tracking
     ↓
Analytics
     ↓
Event Detection
     ↓
Alert
     ↓
Database
```

Supported detection targets may include:

* Person
* Vehicle
* Animal
* Bag
* Fire

---

# 📊 Analytics

The system is designed to support:

### Intrusion Detection

Detect objects entering restricted areas.

### Crowd Counting

Count people in a specific camera area.

### Loitering Detection

Detect objects/persons remaining in an area for too long.

### Restricted Area Monitoring

Monitor predefined zones.

### Event Classification

Classify detected situations into events.

---

# 🚨 Alert System

Possible notification channels:

```text
AI Event
    │
    ├── Telegram
    ├── Email
    ├── SMS
    └── Dashboard
```

Alerts can contain:

* Camera name
* Location
* Event type
* Detection information
* Timestamp
* Screenshot/evidence

---

# 🧑‍💻 Git Workflow

Before starting work:

```bash
git pull origin main
```

Create a feature branch:

```bash
git checkout -b feature/camera-management
```

Make changes and test them.

Then:

```bash
git add .
git commit -m "Add camera management"
git push origin feature/camera-management
```

Create a Pull Request on GitHub.

---

# 🚫 Files That Should NOT Be Committed

```text
.env
venv/
__pycache__/
*.pyc
*.log

screenshots/
evidence/
recordings/
videos/
captures/

*.pt
*.pth
*.onnx
*.weights

*.db
*.sqlite
*.sqlite3
```

Do **not** ignore:

```text
alembic/versions/
```

Alembic migration files **must be committed** to GitHub.

---

# 👥 Team Rules

### Developers should:

* Pull the latest code before starting work.
* Use feature branches.
* Never commit `.env`.
* Never expose database credentials.
* Run migrations after pulling migration changes.
* Test the API before pushing.
* Create Pull Requests for important changes.
* Keep commit messages clear.

### Developers should NOT:

* Delete production database tables.
* Change the shared database manually without agreement.
* Commit secrets.
* Commit large AI model files.
* Commit CCTV recordings.
* Modify migration history that has already been shared/applied without discussing it with the team.

---

# 🧪 Testing

Before creating a Pull Request:

```bash
alembic current
```

Then run:

```bash
uvicorn app.main:app --reload
```

Check:

```text
/docs
/health
```

Test the API endpoints.

---

# 📌 Current Database Migration

Current migration:

```text
5ae9b44811cc
```

Status:

```text
HEAD
```

Database:

```text
Neon PostgreSQL
```

---

# 🔮 Future Development

Planned improvements include:

* [ ] JWT authentication
* [ ] Role-based authorization
* [ ] Camera health monitoring
* [ ] Live CCTV streaming
* [ ] YOLO integration
* [ ] ByteTrack integration
* [ ] Intrusion detection
* [ ] Loitering detection
* [ ] Crowd counting
* [ ] Restricted zones
* [ ] Screenshot evidence
* [ ] Telegram integration
* [ ] Email notifications
* [ ] SMS notifications
* [ ] Dashboard
* [ ] Analytics reports
* [ ] Detection history
* [ ] User management
* [ ] Docker deployment
* [ ] Production deployment
* [ ] Automated testing
* [ ] CI/CD

---

# 🏆 Project Goal

The goal of FISHER AI CCTV SYSTEM is to build a reliable AI-powered CCTV monitoring platform capable of:

```text
Detect
  ↓
Track
  ↓
Analyze
  ↓
Identify Events
  ↓
Store Evidence
  ↓
Notify
  ↓
Monitor
  ↓
Report
```

---

## 👨‍💻 Development Team

**Project:** FISHER AI CCTV SYSTEM

**Backend:** Python + FastAPI

**Database:** Neon PostgreSQL

**AI:** YOLO + ByteTrack

**Computer Vision:** OpenCV + FFmpeg

**Database ORM:** SQLAlchemy

**Migration:** Alembic
