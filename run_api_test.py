#!/usr/bin/env python3
"""
MediDecode API Test Script
Tests the complete upload -> fetch flow
"""

import requests
import json
import sys
import time

BASE_URL = "http://127.0.0.1:5000"
TEST_EMAIL = f"test_user_{int(time.time())}@test.com"
TEST_PASSWORD = "TestPassword123!"

def test_api():
    print("\n" + "="*70)
    print("MediDecode API Flow Test")
    print("="*70)
    
    # 1. Register user
    print("\n[1] Testing POST /api/register")
    user_data = {
        "name": "Test User",
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "age": 30,
        "gender": "Male"
    }
    resp = requests.post(f"{BASE_URL}/api/register", json=user_data)
    print(f"Status: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)}")
    
    if resp.status_code not in [201, 409]:
        print("✗ Registration failed!")
        return False
    
    # 2. Login
    print("\n[2] Testing POST /api/login")
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    resp = requests.post(f"{BASE_URL}/api/login", json=login_data)
    print(f"Status: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)}")
    
    if resp.status_code != 200:
        print("✗ Login failed!")
        return False
    
    user_id = resp.json()["user"]["id"]
    print(f"✓ Logged in as user ID: {user_id}")
    
    # 3. Create test report file
    print("\n[3] Creating test report file")
    test_report_content = """
COMPLETE BLOOD COUNT (CBC) REPORT
Patient: Test User
Date: 2025-01-20

Hemoglobin: 14.5 g/dL
RBC: 4.2 x10^12/L
WBC: 7.3 x10^9/L
Platelets: 250 Lakh/uL
Blood Glucose: 95 mg/dL

Blood Pressure: 120/80 mmHg
Heart Rate: 72 bpm

All values normal.
"""
    
    test_file_path = "d:\\MyProject\\test_report_temp.txt"
    with open(test_file_path, "w") as f:
        f.write(test_report_content)
    print(f"✓ Created test file: {test_file_path}")
    
    # 4. Upload report
    print("\n[4] Testing POST /api/upload")
    with open(test_file_path, "rb") as f:
        files = {"report": f}
        headers = {"X-User-ID": str(user_id)}
        resp = requests.post(f"{BASE_URL}/api/upload", files=files, headers=headers)
    
    print(f"Status: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)}")
    
    if resp.status_code != 201:
        print("✗ Upload failed!")
        return False
    
    report_id = resp.json().get("report_id")
    print(f"✓ Upload successful! Report ID: {report_id}")
    
    if not report_id:
        print("✗ No report_id in response!")
        return False
    
    # 5. Fetch report
    print(f"\n[5] Testing GET /api/reports/{report_id}")
    resp = requests.get(f"{BASE_URL}/api/reports/{report_id}")
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print("✗ Fetch failed!")
        print(f"Response: {json.dumps(resp.json(), indent=2)}")
        return False
    
    report_data = resp.json()
    print(f"Response structure:\n{json.dumps(report_data, indent=2)[:500]}...")
    
    # 6. Verify response structure
    print("\n[6] Verifying response structure")
    
    if "report" not in report_data:
        print("✗ CRITICAL: 'report' key missing from response!")
        print(f"Keys available: {list(report_data.keys())}")
        return False
    
    report = report_data["report"]
    required_fields = ["id", "user_id", "file_name", "report_type", "raw_text", "created_at", "parameters", "medical_information"]
    
    print("\nChecking required fields:")
    missing = []
    for field in required_fields:
        if field in report:
            print(f"  ✓ {field}: present")
        else:
            print(f"  ✗ {field}: MISSING")
            missing.append(field)
    
    if missing:
        print(f"\n✗ Missing fields: {missing}")
        print(f"Available fields: {list(report.keys())}")
        return False
    
    # 7. Verify parameters structure
    print("\n[7] Checking parameters structure")
    params = report.get("parameters", [])
    print(f"  Parameters count: {len(params)}")
    if params:
        print(f"  First parameter: {json.dumps(params[0], indent=2)}")
    
    # 8. Verify medical_information structure  
    print("\n[8] Checking medical_information structure")
    med_info = report.get("medical_information", {})
    print(f"  Keys: {list(med_info.keys())}")
    if "lab_results" in med_info:
        print(f"  lab_results count: {len(med_info.get('lab_results', []))}")
    
    print("\n" + "="*70)
    print("✓ ALL TESTS PASSED!")
    print("="*70)
    print(f"""
SUMMARY:
- User registered and logged in (ID: {user_id})
- Report uploaded successfully (ID: {report_id})
- Report fetched from backend
- Response structure verified
- All required fields present

The flow is working correctly!
""")
    
    return True

if __name__ == "__main__":
    try:
        success = test_api()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
