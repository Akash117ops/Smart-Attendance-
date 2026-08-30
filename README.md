# Smart Attendance System

An AI-powered attendance system that recognizes students' faces from a live classroom camera feed and marks attendance automatically — no roll calls, no ID cards.

## How it works

1. A student is **enrolled** with a few photos. Faces are detected (MTCNN) and converted into a 512-d embedding (FaceNet512 via DeepFace), which is stored against their profile.
2. During a live **session**, the camera feed is scanned every few frames. Detected faces are checked for **liveness/anti-spoofing** to reject photos or screens.
3. Each real face's embedding is compared (cosine distance) against enrolled students. A match below the distance threshold is marked **present**, timestamped, and logged with its confidence score.
4. Faculty can start/stop sessions, view live recognition, and pull attendance and monthly reports from a dashboard.

## Tech stack

| Layer | Tech |
|---|---|
| Face recognition | DeepFace (Facenet512), MTCNN detector, anti-spoof/liveness check |
| Backend | Flask, Flask-SQLAlchemy, Flask-CORS |
| Database | MySQL |
| Frontend | React (Vite), Lucide icons |
| CV runtime | OpenCV, NumPy |

## Project structure

```
backend/            Flask API — students, sessions, attendance, reports
  models/           SQLAlchemy models (Student, Classroom, Session, Attendance, Faculty, AuditLog)
  face_service.py   Generates & averages face embeddings at enrollment
  recognition_service.py  Live-frame face detection, liveness check, matching

face_engine/        Standalone CV scripts used during R&D
  enrollment.py, bulk_enrollment.py     Enroll students from images
  live_attendance.py, live_recognition.py  Webcam-based recognition trials
  antispoof_test.py, liveness_test.py   Anti-spoofing experiments

frontend/           React dashboard — live camera panel, students, sessions, reports
```

## API overview

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/students` | GET | List enrolled students |
| `/api/students/enroll` | POST | Enroll a new student (photos → embedding) |
| `/api/students/<id>` | DELETE | Remove a student |
| `/api/sessions/start` | POST | Start an attendance session for a classroom |
| `/api/sessions/<id>/stop` | POST | Stop a session |
| `/api/attendance/recognize` | POST | Run recognition on a camera frame |
| `/api/attendance` | GET | Attendance records |
| `/api/reports/monthly` | GET | Monthly attendance report |
| `/api/classrooms` | GET | List classrooms |
| `/api/sessions` | GET | List sessions |
| `/api/dashboard` | GET | Dashboard summary stats |

## Setup

**Backend**
```bash
cd backend
pip install -r requirements.txt
```
Create a `.env` file with `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`, then run the Flask app.

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

**face_engine (optional R&D scripts)**
```bash
cd face_engine
pip install -r requirements.txt
```
These are standalone scripts used to prototype enrollment and live recognition outside the API — not required to run the app itself.


