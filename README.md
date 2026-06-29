# 🎓 Smart Attendance System

> **AI-powered, full-stack attendance management** using Face Recognition, QR Codes, Supabase (pgvector), and Streamlit.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red?logo=streamlit)
![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL+pgvector-green?logo=supabase)
![License](https://img.shields.io/badge/license-MIT-brightgreen)

---

## ✨ Features

| Module | Features |
|---|---|
| 🔐 **Auth** | Login/Signup, bcrypt passwords, Admin & Student roles, session management |
| 📊 **Dashboard** | KPI metrics, 30-day trend chart, department breakdown, live attendance table |
| 👨‍🎓 **Students** | Add/Edit/Delete, search & filter, department assignment |
| 🧠 **Face Registration** | Upload 3–10 images, auto face detection with preview, 128-d embeddings stored in pgvector |
| 📷 **Face Attendance** | Webcam capture, real-time recognition, confidence score, duplicate prevention |
| 📱 **QR Attendance** | Unique QR per student (color-coded with segno), token validation, manual backup |
| 📈 **Analytics** | Daily/Weekly/Monthly Plotly charts, department pie, method distribution, student leaderboard |
| 📄 **Reports** | Date range filter, CSV & Excel export with styled headers |

---

## 🗂️ Project Structure

```
attendance_system/
│
├── app.py                        # Main entry (Login/Signup)
├── pages/
│   ├── 01_dashboard.py           # Admin dashboard
│   ├── 02_students.py            # Student CRUD
│   ├── 03_face_registration.py   # Face image upload & embedding
│   ├── 04_face_attendance.py     # Webcam face recognition
│   ├── 05_qr_attendance.py       # QR code attendance
│   ├── 06_analytics.py           # Charts & analytics
│   └── 07_reports.py             # Report export
│
├── services/
│   ├── auth_service.py           # Login, bcrypt, session
│   ├── face_service.py           # face_recognition + pgvector search
│   ├── qr_service.py             # segno QR generation + validation
│   ├── attendance_service.py     # Attendance CRUD + dedup
│   └── analytics_service.py     # Aggregation + Plotly charts
│
├── database/
│   ├── supabase_client.py        # Singleton client
│   ├── schema.sql                # Full DB schema (run first)
│   └── seed.sql                  # Demo data
│
├── models/
│   ├── user.py │ student.py │ attendance.py
│
├── utils/
│   ├── ui_helpers.py │ validators.py │ exporters.py │ constants.py
│
├── assets/styles.css             # Dark glassmorphism CSS
├── .streamlit/config.toml        # Dark theme
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Quick Start

### 1. Prerequisites

- **Python 3.10+**
- **pip** or **conda**
- A **Supabase** project (free tier works)
- Windows: Visual C++ Build Tools (for dlib) — OR use `dlib-bin` (pre-compiled, included in requirements)

### 2. Clone / Download

```bash
# If using git
git clone <your-repo-url>
cd attendance_system

# Or just navigate to the downloaded folder
cd "c:\Users\ashis\Downloads\ai learning\attendance"
```

### 3. Create Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 4. Install Dependencies

```powershell
pip install -r requirements.txt
```

> ⚠️ **Windows dlib note**: If `dlib-bin` fails, try:
> ```powershell
> pip install cmake
> pip install dlib
> ```
> Or install Visual C++ Build Tools from https://visualstudio.microsoft.com/visual-cpp-build-tools/

### 5. Set Up Supabase

1. Go to [supabase.com](https://supabase.com) → Create new project
2. Navigate to **SQL Editor**
3. Run `database/schema.sql` (copy-paste the entire file)
4. Run `database/seed.sql` for demo data
5. Get your credentials: **Project Settings → API**
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`

### 6. Configure Environment

```powershell
copy .env.example .env
```

Edit `.env`:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
APP_SECRET_KEY=your-random-secret
FACE_MATCH_THRESHOLD=0.5
ADMIN_EMAIL=admin@school.edu
ADMIN_PASSWORD=Admin@123456
ADMIN_NAME=System Administrator
```

### 7. Run the App

```powershell
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

### 8. Default Login

| Role | Email | Password |
|---|---|---|
| Admin | `admin@school.edu` | `Admin@123456` |

---

## 🗄️ Database Schema

```sql
users       → id, email, password_hash, full_name, role, is_active
students    → id, name, email, roll_number, department, face_embedding (vector(128)), qr_code_token
attendance  → id, student_id, date, time, method, status, confidence
```

**pgvector** stores face embeddings as 128-dimensional vectors with HNSW indexing for fast similarity search.

---

## 🧠 Face Recognition Flow

```
Upload 3-10 images
        ↓
face_recognition.face_locations()  ← detects faces
        ↓
face_recognition.face_encodings()  ← 128-d vector per image
        ↓
numpy.mean(all_encodings)          ← average embedding
        ↓
Supabase students.face_embedding   ← stored as vector(128)
        ↓ (attendance time)
Webcam capture → encode → match_face_embedding() RPC
        ↓
L2 distance < threshold → mark attendance
```

---

## 📱 QR Code Flow

```
generate_qr_code(student_id, token)
        ↓
segno.make_qr("ATTENDANCE_QR|student_id|token")
        ↓
PNG → base64 data URI → stored in students.qr_code_data
        ↓ (scan time)
Paste QR text → validate_qr_token() → match student → mark attendance
```

---

## 🔒 Security

- Passwords hashed with **bcrypt (cost=12)**
- **Service Role Key** used server-side only (bypasses RLS)
- **Row Level Security** enabled on all tables
- Input validation via regex + HTML escaping
- Parameterized queries through Supabase Python client (no raw SQL from user input)
- Environment variables via `.env` (never committed)

---

## 📦 Key Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web UI framework |
| `supabase` | Database client |
| `face-recognition` | Face detection & encoding |
| `dlib-bin` | Pre-compiled dlib (avoids CMake) |
| `bcrypt` | Password hashing |
| `segno` | QR code generation |
| `plotly` | Interactive charts |
| `pandas` | Data processing |
| `openpyxl` | Excel export |
| `python-dotenv` | Environment variables |

---

## 🌐 Deployment

### Streamlit Cloud (Recommended)

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo, set main file to `app.py`
4. Add secrets in the Streamlit Cloud dashboard (same as `.env`)

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential cmake libopenblas-dev
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Local HTTPS (for webcam)

Webcam requires HTTPS in production. For local dev:
```powershell
streamlit run app.py --server.enableCORS=false
```

---

## 🛠️ Troubleshooting

| Issue | Solution |
|---|---|
| `dlib` install fails | Use `dlib-bin` or install CMake + Visual C++ Build Tools |
| Webcam not working | Ensure browser camera permission granted; use HTTPS in production |
| Supabase connection error | Verify `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in `.env` |
| `pgvector` not found | Run `CREATE EXTENSION IF NOT EXISTS vector;` in Supabase SQL Editor |
| Face not recognized | Lower `FACE_MATCH_THRESHOLD` (e.g., `0.6`); ensure good lighting |
| Import error on Windows | Activate the venv with `.\venv\Scripts\activate` |

---

## 📄 License

MIT License — feel free to use and modify.

---

**Built with ❤️ using Python, Streamlit, Supabase, and face_recognition**
