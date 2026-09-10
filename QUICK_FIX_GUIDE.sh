#!/bin/bash
# MediDecode - Quick Fix Guide
# Run these commands in order to fix the end-to-end report flow

echo "=== MediDecode API Fix Sequence ==="
echo ""
echo "STEP 1: Stop Flask Server"
echo "Command: Get-Process python | Stop-Process -Force"
echo ""

echo "STEP 2: Recreate Database with Fixed Schema"
echo "Command: cd d:\MyProject && Get-Content Datasase\database.sql | mysql -u root -p@Moksha29"
echo ""

echo "STEP 3: Verify Backend Files"
echo "✓ Check that Backend/app.py contains the updated /api/reports/<int:report_id> endpoint"
echo "  Lines 861-902 should show:"
echo "    - cursor.execute() with raw_text, created_at fields"
echo "    - report['parameters'] = extract_medical_parameters()"
echo "    - report['medical_information'] = extract_medical_information()"
echo "    - return jsonify({'report': report}), 200"
echo ""

echo "STEP 4: Start Flask Server"
echo "Command: cd d:\MyProject\Backend && python app.py"
echo "Expected: 'Running on http://127.0.0.1:5000'"
echo ""

echo "STEP 5: Open Frontend Upload"
echo "URL: http://127.0.0.1:5500/upload.html"
echo "Action: Upload a PDF, JPG, or PNG medical report"
echo ""

echo "STEP 6: Verify sessionStorage (Browser Console)"
echo "Command: sessionStorage.getItem('medidecode_last_report_id')"
echo "Expected: A number like 1, 2, 3, etc."
echo ""

echo "STEP 7: Open Reports Page"
echo "URL: http://127.0.0.1:5500/reports.html"
echo "Expected: Should display:"
echo "  - Report filename"
echo "  - Upload date"
echo "  - Medical parameters table"
echo "  - Extracted report text"
echo ""

echo "STEP 8: Verify in Browser Console"
echo "Commands to run:"
echo '  const rid = sessionStorage.getItem("medidecode_last_report_id");'
echo '  const resp = await fetch(`http://127.0.0.1:5000/api/reports/${rid}`);'
echo '  const data = await resp.json();'
echo '  console.log("Parameters:", data.report.parameters);'
echo '  console.log("Medical Info:", data.report.medical_information);'
echo ""

echo "STEP 9: Troubleshooting"
echo "  If 'No report ID found' -> Upload a report first"
echo "  If 'Report not found' (404) -> Check report_id matches in DB"
echo "  If 'No structured values' -> Check Flask is returning parameters array"
echo "  If blank/errors -> Press F12 in browser to see exact error in console"
echo ""

echo "✓ All steps complete!"
echo ""
echo "Expected final result:"
echo "  - Upload page stores report_id in sessionStorage"
echo "  - Reports page reads report_id from sessionStorage"
echo "  - Frontend fetches /api/reports/<id> from Flask"
echo "  - Backend returns report data with parameters and medical_information"
echo "  - Frontend displays all data in table and text sections"
