import sys
sys.path.insert(0, r'd:\MyProject\Backend')
import app

samples = [
    'Cholesterol 210 mg/dL < 200 mg/dL',
    'Hemoglobin 13.2 g/dL',
    'Total Cholesterol: 210 mg/dL',
    'Hb: 13.2 g/dL',
    'Platelet Count 2.1 Lakh/uL',
    'Glucose 112 mg/dL',
    'Hemoglobin    13.2    g/dL    13.0-17.0\nCholesterol   210     mg/dL   <200\nWBC    7.5    x10^3/uL    4.0-11.0\nTSH    2.1    uIU/mL   0.5-4.5',
    'Blood Pressure 118/76 mmHg',
    'Heart Rate 72 bpm',
]

for s in samples:
    print('---')
    print(s)
    print(app.extract_medical_parameters(s))
