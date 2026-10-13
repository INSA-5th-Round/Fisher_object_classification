# FISHER AI CCTV SYSTEM

> An intelligent AI-powered CCTV surveillance system for real-time object detection, tracking, video analytics, and automated security alerts.

FISHER AI CCTV SYSTEM is a modular intelligent surveillance platform designed to transform traditional CCTV cameras into an AI-assisted monitoring system.

The system processes live video streams, detects and tracks objects using modern computer vision and AI models, analyzes events, records important information, and sends alerts when suspicious or predefined activities are detected.

---

# Key Features

* Live CCTV and IP Camera Support
* Real-Time Video Frame Processing
* AI-Based Object Detection
* Human Detection and Tracking
* Vehicle Detection and Tracking
* Animal Detection
* Bag Detection
* Optional Fire Detection
* Restricted Area Monitoring
* Intrusion Detection
* Crowd Counting
* Loitering Detection
* Event Analytics and Statistics
* Automatic Screenshot Capture
* Telegram Alerts
* Email Alerts
* SMS Alerts
* Detection and Event Logging
* Web Dashboard
* User Authentication and Management

---

# System Architecture

FISHER is organized into multiple layers. Each layer has a specific responsibility, making the system easier to develop, maintain, and extend.

```text
FISHER AI CCTV SYSTEM
|
|-- 1. Camera Layer
|   |
|   |-- CCTV Cameras
|   |-- IP Cameras
|   |-- Video Streams
|
|-- 2. Video Processing Layer
|   |
|   |-- OpenCV
|   |-- FFmpeg
|   |-- Frame Extraction
|   |-- Video Enhancement
|
|-- 3. AI Detection Layer
|   |
|   |-- YOLOv8 / YOLO11
|   |-- Human Detection
|   |-- Vehicle Detection
|   |-- Animal Detection
|   |-- Bag Detection
|   |-- Fire Detection (Optional)
|
|-- 4. Tracking Layer
|   |
|   |-- ByteTrack
|   |-- Object ID Assignment
|   |-- Person Tracking
|   |-- Vehicle Tracking
|
|-- 5. Analytics Layer
|   |
|   |-- Intrusion Detection
|   |-- Crowd Counting
|   |-- Loitering Detection
|   |-- Restricted Area Monitoring
|   |-- Event Classification
|
|-- 6. Alert Layer
|   |
|   |-- Telegram Alerts
|   |-- Email Alerts
|   |-- SMS Alerts
|   |-- Screenshot Capture
|
|-- 7. Database Layer
|   |
|   |-- Detection Logs
|   |-- Alert Logs
|   |-- User Data
|   |-- Camera Data
|   |-- Event History
|
|-- 8. Dashboard Layer
|   |
|   |-- Live CCTV Feed
|   |-- Detection Results
|   |-- Statistics
|   |-- Reports
|   |-- User Management
|
|-- 9. Administration Layer
    |
    |-- Login System
    |-- Camera Configuration
    |-- Alert Configuration
    |-- System Settings
```

---

# System Layers

## 1. Camera Layer

The Camera Layer is the entry point of the system.

It receives video from different surveillance sources, including:

* CCTV cameras
* IP cameras
* RTSP video streams
* Other compatible video sources

The collected video is passed to the Video Processing Layer for further processing.

---

## 2. Video Processing Layer

This layer prepares the incoming video for AI analysis.

### Technologies

* OpenCV
* FFmpeg

### Responsibilities

* Extract frames from video streams
* Resize frames
* Enhance image quality
* Process regions of interest
* Prepare frames for AI detection

Efficient video processing helps reduce unnecessary computation while maintaining useful detection performance.

---

## 3. AI Detection Layer

The AI Detection Layer is responsible for identifying objects within video frames.

### AI Models

* YOLOv8
* YOLO11

### Detection Categories

* Humans
* Vehicles
* Animals
* Bags
* Fire (Optional)

The detector analyzes frames and returns information such as:

* Object class
* Confidence score
* Bounding box
* Detection location

---

## 4. Tracking Layer

Detection identifies objects in individual frames. The Tracking Layer allows the system to maintain an object's identity across multiple frames.

### Technology

ByteTrack

### Responsibilities

* Assign unique object IDs
* Track people
* Track vehicles
* Maintain object movement information
* Associate detections between consecutive frames

For example, a person detected in multiple frames can continue to be recognized as the same tracked object rather than being treated as a new person in every frame.

---

## 5. Analytics Layer

The Analytics Layer converts raw detection and tracking information into meaningful security events.

### Intrusion Detection

Detects when an object enters a predefined monitored area.

### Crowd Counting

Counts the number of people within a particular area.

### Loitering Detection

Identifies objects that remain within an area for longer than a configured period.

### Restricted Area Monitoring

Monitors predefined restricted zones.

### Event Classification

Combines detection and tracking information to classify important events.

---

## 6. Alert Layer

When an important event is detected, the Alert Layer can notify authorized users.

### Supported Alert Methods

* Telegram
* Email
* SMS
* Screenshot Capture

An alert can contain useful information such as:

* Event type
* Camera name
* Detection time
* Detected object
* Confidence score
* Captured screenshot

---

## 7. Database Layer

The Database Layer stores information generated by the surveillance system.

### Stored Information

* Detection logs
* Alert logs
* User information
* Camera information
* Event history

