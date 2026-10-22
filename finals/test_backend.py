"""
Verification and Test Suite for FISHER CCTV Backend Service
"""

import sys
from pathlib import Path
from fastapi.testclient import TestClient

from config import settings
import database
from detection_api import app
from telegram_service import telegram_service


def test_configuration():
    print("\n--- 1. Testing Configuration ---")
    assert settings.BOT_TOKEN, "BOT_TOKEN must not be empty"
    assert settings.CHAT_ID, "CHAT_ID must not be empty"
    assert settings.MONGODB_URI, "MONGODB_URI must not be empty"
    assert settings.DB_NAME == "fisher_cctv", f"Unexpected DB_NAME: {settings.DB_NAME}"
    assert len(settings.AUTHORIZED_EMAILS) == 3, f"Expected 3 authorized emails, got {len(settings.AUTHORIZED_EMAILS)}"
    print(" [PASS] .env file loaded successfully.")
    print(f"        Bot Token: configured (hidden)")
    print(f"        Chat ID: {settings.CHAT_ID}")
    print(f"        Authorized emails: {settings.AUTHORIZED_EMAILS}")


def test_telegram_connection():
    print("\n--- 2. Testing Telegram Bot Credentials ---")
    info = telegram_service.verify_credentials()
    print(f"        Verification result: {info}")
    assert info.get("valid") is True, f"Telegram bot check failed: {info}"
    print(f" [PASS] Telegram Bot connected: @{info.get('username')} ({info.get('bot_name')})")


def test_database_connection():
    print("\n--- 3. Testing MongoDB Atlas Database ---")
    health = database.check_db_connection()
    print(f"        Connection status: {health.get('status')}")
    assert health.get("status") == "connected", f"Database not connected: {health}"

    database.init_indexes()
    print(" [PASS] MongoDB connection alive and indexes initialized.")

    stats = database.get_dashboard_statistics()
    print(f"        Dashboard statistics: {stats}")
    assert "totalCameras" in stats
    assert "onlineCameras" in stats
    assert "totalDetections" in stats
    assert "activeAlerts" in stats
    print(" [PASS] MongoDB statistics computed successfully.")


def test_contract_endpoints():
    print("\n--- 4. Testing Contract Endpoints with Frontend ---")
    with TestClient(app) as client:
        # 1. LIVE PC CAMERA STREAM
        print(" -> Testing 1: Live PC Camera Stream GET /api/cameras/CAM-001/stream")
        with client.stream("GET", "/api/cameras/CAM-001/stream") as stream_res:
            assert stream_res.status_code == 200, f"Camera stream returned {stream_res.status_code}"
            content_type = stream_res.headers.get("Content-Type", "")
            assert "multipart/x-mixed-replace" in content_type, f"Bad content type: {content_type}"
            assert "boundary=frame" in content_type, f"Missing boundary: {content_type}"

            for chunk in stream_res.iter_raw(chunk_size=1024):
                if b"--frame" in chunk and b"image/jpeg" in chunk:
                    print(" [PASS] Live stream chunk received with valid multipart JPEG boundary.")
                    break

        # 2. REGISTERED CAMERAS
        print(" -> Testing 2: Registered Cameras GET /api/cameras")
        res = client.get("/api/cameras")
        assert res.status_code == 200
        cameras = res.json()
        assert isinstance(cameras, list)
        assert len(cameras) >= 1
        cam_001 = next((c for c in cameras if c["id"] == "CAM-001"), None)
        assert cam_001 is not None
        assert cam_001["name"] == "PC Camera (OpenCV)"
        assert cam_001["streamUrl"] == "/api/cameras/CAM-001/stream"
        print(f" [PASS] Camera verified: {cam_001['id']} ({cam_001['status']})")

        # 3. DASHBOARD STATISTICS
        print(" -> Testing 3: Dashboard Statistics GET /api/dashboard/statistics")
        res = client.get("/api/dashboard/statistics")
        assert res.status_code == 200
        stats = res.json()
        for key in ["totalCameras", "onlineCameras", "totalDetections", "activeAlerts"]:
            assert key in stats
        print(f" [PASS] Dashboard statistics contract verified: {stats}")

        # 4. AUTHENTICATION & LOGIN RESTRICTIONS
        print(" -> Testing 4: Authentication & Login Restrictions")
        # Valid login with authorized email
        login_res = client.post(
            "/api/auth/login",
            json={"username": "admin", "email": "admin@fisher.cctv", "password": "admin123"},
        )
        assert login_res.status_code == 200, f"Valid login failed: {login_res.text}"
        login_data = login_res.json()
        token = login_data["token"]
        assert token, "Token must be returned"
        print(" [PASS] Admin login succeeded with authorized email.")

        # Unauthorized email login should be rejected with 403
        bad_login_res = client.post(
            "/api/auth/login",
            json={"username": "admin", "email": "hacker@evil.com", "password": "admin123"},
        )
        assert bad_login_res.status_code == 403, f"Expected 403 for unauthorized email, got {bad_login_res.status_code}"
        print(" [PASS] Unauthorized email rejected with HTTP 403.")

        # 5. USER REGISTRATION ENFORCING EXACTLY 3 AUTHORIZED USERS
        print(" -> Testing 5: User Management Restrictions")
        users_res = client.get("/api/users")
        assert users_res.status_code == 200
        users = users_res.json()
        print(f"        Current registered users: {len(users)}")

        # Attempt to register with unauthorized email
        bad_user_res = client.post(
            "/api/users",
            json={
                "name": "Intruder User",
                "email": "unauthorized@example.com",
                "role": "operator",
            },
        )
        assert bad_user_res.status_code in (400, 403), "Unauthorized email must be rejected by backend"
        print(" [PASS] Registration of unauthorized email address blocked by backend.")


def run_all_tests():
    print("=" * 65)
    print("FISHER AI CCTV — BACKEND VERIFICATION SUITE")
    print("=" * 65)
    test_configuration()
    test_telegram_connection()
    test_database_connection()
    test_contract_endpoints()
    print("\n" + "=" * 65)
    print("ALL BACKEND VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == "__main__":
    run_all_tests()
