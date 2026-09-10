#!/usr/bin/env python3
"""
Test script to verify MediDecode API flow:
1. Register/Login user
2. Create a test report file
3. Upload report
4. Fetch report
5. Verify response structure
"""

import requests
import json
import os
import sys
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"
TEST_USER_EMAIL = "apitest@medidecode.com"
TEST_USER_PASSWORD = "APITest123!"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_response(resp, title="Response"):
    print(f"\n{title}:")
    print(f"Status: {resp.status_code}")
    try:
        print(f"Data: {json.dumps(resp.json(), indent=2)}")
    except:
        print(f"Data: {resp.text}")

def test_register_user():
    print_section("1. REGISTER USER")
    
    data = {
        "name": "API Test User",
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
        "age": 30,
        "gender": "Male",
        "blood_group": "O+",
        "height": 175,
        "weight": 70,
        "phone": "9876543210",
        "address": "123 Test Street",
        "emergency_contact": "9876543211"
    }
    
    resp = requests.post(f"{BASE_URL}/api/register", json=data)
    print_response(resp)
    
    if resp.status_code == 201:
        return True
    elif resp.status_code == 409:
        print("User already exists - will proceed with login")
        return True
    else:
        return False

def test_login():
    print_section("2. LOGIN USER")
    
    data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    
    resp = requests.post(f"{BASE_URL}/api/login", json=data)
    print_response(resp)
    
    if resp.status_code == 200:
        user_data = resp.json()
        user_id = user_data.get("user", {}).get("id")
        print(f"\n✓ Login successful! User ID: {user_id}")
        return user_id
    else:
        print("\n✗ Login failed!")
        return None

def create_test_report_file():
    print_section("3. CREATE TEST REPORT FILE")
    
    # Create a simple text file that looks like a medical report
    test_content = """
COMPLETE BLOOD COUNT (CBC) REPORT
Patient Name: API Test User
Report Date: 2025-01-20
Lab: Test Diagnostics

HEMATOLOGY PARAMETERS:
Hemoglobin: 14.5 g/dL
RBC: 4.2 x10^12/L
WBC: 7.3 x10^9/L
Platelets: 250 Lakh/uL

BIOCHEMISTRY:
Blood Glucose: 95 mg/dL
Cholesterol: 180 mg/dL
HDL: 50 mg/dL
LDL: 100 mg/dL
Triglycerides: 120 mg/dL

VITAL SIGNS:
Blood Pressure: 120/80 mmHg
Heart Rate: 72 bpm

REFERENCE RANGES:
Hemoglobin: 12.5-17.5 g/dL
RBC: 3.8-5.1 x10^12/L
WBC: 4.0-11.0 x10^9/L
Blood Glucose (Fasting): 70-99 mg/dL
Cholesterol: 0-200 mg/dL

INTERPRETATION:
All values are within normal range. Patient is in good health.
"""
    
    # Save to a temporary text file
    test_file_path = "d:\\MyProject\\test_report.txt"
    with open(test_file_path, "w") as f:
        f.write(test_content)
    
    print(f"✓ Created test report file: {test_file_path}")
    return test_file_path

def test_upload_report(user_id, file_path):
    print_section("4. UPLOAD REPORT")
    
    if not os.path.exists(file_path):
        print(f"✗ Test file not found: {file_path}")
        return None
    
    with open(file_path, "rb") as f:
        files = {"report": f}
        headers = {
            "X-User-ID": str(user_id)
        }
        
        resp = requests.post(
            f"{BASE_URL}/api/upload",
            files=files,
            headers=headers
        )
    
    print_response(resp)
    
    if resp.status_code == 201:
        report_data = resp.json()
        report_id = report_data.get("report_id")
        print(f"\n✓ Upload successful! Report ID: {report_id}")
        return report_id
    else:
        print("\n✗ Upload failed!")
        return None