This information can later be used for:

* Searching previous events
* Generating reports
* Viewing statistics
* Investigating incidents
* System monitoring

---

## 8. Dashboard Layer

The Dashboard provides a central interface for authorized users to interact with the system.

### Dashboard Features

* Live CCTV feeds
* Detection results
* Statistics
* Reports
* User management
* Alert history
* Camera monitoring

The dashboard provides a visual overview of the surveillance environment and detected events.

---

## 9. Administration Layer

The Administration Layer manages system configuration and access control.

### Login System

Provides authentication for authorized users.

### Camera Configuration

Allows administrators to configure cameras and video streams.

### Alert Configuration

Controls which alerts are enabled and where notifications are sent.

### System Settings

Manages general system configuration.

---

# Technology Stack

| Layer            | Technologies                 |
| ---------------- | ---------------------------- |
| Camera           | CCTV, IP Cameras, RTSP       |
| Video Processing | OpenCV, FFmpeg               |
| AI Detection     | YOLOv8 / YOLO11              |
| Object Tracking  | ByteTrack                    |
| Analytics        | Computer Vision and Tracking |
| Alerts           | Telegram, Email, SMS         |
| Database         | SQL/NoSQL Database           |
| Dashboard        | Web-Based Interface          |
| Authentication   | Login and Access Control     |

---

# How FISHER Works

1. The Camera Layer receives live video.
2. The Video Processing Layer extracts and prepares frames.
3. The AI Detection Layer identifies objects.
4. The Tracking Layer assigns IDs and follows objects.
5. The Analytics Layer analyzes their behavior and location.
6. The Alert Layer generates notifications for important events.
7. The Database Layer stores detections, alerts, and event history.
8. The Dashboard Layer displays live information and reports.
9. The Administration Layer controls users and system configuration.

---

# Project Goals

FISHER AI CCTV SYSTEM aims to provide an intelligent surveillance platform that can:

* Reduce the need for continuous manual monitoring
* Detect important objects automatically
* Monitor restricted areas
* Track people and vehicles
* Identify predefined security events
* Notify authorized personnel quickly
* Maintain historical detection records
* Provide centralized CCTV monitoring

---

# Security Considerations

Because FISHER processes surveillance data, security is an important part of the system.

The system should consider:

* Secure user authentication
* Role-based access control
* Protected camera credentials
* Secure communication
* Database access control
* Audit logging
* Secure storage of screenshots and recordings
* Protection of sensitive surveillance information

---

# Project Structure

```text
FISHER-AI-CCTV/
|
|-- camera/
|   |-- cctv_client.py
|   |-- stream_manager.py
|   |-- camera_config.py
|
|-- video_processing/
|   |-- frame_extractor.py
|   |-- video_processor.py
|   |-- enhancement.py
|
|-- detection/
|   |-- detector.py
|   |-- yolo_model.py
|   |-- detection_config.py
|
|-- tracking/
|   |-- tracker.py
|   |-- bytetrack.py
|
|-- analytics/
|   |-- intrusion.py
|   |-- crowd_counting.py
|   |-- loitering.py
|   |-- restricted_area.py
|   |-- event_classifier.py
|
|-- alerts/
|   |-- telegram.py
|   |-- email.py
|   |-- sms.py
|   |-- screenshot.py
|
|-- database/
|   |-- models/
|   |-- database.py
|   |-- repositories/
|
|-- dashboard/
|   |-- frontend/
|   |-- backend/
|
|-- administration/
|   |-- authentication.py
|   |-- camera_management.py
|   |-- alert_configuration.py
|   |-- system_settings.py
|
|-- tests/
|
|-- requirements.txt
|-- .env.example
|-- .gitignore
|-- README.md
```

---

# Future Improvements

Possible future additions include:

* Advanced fire and smoke detection
* License plate recognition
* PPE detection
* Person re-identification
* Audio event detection
* Mobile application
* Cloud deployment
* Custom-trained AI models
* Advanced analytics
* Multi-camera monitoring
* More notification channels

---

# Responsible Use

FISHER is intended for authorized security, monitoring, research, and educational environments.

Camera systems should be deployed responsibly and in accordance with applicable privacy, surveillance, and data-protection requirements. Access to surveillance data should be restricted to authorized personnel.

---

# Project

**FISHER AI CCTV SYSTEM**

An AI-powered CCTV platform combining:

**Computer Vision, Object Detection, Object Tracking, Video Analytics, Automated Alerts, and Centralized Monitoring.**

---

# Status

**Under Development**

The system architecture is modular, allowing individual components to be developed, tested, and integrated progressively.

## Consolidated branch entry points

This branch combines alert integration, object detection and tracking, CCTV analytics, video processing, and the database layer.

Install dependencies with `pip install -r requirements.txt` and copy `.env.example` to `.env`, then configure the services you intend to run.

- Detection and alerts: `python object_detection.py`
- CCTV analytics: `python main.py`; see [CCTV_ANALYTICS.md](CCTV_ANALYTICS.md).
- Video processing: see [VIDEO_PROCESSING.md](VIDEO_PROCESSING.md).
- Database API: `uvicorn app.main:app --reload`; configure `DATABASE_URL` and `SECRET_KEY`, then apply migrations with `alembic upgrade head`.

The database files are restored from the database branch because they had been removed from main. These components retain their separate entry points.
