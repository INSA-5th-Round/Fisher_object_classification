# FISHER CCTV — Operations Command Center (Frontend)

This directory contains the production React 19 + TypeScript + Vite frontend for the **FISHER CCTV Intelligent Defense & Surveillance Platform**.

For complete system architecture, backend integration, Python detection setup, MongoDB Atlas persistence, and Telegram escalation workflows, refer to the root [Project README](../../../README.md).

---

## Project Team & Engineering Contributions

- **Hawlet Musbah**: Backend and Frontend Integration, Video Frame Processing, and Project Coordination
- **Iman Muhammednur**: Dashboard Frontend
- **Sitota Getahun**: Frame Analysis
- **Bona Tolasa**: Database Management
- **Natnaile Desalgn**: AI Object Detection
- **Nuhamin Anbese**: Telegram Alerts

---

## Features

- **Initial Authentication Gate**: Dedicated login screen requiring Username, Authorized Email, and Password. Strictly restricted to the 3 approved accounts (`admin@fisher.cctv`, `operator@fisher.cctv`, `supervisor@fisher.cctv`).
- **Live CCTV Video Player**: Streams real-time MJPEG feed directly from the single-owner camera backend (`/api/cameras/CAM-001/stream`).
- **Incident Alert Center**: Real-time intrusion incident tracking, acknowledgment, resolution, and Telegram status updates.
- **Detection Results**: Live review of AI-detected objects, classifications, timestamps, and confidence ratings.
- **Security Reports & Dedicated Media Modal**: Compiles official security reports from MongoDB Atlas records with audit summaries, captured intrusion photos, and an embedded HTML5 video player for the 2-minute incident recording.
- **User Management**: Strictly restricted account administration enforcing the 3 authorized system emails.
- **Zero Mock Data**: Displays only genuine real-time camera feeds and database records.

---

## Quick Start & Usage

### 1. Install Dependencies
```powershell
npm install
```

### 2. Run Development Server
```powershell
npm run dev
```
*(Runs on `http://localhost:5173` with reverse proxy to backend on port 8000)*

### 3. Log In to Dashboard
Open `http://localhost:5173` and log in with an authorized account:
- **Username**: `admin`
- **Authorized Email**: `admin@fisher.cctv`
- **Password**: `admin123`

### 4. Run Unit Tests (Vitest)
```powershell
npm test -- --run
```

### 5. Build for Production
```powershell
npm run build
```

---

## Environment Configuration (`.env`)

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api
VITE_BACKEND_URL=http://127.0.0.1:8000
```
