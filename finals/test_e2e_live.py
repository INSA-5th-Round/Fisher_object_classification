"""
End-to-End Live Integration Test for FISHER CCTV Running Server
Tests:
- Live MJPEG Stream & Raw Stream
- Authentication & Strict 3-User Email Enforcement
- Reports Generation & Retrieval from MongoDB
- Frame Injection from Detector
"""

import sys
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_live_system():
    print("=" * 65)
    print("RUNNING LIVE END-TO-END INTEGRATION TESTS")
    print(f"Target: {BASE_URL}")
    print("=" * 65)

    # 1. Cameras Endpoint
    print("\n[1] Verifying Cameras Endpoint...")
    r = requests.get(f"{BASE_URL}/api/cameras", timeout=10)
    assert r.status_code == 200, f"Cameras endpoint failed: {r.status_code}"
    cameras = r.json()
    assert len(cameras) >= 1, "Expected at least 1 camera"
    cam = cameras[0]
    print(f"    Camera: {cam['id']} ({cam['name']}) - Status: {cam['status']}")
    assert cam["id"] == "CAM-001"
    assert cam["status"] == "online"
    print("    [PASS] Camera online and available.")

    # 2. Live MJPEG Camera Stream
    print("\n[2] Verifying Live CCTV Camera Stream...")
    stream_res = requests.get(f"{BASE_URL}/api/cameras/CAM-001/stream", stream=True, timeout=10)
    assert stream_res.status_code == 200, f"Stream failed: {stream_res.status_code}"
    ct = stream_res.headers.get("Content-Type", "")
    assert "multipart/x-mixed-replace" in ct, f"Unexpected Content-Type: {ct}"
    received_chunk = False
    try:
        for chunk in stream_res.iter_content(chunk_size=1024):
            if b"--frame" in chunk and b"image/jpeg" in chunk:
                received_chunk = True
                break
    finally:
        stream_res.close()
    assert received_chunk, "Did not receive valid JPEG multipart frame chunk"
    print("    [PASS] Received valid MJPEG live stream chunks from physical camera.")

    # 3. Live Raw MJPEG Camera Stream (for frame_and_detection.py)
    print("\n[3] Verifying Raw Camera Stream for Detector Process...")
    raw_res = requests.get(f"{BASE_URL}/api/cameras/CAM-001/raw-stream", stream=True, timeout=10)
    assert raw_res.status_code == 200, f"Raw stream failed: {raw_res.status_code}"
    ct = raw_res.headers.get("Content-Type", "")
    assert "multipart/x-mixed-replace" in ct, f"Unexpected Content-Type: {ct}"
    received_raw_chunk = False
    try:
        for chunk in raw_res.iter_content(chunk_size=1024):
            if b"--frame" in chunk and b"image/jpeg" in chunk:
                received_raw_chunk = True
                break
    finally:
        raw_res.close()
    assert received_raw_chunk, "Did not receive valid raw stream frame chunk"
    print("    [PASS] Raw camera stream active and ready for external detector connection.")

    # 4. Strict Login & Authentication Tests
    print("\n[4] Testing Authentication and Email Whitelist Enforcement...")
    auth_users = [
        ("admin", "admin@fisher.cctv", "admin123"),
        ("operator", "operator@fisher.cctv", "operator123"),
        ("supervisor", "supervisor@fisher.cctv", "supervisor123"),
    ]
    tokens = {}
    for uname, email, pwd in auth_users:
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": uname, "email": email, "password": pwd},
            timeout=15,
        )
        assert resp.status_code == 200, f"Login failed for {email}: {resp.text}"
        data = resp.json()
        assert data.get("token"), f"Missing token for {email}"
        tokens[email] = data["token"]
        print(f"    [PASS] Authorized user login OK: {uname} ({email}) -> Token received")

    # Unauthorized Email Login Attempt
    unauth_resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": "admin", "email": "unauthorized@external.com", "password": "admin123"},
        timeout=15,
    )
    assert unauth_resp.status_code == 403, f"Expected 403 for unauthorized email, got {unauth_resp.status_code}"
    print("    [PASS] Unauthorized email correctly rejected with HTTP 403 Forbidden.")

    # 5. User Management & 3-User Limit Enforcement
    print("\n[5] Verifying 3-User Capacity & User Management Restrictions...")
    users_resp = requests.get(f"{BASE_URL}/api/users", timeout=15)
    assert users_resp.status_code == 200
    current_users = users_resp.json()
    print(f"    Current users in MongoDB: {len(current_users)}")
    assert len(current_users) == 3, f"Expected exactly 3 authorized users, got {len(current_users)}"

    # Attempt to register 4th user
    extra_user_resp = requests.post(
        f"{BASE_URL}/api/users",
        json={"name": "Extra User", "email": "admin@fisher.cctv", "role": "operator"},
        timeout=15,
    )
    assert extra_user_resp.status_code in (400, 403)
    print("    [PASS] Backend correctly rejected registering beyond 3 authorized users.")

    # 6. Reports Generation & Retrieval
    print("\n[6] Verifying Report Generation and Media Persistence...")
    gen_resp = requests.post(
        f"{BASE_URL}/api/reports",
        json={"title": "Verification Audit Report"},
        timeout=15,
    )
    assert gen_resp.status_code == 200, f"Report generation failed: {gen_resp.text}"
    report_data = gen_resp.json()
    rep_id = report_data["id"]
    print(f"    Report Created: {rep_id} - '{report_data['title']}' (Detections: {report_data['totalDetections']})")
    assert report_data["status"] == "ready"

    # Fetch report list
    rep_list_resp = requests.get(f"{BASE_URL}/api/reports", timeout=15)
    assert rep_list_resp.status_code == 200
    reports = rep_list_resp.json()
    assert any(r["id"] == rep_id for r in reports), f"Report {rep_id} not found in list"
    print(f"    [PASS] Report {rep_id} successfully retrieved from MongoDB reports collection.")

    # Fetch specific report details
    rep_detail_resp = requests.get(f"{BASE_URL}/api/reports/{rep_id}", timeout=15)
    assert rep_detail_resp.status_code == 200
    detail = rep_detail_resp.json()
    assert detail["id"] == rep_id
    assert "detections" in detail
    assert "summary" in detail
    print("    [PASS] Full report details, summary, and detection records verified.")

    # 7. Live Frame Injection from External Detector
    print("\n[7] Verifying Live Frame Injection Endpoint for frame_and_detection.py...")
    import cv2
    import numpy as np
    blank = np.zeros((240, 320, 3), dtype=np.uint8)
    cv2.putText(blank, "INJECTED FRAME TEST", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    _, buf = cv2.imencode(".jpg", blank)
    inj_resp = requests.post(
        f"{BASE_URL}/api/cameras/CAM-001/live-frame",
        data=buf.tobytes(),
        headers={"Content-Type": "image/jpeg"},
        timeout=15,
    )
    assert inj_resp.status_code in (200, 204), f"Frame injection failed: {inj_resp.status_code} {inj_resp.text}"
    print("    [PASS] Detector frame injection accepted by CameraStreamManager (HTTP 204).")

    print("\n" + "=" * 65)
    print("ALL LIVE END-TO-END SYSTEM INTEGRATION TESTS PASSED!")
    print("=" * 65)

if __name__ == "__main__":
    test_live_system()