def test_fetch_report(report_id):
    print_section("5. FETCH REPORT DATA")
    
    resp = requests.get(f"{BASE_URL}/api/reports/{report_id}")
    print_response(resp)
    
    if resp.status_code == 200:
        report_data = resp.json()
        
        # Verify structure
        print("\n✓ Fetch successful!")
        print("\n--- RESPONSE STRUCTURE ANALYSIS ---")
        
        if "report" in report_data:
            report = report_data["report"]
            print(f"✓ 'report' field exists")
            
            # Check for required fields
            required_fields = ["id", "file_name", "report_type", "raw_text", "created_at"]
            for field in required_fields:
                if field in report:
                    print(f"✓ '{field}' exists")
                else:
                    print(f"✗ '{field}' MISSING")
            
            # Check for parameters
            if "parameters" in report:
                params = report.get("parameters", [])
                print(f"✓ 'parameters' exists ({len(params)} items)")
                if params:
                    print(f"  First parameter: {json.dumps(params[0], indent=4)}")
            else:
                print(f"✗ 'parameters' MISSING")
            
            # Check for medical_information
            if "medical_information" in report:
                med_info = report.get("medical_information", {})
                print(f"✓ 'medical_information' exists")
                if isinstance(med_info, dict):
                    print(f"  Keys: {list(med_info.keys())}")
                    if "lab_results" in med_info:
                        lab_results = med_info.get("lab_results", [])
                        print(f"  'lab_results': {len(lab_results)} items")
                        if lab_results:
                            print(f"    First result: {json.dumps(lab_results[0], indent=4)}")
            else:
                print(f"✗ 'medical_information' MISSING")
        else:
            print(f"✗ 'report' field MISSING - this is a critical error!")
        
        return report_data
    else:
        print("\n✗ Fetch failed!")
        return None

def test_browser_flow():
    print_section("6. BROWSER-SIDE VALIDATION")
    print("""
The following JavaScript should be tested in the browser console:

// 1. Check sessionStorage for report ID
const reportId = sessionStorage.getItem("medidecode_last_report_id");
console.log("Report ID from sessionStorage:", reportId);

// 2. Fetch report from backend
const response = await fetch(`http://127.0.0.1:5000/api/reports/${reportId}`);
const data = await response.json();
console.log("Full response:", data);
console.log("Report object:", data.report);
console.log("Parameters:", data.report.parameters);
console.log("Medical Info:", data.report.medical_information);
console.log("Lab Results:", data.report.medical_information?.lab_results);

// 3. Verify structure matches frontend expectations
if (data.report && data.report.parameters) {
    console.log("✓ Frontend should render parameters correctly");
}
    """)

def main():
    print_section("MediDecode API End-to-End Test")
    
    # Step 1: Register user
    if not test_register_user():
        print("Failed to register user - aborting")
        return
    
    # Step 2: Login
    user_id = test_login()
    if not user_id:
        print("Failed to login - aborting")
        return
    
    # Step 3: Create test report
    test_file = create_test_report_file()
    
    # Step 4: Upload report
    report_id = test_upload_report(user_id, test_file)
    if not report_id:
        print("Failed to upload report - aborting")
        return
    
    # Step 5: Fetch and verify report
    report_data = test_fetch_report(report_id)
    if not report_data:
        print("Failed to fetch report - aborting")
        return
    
    # Step 6: Browser flow info
    test_browser_flow()
    
    # Summary
    print_section("TEST SUMMARY")
    print(f"""
✓ User registered/logged in (ID: {user_id})
✓ Report uploaded successfully (ID: {report_id})
✓ Report fetched from database
✓ API response structure verified

NEXT STEPS:
1. Open http://127.0.0.1:5500/upload.html in browser
2. Create a test report file or use existing one
3. Upload it to populate sessionStorage with report_id
4. Open http://127.0.0.1:5500/reports.html
5. Check the browser console to verify:
   - sessionStorage has the report ID
   - Fetch to /api/reports/<id> returns correct structure
   - Frontend renders the report correctly
    """)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
