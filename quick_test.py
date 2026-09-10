#!/usr/bin/env python3
"""
MediDecode Quick Test - Verifies the upload→reports flow works

Run this after:
1. Database is recreated
2. Flask is running on http://127.0.0.1:5000
3. You've logged in and have user_id in localStorage
"""

import requests
import json
import time
import os

BASE_URL = "http://127.0.0.1:5000"

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_result(success, message):
    icon = "✓" if success else "✗"
    print(f"{icon} {message}")

def test_backend_running():
    """Test if Flask backend is running"""
    print_header("TEST 1: Backend Running?")
    try:
        resp = requests.get(f"{BASE_URL}/", timeout=2)
        print_result(True, "Flask backend is running on http://127.0.0.1:5000")
        print(f"  Response: {json.dumps(resp.json())}")
        return True
    except Exception as e:
        print_result(False, f"Flask backend not running: {e}")
        print("\n  Start Flask with: cd Backend && python app.py")
        return False

def register_test_user():
    """Register a test user"""
    print_header("TEST 2: User Registration")
    
    test_email = f"test_{int(time.time())}@example.com"
    user_data = {
        "name": "Test User",
        "email": test_email,
        "password": "TestPass123!",
        "age": 30,
        "gender": "Male"
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/api/register", json=user_data)
        
        if resp.status_code in [201, 409]:  # 409 = already exists
            print_result(True, f"User registered/exists: {test_email}")
            return test_email
        else:
            print_result(False, f"Registration failed: {resp.status_code}")
            print(f"  Response: {json.dumps(resp.json())}")
            return None
    except Exception as e:
        print_result(False, f"Registration error: {e}")
        return None

def login_user(email):
    """Login user and get user_id"""
    print_header("TEST 3: User Login")
    
    login_data = {
        "email": email,
        "password": "TestPass123!"
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/api/login", json=login_data)
        
        if resp.status_code != 200:
            print_result(False, f"Login failed: {resp.status_code}")
            print(f"  Response: {json.dumps(resp.json())}")
            return None
        
        user_data = resp.json()
        user_id = user_data.get("user", {}).get("id")
        
        if not user_id:
            print_result(False, "Login response missing user.id")
            print(f"  Response: {json.dumps(resp.json())}")
            return None
        
        print_result(True, f"Login successful! User ID: {user_id}")
        return user_id
    except Exception as e:
        print_result(False, f"Login error: {e}")
        return None

def upload_test_report(user_id):
    """Upload a test report file"""
    print_header("TEST 4: Report Upload")
    
    # Create test file
    test_content = """
COMPLETE BLOOD COUNT - CBC REPORT
Date: 2025-01-20

PATIENT INFORMATION
Name: Test User
Age: 30

HEMATOLOGY
Hemoglobin (Hb): 14.5 g/dL
Red Blood Cell Count (RBC): 4.2 x10^12/L
White Blood Cell Count (WBC): 7.3 x10^9/L
Platelets: 250 Lakh/uL

BIOCHEMISTRY
Fasting Blood Sugar: 95 mg/dL
Total Cholesterol: 180 mg/dL
HDL: 50 mg/dL
LDL: 100 mg/dL
Triglycerides: 120 mg/dL

VITAL SIGNS
Blood Pressure: 120/80 mmHg
Heart Rate: 72 bpm

INTERPRETATION
All values are within normal ranges. 
Patient is in good health.
"""
    
    test_file = "d:\\MyProject\\test_report_temp.txt"
    
    try:
        # Write test file
        with open(test_file, "w") as f:
            f.write(test_content)
        print(f"  Created test file: {test_file}")
        
        # Upload file
        with open(test_file, "rb") as f:
            files = {"report": f}
            headers = {"X-User-ID": str(user_id)}
            resp = requests.post(f"{BASE_URL}/api/upload", files=files, headers=headers)
        
        if resp.status_code != 201:
            print_result(False, f"Upload failed: {resp.status_code}")
            print(f"  Response: {json.dumps(resp.json())}")
            return None
        
        data = resp.json()
        report_id = data.get("report_id")
        
        if not report_id:
            print_result(False, "Upload succeeded but no report_id returned")
            print(f"  Response: {json.dumps(resp.json())}")
            return None
        
        print_result(True, f"Report uploaded! Report ID: {report_id}")
        print(f"  Response keys: {list(data.keys())}")
        
        # Clean up
        try:
            os.remove(test_file)
        except:
            pass
        
        return report_id
    except Exception as e:
        print_result(False, f"Upload error: {e}")
        return None

def fetch_report(report_id):
    """Fetch the uploaded report"""
    print_header("TEST 5: Fetch Report")
    
    try:
        resp = requests.get(f"{BASE_URL}/api/reports/{report_id}")
        
        if resp.status_code != 200:
            print_result(False, f"Fetch failed: {resp.status_code}")
            print(f"  Response: {json.dumps(resp.json())}")
            return None
        
        data = resp.json()
        
        if "report" not in data:
            print_result(False, "Response missing 'report' field")
            print(f"  Response keys: {list(data.keys())}")
            return None
        
        report = data["report"]
        print_result(True, "Report fetched successfully!")
        
        # Verify required fields
        print("\n  Verifying response structure:")
        required_fields = ["id", "user_id", "file_name", "report_type", "raw_text", "created_at", "parameters", "medical_information"]
        
        missing = []
        for field in required_fields:
            if field in report:
                print(f"    ✓ {field}")
            else:
                print(f"    ✗ {field} MISSING")
                missing.append(field)
        
        if missing:
            print_result(False, f"Missing fields: {missing}")
            return None
        
        print_result(True, "All required fields present!")
        
        # Show sample data
        print("\n  Sample data:")
        print(f"    file_name: {report.get('file_name')}")
        print(f"    report_type: {report.get('report_type')}")
        print(f"    created_at: {report.get('created_at')}")
        print(f"    parameters: {len(report.get('parameters', []))} items")
        print(f"    raw_text length: {len(str(report.get('raw_text', '')))}")
        
        return report
    except Exception as e:
        print_result(False, f"Fetch error: {e}")
        return None

def run_all_tests():
    """Run all tests in sequence"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║        MediDecode Upload → Reports Flow - Test Suite               ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    
    # Test 1: Backend running
    if not test_backend_running():
        print("\n✗ Tests aborted: Backend not running")
        return False
    
    # Test 2: Register user
    email = register_test_user()
    if not email:
        print("\n✗ Tests aborted: Registration failed")
        return False
    
    # Test 3: Login
    user_id = login_user(email)
    if not user_id:
        print("\n✗ Tests aborted: Login failed")
        return False
    
    # Test 4: Upload report
    report_id = upload_test_report(user_id)
    if not report_id:
        print("\n✗ Tests aborted: Upload failed")
        return False
    
    # Test 5: Fetch report
    report = fetch_report(report_id)
    if not report:
        print("\n✗ Tests aborted: Fetch failed")
        return False
    
    # Success!
    print_header("✓ ALL TESTS PASSED!")
    print("""
The entire upload → reports flow is working correctly!

NEXT: Test in browser
1. Open http://127.0.0.1:5500/login.html
2. Register/login with your test user
3. Go to http://127.0.0.1:5500/upload.html
4. Upload a real medical report (PDF/JPG/PNG)
5. You should be redirected to reports.html
6. The report should display with:
   - File name
   - Upload date
   - Report type
   - Medical parameters (if text was parsed)
   - Raw extracted text

Check browser console (F12) for any errors.
""")
    return True

if __name__ == "__main__":
    try:
        success = run_all_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
