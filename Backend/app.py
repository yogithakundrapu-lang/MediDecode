from flask import Flask, jsonify, request
from flask import send_from_directory
from flask_cors import CORS
import mysql.connector
import bcrypt
import os
import uuid
import re
import requests
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image, ImageOps, ImageFilter
import pymupdf
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
FRONTEND_DIR = os.path.abspath(
	os.path.join(os.path.dirname(__file__), "..", "frontend")
)
app = Flask(
	__name__,
	static_folder=FRONTEND_DIR,
	static_url_path=""
)
CORS(app)
app.config["UPLOAD_FOLDER"] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "uploads"
)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 10 * 1024 * 1024
# ============================================================
# LANGUAGE SUPPORT
# ============================================================

SUPPORTED_LANGUAGES = {"en", "te", "hi"}


def get_requested_language():
    """
    Get the language selected by the frontend.

    Priority:
    1. X-Language header
    2. ?lang= query parameter
    3. English by default
    """
    language = (
        request.headers.get("X-Language")
        or request.args.get("lang")
        or "en"
    ).lower().strip()

    if language not in SUPPORTED_LANGUAGES:
        language = "en"

    return language


PARAMETER_TRANSLATIONS = {
    "en": {
        "Hemoglobin": "Hemoglobin",
        "RBC": "RBC",
        "WBC": "WBC",
        "Platelets": "Platelets",
        "Blood Sugar": "Blood Sugar",
        "Fasting Blood Sugar": "Fasting Blood Sugar",
        "Glucose": "Glucose",
        "Cholesterol": "Cholesterol",
        "HDL": "HDL",
        "LDL": "LDL",
        "Triglycerides": "Triglycerides",
        "Vitamin D": "Vitamin D",
        "Vitamin B12": "Vitamin B12",
        "TSH": "TSH",
        "Creatinine": "Creatinine",
        "Urea": "Urea",
        "Uric Acid": "Uric Acid",
        "ALT": "ALT",
        "AST": "AST",
        "Bilirubin": "Bilirubin",
        "Calcium": "Calcium",
        "Sodium": "Sodium",
        "Potassium": "Potassium",
        "Blood Pressure": "Blood Pressure",
        "Heart Rate": "Heart Rate",
    },

    "te": {
        "Hemoglobin": "హీమోగ్లోబిన్",
        "RBC": "RBC",
        "WBC": "WBC",
        "Platelets": "ప్లేట్‌లెట్స్",
        "Blood Sugar": "బ్లడ్ షుగర్",
        "Fasting Blood Sugar": "ఫాస్టింగ్ బ్లడ్ షుగర్",
        "Glucose": "గ్లూకోజ్",
        "Cholesterol": "కొలెస్ట్రాల్",
        "HDL": "HDL",
        "LDL": "LDL",
        "Triglycerides": "ట్రైగ్లిజరైడ్స్",
        "Vitamin D": "విటమిన్ D",
        "Vitamin B12": "విటమిన్ B12",
        "TSH": "TSH",
        "Creatinine": "క్రియాటినిన్",
        "Urea": "యూరియా",
        "Uric Acid": "యూరిక్ యాసిడ్",
        "ALT": "ALT",
        "AST": "AST",
        "Bilirubin": "బిలిరుబిన్",
        "Calcium": "కాల్షియం",
        "Sodium": "సోడియం",
        "Potassium": "పొటాషియం",
        "Blood Pressure": "రక్తపోటు",
        "Heart Rate": "హృదయ స్పందన రేటు",
    },

    "hi": {
        "Hemoglobin": "हीमोग्लोबिन",
        "RBC": "RBC",
        "WBC": "WBC",
        "Platelets": "प्लेटलेट्स",
        "Blood Sugar": "ब्लड शुगर",
        "Fasting Blood Sugar": "फास्टिंग ब्लड शुगर",
        "Glucose": "ग्लूकोज़",
        "Cholesterol": "कोलेस्ट्रॉल",
        "HDL": "HDL",
        "LDL": "LDL",
        "Triglycerides": "ट्राइग्लिसराइड्स",
        "Vitamin D": "विटामिन D",
        "Vitamin B12": "विटामिन B12",
        "TSH": "TSH",
        "Creatinine": "क्रिएटिनिन",
        "Urea": "यूरिया",
        "Uric Acid": "यूरिक एसिड",
        "ALT": "ALT",
        "AST": "AST",
        "Bilirubin": "बिलीरुबिन",
        "Calcium": "कैल्शियम",
        "Sodium": "सोडियम",
        "Potassium": "पोटैशियम",
        "Blood Pressure": "ब्लड प्रेशर",
        "Heart Rate": "हृदय गति",
    }
}


STATUS_TRANSLATIONS = {
    "en": {
        "Normal": "Normal",
        "Low": "Low",
        "Slightly Low": "Slightly Low",
        "High": "High",
        "Slightly High": "Slightly High",
        "Unknown": "Unknown",
        "NORMAL": "NORMAL",
        "LOW": "LOW",
        "HIGH": "HIGH",
    },

    "te": {
        "Normal": "సాధారణం",
        "Low": "తక్కువ",
        "Slightly Low": "కొద్దిగా తక్కువ",
        "High": "ఎక్కువ",
        "Slightly High": "కొద్దిగా ఎక్కువ",
        "Unknown": "తెలియదు",
        "NORMAL": "సాధారణం",
        "LOW": "తక్కువ",
        "HIGH": "ఎక్కువ",
    },

    "hi": {
        "Normal": "सामान्य",
        "Low": "कम",
        "Slightly Low": "थोड़ा कम",
        "High": "अधिक",
        "Slightly High": "थोड़ा अधिक",
        "Unknown": "अज्ञात",
        "NORMAL": "सामान्य",
        "LOW": "कम",
        "HIGH": "अधिक",
    }
}


PARAMETER_MEANINGS = {
    "en": {
        "Hemoglobin": "Hemoglobin is a protein in red blood cells that carries oxygen throughout your body.",
        "RBC": "RBCs are red blood cells that carry oxygen from your lungs to the rest of your body.",
        "WBC": "WBCs are white blood cells that help your body fight infections and other illnesses.",
        "Platelets": "Platelets help your blood form clots and stop bleeding.",
        "Fasting Blood Sugar": "Fasting blood sugar measures the amount of glucose in your blood after not eating for several hours.",
        "Blood Sugar": "Blood sugar measures the amount of glucose in your blood and helps show how your body is controlling sugar.",
        "Glucose": "Glucose is the main type of sugar in your blood and provides energy to your body's cells.",
        "Cholesterol": "Cholesterol is a fatty substance in your blood. Your body needs some cholesterol, but too much can increase heart and blood vessel risks.",
        "HDL": "HDL is often called the 'good' cholesterol because it helps carry excess cholesterol away from the blood vessels.",
        "LDL": "LDL is often called the 'bad' cholesterol because high levels can contribute to cholesterol buildup in blood vessels.",
        "Triglycerides": "Triglycerides are a type of fat in your blood. High levels can be associated with increased heart health risk.",
        "Vitamin D": "Vitamin D helps your body absorb calcium and supports healthy bones and muscles.",
        "Vitamin B12": "Vitamin B12 helps make healthy red blood cells and supports normal nerve function.",
        "TSH": "TSH is a hormone that helps control how your thyroid gland works.",
        "Creatinine": "Creatinine is a waste product produced by muscles. The kidneys normally remove it from the blood.",
        "Urea": "Urea is a waste product produced when the body breaks down proteins. The kidneys normally remove it from the blood.",
        "Uric Acid": "Uric acid is produced when the body breaks down certain substances called purines. The kidneys normally remove it from the body.",
        "ALT": "ALT is an enzyme found mainly in the liver. It is commonly measured to help assess liver health.",
        "AST": "AST is an enzyme found in the liver and other tissues. It is commonly measured when checking for tissue or liver problems.",
        "Bilirubin": "Bilirubin is a yellow substance produced when old red blood cells are broken down. The liver helps process and remove it.",
        "Calcium": "Calcium is an important mineral needed for healthy bones, muscles and normal nerve function.",
        "Sodium": "Sodium is an electrolyte that helps control fluid balance and supports normal nerve and muscle function.",
        "Potassium": "Potassium is an electrolyte that is important for normal heart, nerve and muscle function.",
        "Blood Pressure": "Blood pressure shows the force of blood pushing against the walls of your blood vessels.",
        "Heart Rate": "Heart rate is the number of times your heart beats in one minute."
    },
    "te": {
        "Hemoglobin": "హీమోగ్లోబిన్ అనేది ఎర్ర రక్త కణాలలో ఉండే ప్రోటీన్, ఇది మీ శరీరమంతా ఆక్సిజన్‌ను తీసుకువెళుతుంది.",
        "RBC": "RBCలు ఎర్ర రక్త కణాలు, ఇవి మీ ఊపిరితిత్తుల నుంచి మీ శరీరంలోని ఇతర కణాలకు ఆక్సిజన్‌ను తీసుకువెళతాయి.",
        "WBC": "WBCలు తెల్ల రక్త కణాలు, ఇవి మీ శరీరాన్ని ఇన్‌ఫెక్షన్ మరియు ఇతర వ్యాధుల నుంచి రక్షిస్తాయి.",
        "Platelets": "ప్లేట్‌లెట్స్ రక్తంపు బయటకు వెళ్లకుండా బుడగలు ఏర్పరచి రక్తం అతుక్కుపోకుండా సహాయపడతాయి.",
        "Fasting Blood Sugar": "ఫాస్టింగ్ బ్లడ్ షుగర్ మీ శరీరం ఒకటిన్నర గంటల పాటు తినకుండానే ఉన్నప్పుడు రక్తంలో గ్లూకోజ్ పరిమాణాన్ని చూపుతుంది.",
        "Blood Sugar": "బ్లడ్ షుగర్ మీ రక్తంలో గ్లూకోజ్ మొత్తాన్ని సూచిస్తుంది మరియు మీ శరీరం చక్కగా షుగర్‌ను నియంత్రిస్తున్నదో లేదో అర్థం చేసుకోవడానికి సహాయపడుతుంది.",
        "Glucose": "గ్లూకోజ్ మీ రక్తంలో ఉన్న ప్రధాన శక్తి పరిమాణం మరియు మీ శరీర కణాలకు శక్తిని అందిస్తుంది.",
        "Cholesterol": "కొలెస్ట్రాల్ మీ రక్తంలో ఉండే కొవ్వు పదార్థం. మీ శరీరం కొంత కొలెస్ట్రాల్‌ను అవసరపడుతుంది, కానీ ఎక్కువగా ఉన్నప్పుడు గుండె మరియు రక్త నాళాల సమస్యలు పెరగవచ్చు.",
        "HDL": "HDL‌ను సాధారణంగా 'ఉత్తమ' కొలెస్ట్రాల్ అని పిలుస్తారు, ఎందుకంటే ఇది మిగిలిన కొలెస్ట్రాల్‌ను రక్త నాళాల నుండి బయటకు తీసుకెళుతుంది.",
        "LDL": "LDL‌ను సాధారణంగా 'మంచిది కాని' కొలెస్ట్రాల్ అని పిలుస్తారు, ఎందుకంటే ఎక్కువగా ఉన్నప్పుడు రక్త నాళాల్లో కొలెస్ట్రాల్ పేరుకుపోవచ్చు.",
        "Triglycerides": "ట్రైగ్లిజరైడ్స్ మీ రక్తంలో ఉండే కొవ్వు రకం. ఎక్కువగా ఉన్నప్పుడు గుండె ఆరోగ్యానికి ప్రమాదం పెరగవచ్చు.",
        "Vitamin D": "విటమిన్ D మీ శరీరానికి కాల్షియంను శోషించడంలో సహాయమని మరియు బలమైన ఎముకలు, ప músculosకు మద్దతు ఇస్తుంది.",
        "Vitamin B12": "విటమిన్ B12 ఆరోగ్యకరమైన ఎర్ర రక్త కణాల తయారీ మరియు సాధారణ నరాల పనితీరుకు సహాయపడుతుంది.",
        "TSH": "TSH అనేది థైరాయిడ్ గ్రంధం పని ఎలా జరుగుతుందో నియంత్రించడంలో సహాయపడే హార్మోన్.",
        "Creatinine": "క్రియాటినిన్ అనేది కండరాలతో తయారయ్యే వ్యర్థ పదార్థం. శరీరంలో ఉన్న ఈ పదార్థాన్ని కాలేయం కాదు, కిడ్నీలు సాధారణంగా తొలగిస్తాయి.",
        "Urea": "యూరియా అనేది ప్రోటీన్ల విచ్ఛిన్నం వల్ల ఏర్పడే వ్యర్థ పదార్థం. కిడ్నీలు దీనిని సాధారణంగా రక్తం నుండి తొలగిస్తాయి.",
        "Uric Acid": "యూరిక్ యాసిడ్ అనేది ప్యూరిన్‌లను విచ్ఛిన్నం చేసినప్పుడు ఏర్పడే పదార్థం. కిడ్నీలు దీనిని సాధారణంగా శరీరం నుండి తొలగిస్తాయి.",
        "ALT": "ALT అనేది ముఖ్యంగా గుణ్ణం (లివర్) లో ఉండే ఎంజైమ్, ఇది లివర్ ఆరోగ్యాన్ని అంచనా వేయడానికి ఉపయోగిస్తారు.",
        "AST": "AST అనేది లివర్ మరియు ఇతర కణజాలాలలో ఉండే ఎంజైమ్, ఇది కణజాల లేదా లివర్ సమస్యలను పరీక్షించడంలో సహాయపడుతుంది.",
        "Bilirubin": "బిలిరుబిన్ అనేది పాత ఎర్ర రక్త కణాల విచ్ఛిన్నం వల్ల ఏర్పడే పసుపు పదార్థం. లివర్ దీనిని ప్రాసెస్ చేసి తొలగిస్తుంది.",
        "Calcium": "కాల్షియం అనేది బలమైన ఎముకలు, కండరాలు మరియు సాధారణ నరాల పనితీరుకు అవసరమైన ముఖ్యమైన ఖనిజం.",
        "Sodium": "సోడియం అనేది ద్రవ సమతుల్యతను నియంత్రించడంలో సహాయపడే ఎలక్ట్రోలైట్, అలాగే సాధారణ నరాలు మరియు కండరాల పనితీరును మద్దతు ఇస్తుంది.",
        "Potassium": "పొటాషియం అనేది సాధారణ గుండె, నరాలు మరియు కండరాల పనితీరుకు ముఖ్యమైన ఎలక్ట్రోలైట్.",
        "Blood Pressure": "రక్తపోటు అనేది రక్తం రక్త నాళాల గోడలపై ఎంత బలంగా ఒత్తిడిని చూపిస్తుందో తెలియజేస్తుంది.",
        "Heart Rate": "హృదయ స్పందన రేటు అనేది మీ గుండె ఒక నిమిషంలో ఎన్ని సార్లు కొట్టుకుంటుందో సూచిస్తుంది."
    },
    "hi": {
        "Hemoglobin": "हीमोग्लोबिन लाल रक्त कोशिकाओं में पाया जाने वाला एक प्रोटीन है जो पूरे शरीर में ऑक्सीजन ले जाता है।",
        "RBC": "RBC लाल रक्त कोशिकाएँ होती हैं जो आपके फेफड़ों से शरीर के बाकी हिस्सों तक ऑक्सीजन ले जाती हैं।",
        "WBC": "WBC सफेद रक्त कोशिकाएँ होती हैं जो आपके शरीर को संक्रमण और अन्य बीमारियों से लड़ने में मदद करती हैं।",
        "Platelets": "प्लेटलेट्स आपके रक्त में थक्का बनाकर bleeding बंद करने में मदद करते हैं।",
        "Fasting Blood Sugar": "फास्टिंग ब्लड शुगर आपके शरीर के कई घंटे तक भोजन न लेने के बाद रक्त में ग्लूकोज़ की मात्रा को मापता है।",
        "Blood Sugar": "ब्लड शुगर आपके रक्त में ग्लूकोज़ की मात्रा को बताता है और दिखाता है कि आपका शरीर शुगर को सही तरीके से नियंत्रित कर रहा है या नहीं।",
        "Glucose": "ग्लूकोज़ आपके रक्त में मौजूद मुख्य शर्करा है और शरीर की कोशिकाओं को ऊर्जा देता है।",
        "Cholesterol": "कोलेस्ट्रॉल आपके रक्त में मौजूद एक वसा पदार्थ है। आपके शरीर को कुछ कोलेस्ट्रॉल की जरूरत होती है, लेकिन बहुत अधिक होने पर हृदय और रक्त नलिकाओं के जोखिम बढ़ सकते हैं।",
        "HDL": "HDL को अक्सर 'अच्छा' कोलेस्ट्रॉल कहा जाता है क्योंकि यह अतिरिक्त कोलेस्ट्रॉल को रक्त नलिकाओं से बाहर ले जाने में मदद करता है।",
        "LDL": "LDL को अक्सर 'बुरा' कोलेस्ट्रॉल कहा जाता है क्योंकि इसकी अधिक मात्रा रक्त नलिकाओं में कोलेस्ट्रॉल जमा होने में योगदान दे सकती है।",
        "Triglycerides": "ट्राइग्लिसराइड्स आपके रक्त में मौजूद एक प्रकार की वसा हैं। अधिक मात्रा होने पर हृदय स्वास्थ्य जोखिम बढ़ सकता है।",
        "Vitamin D": "विटामिन D आपके शरीर को कैल्शियम अवशोषित करने में मदद करता है और स्वस्थ हड्डियों तथा मांसपेशियों का समर्थन करता है।",
        "Vitamin B12": "विटामिन B12 स्वस्थ लाल रक्त कोशिकाओं के निर्माण और सामान्य तंत्रिका कार्य में मदद करता है।",
        "TSH": "TSH एक हार्मोन है जो आपके थायरॉयड ग्रंथि के काम को नियंत्रित करने में मदद करता है।",
        "Creatinine": "क्रिएटिनिन मांसपेशियों द्वारा उत्पादित एक अपशिष्ट पदार्थ है। किडनी इसे सामान्यतः रक्त से निकाल देती हैं।",
        "Urea": "यूरिया प्रोटीन के टूटने के कारण बनने वाला एक अपशिष्ट पदार्थ है। किडनी इसे सामान्यतः रक्त से निकाल देती हैं।",
        "Uric Acid": "यूरिक एसिड एक ऐसा पदार्थ है जो प्यूरिन के टूटने से बनता है। किडनी इसे सामान्यतः शरीर से बाहर निकाल देती हैं।",
        "ALT": "ALT मुख्य रूप से यकृत में पाया जाने वाला एक एंजाइम है। इसका उपयोग यकृत स्वास्थ्य का मूल्यांकन करने में किया जाता है।",
        "AST": "AST यकृत और अन्य ऊतकों में पाया जाने वाला एक एंजाइम है। इसकी मदद से ऊतक या यकृत की समस्याओं का परीक्षण किया जाता है।",
        "Bilirubin": "बिलीरुबिन पुरानी लाल रक्त कोशिकाओं के अपघटन के दौरान बनने वाली पीली पदार्थ है। यकृत इसे संसाधित करके हटाता है।",
        "Calcium": "कैल्शियम स्वस्थ हड्डियों, मांसपेशियों और सामान्य तंत्रिका कार्य के लिए आवश्यक एक महत्वपूर्ण खनिज है।",
        "Sodium": "सोडियम एक इलेक्ट्रोलाइट है जोfluid balance को नियंत्रित करने और सामान्य तंत्रिका तथा मांसपेशियों के कार्य में मदद करता है।",
        "Potassium": "पोटैशियम एक इलेक्ट्रोलाइट है जो सामान्य हृदय, तंत्रिका और मांसपेशियों के कार्य के लिए महत्वपूर्ण है।",
        "Blood Pressure": "ब्लड प्रेशर यह बताता है कि रक्त आपके रक्त नलिकाओं की दीवारों पर कितना दबाव डाल रहा है।",
        "Heart Rate": "हृदय गति यह बताती है कि आपका दिल एक मिनट में कितनी बार धड़कता है।"
    }
}


def translate_parameters(parameters, language):
    """
    Translate parameter names, meanings and risk/status.
    Numeric values and units are NEVER changed.
    """
    if language == "en":
        return parameters

    translated = []

    for parameter in parameters:
        item = parameter.copy()

        original_name = item.get("name", "")
        original_risk = item.get("risk", "Unknown")

        item["name"] = PARAMETER_TRANSLATIONS.get(
            language, {}
        ).get(
            original_name,
            original_name
        )

        item["risk"] = STATUS_TRANSLATIONS.get(
            language, {}
        ).get(
            original_risk,
            original_risk
        )

        translated_meaning = PARAMETER_MEANINGS.get(
            language,
            PARAMETER_MEANINGS["en"]
        ).get(
            original_name,
            item.get("meaning", PARAMETER_MEANINGS["en"].get(original_name, ""))
        )

        item["meaning"] = translated_meaning

        translated.append(item)

    return translated


def translate_medical_information(information, language):
    """
    Translate structured medical information while preserving
    patient values, numbers and units.
    """
    if language == "en":
        return information

    translated = {}

    for key, value in information.items():

        if key == "patient":
            translated["patient"] = value.copy()

        elif key == "medical_history":
            translated["medical_history"] = value

        elif key == "allergies":
            translated["allergies"] = value

        elif key == "medications":
            translated["medications"] = value

        elif key == "vital_signs":
            translated["vital_signs"] = value

        elif key == "diagnostic_findings":
            translated["diagnostic_findings"] = value

        elif key == "lab_results":
            translated_results = []

            for result in value:
                translated_result = result.copy()

                status = translated_result.get("status")

                if status:
                    translated_result["status"] = STATUS_TRANSLATIONS.get(
                        language,
                        {}
                    ).get(
                        status,
                        status
                    )

                translated_results.append(translated_result)

            translated["lab_results"] = translated_results

        else:
            translated[key] = value

    return translated


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="@Moksha29",
        database="medidecode"
    )


def get_authenticated_user_id():
    user_id = request.headers.get("X-User-ID")
    if user_id is None or user_id == "":
        return None

    try:
        return int(user_id)
    except (TypeError, ValueError):
        return None

@app.route('/api/support', methods=['POST'])
def submit_support_request():
    try:
        data = request.get_json()

        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        category = data.get('category', '').strip()
        message = data.get('message', '').strip()

        # Validate required fields
        if not name or not email or not category or not message:
            return jsonify({
                "success": False,
                "message": "Please fill in all required fields."
            }), 400

        # Get logged-in user ID if available
        user_id = get_authenticated_user_id()

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO support_requests
            (user_id, name, email, category, message)
            VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(query, (
            user_id,
            name,
            email,
            category,
            message
        ))

        conn.commit()

        support_id = cursor.lastrowid

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Your support request has been submitted successfully.",
            "id": support_id
        }), 201

    except Exception as e:
        print("Support request error:", e)

        return jsonify({
            "success": False,
            "message": "Unable to submit your support request."
        }), 500
    
@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/index.html")
def index_page():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/labs.html")
def labs_page():
    return send_from_directory(FRONTEND_DIR, "labs.html")


@app.route("/api/status")
def api_status():
    return jsonify({
        "message": "Medical Report Simplifier Backend is Running"
    })

@app.route("/medicalshops.html")
def medicalshops_page():
	return send_from_directory(FRONTEND_DIR, "medicalshops.html")

@app.route("/reports.html")
def reports_page():
    return send_from_directory(FRONTEND_DIR, "reports.html")


@app.route("/settings.html")
def settings_page():
    return send_from_directory(FRONTEND_DIR, "settings.html")

@app.route("/upload.html")
def upload_page():
    return send_from_directory(FRONTEND_DIR, "upload.html")


@app.route("/history.html")
def history_page():
    return send_from_directory(FRONTEND_DIR, "history.html")


@app.route("/health.html")
def health_page():
    return send_from_directory(FRONTEND_DIR, "health.html")


@app.route("/language.html")
def language_page():
    return send_from_directory(FRONTEND_DIR, "language.html")

@app.route("/signup.html")
def signup_page():
    return send_from_directory(FRONTEND_DIR, "signup.html")

@app.route("/profile.html")
def profile_page():
    return send_from_directory(FRONTEND_DIR, "profile.html")

@app.route("/dashboard.html")
def dashboard_page():
    return send_from_directory(FRONTEND_DIR, "dashboard.html")


@app.route("/hospitals.html")
def hospitals_page():
	return send_from_directory(FRONTEND_DIR, "hospitals.html")

@app.route("/feedback.html")
def feedback_page():
    return send_from_directory(FRONTEND_DIR, "feedback.html")

@app.route("/support.html")
def supports_page():
    return send_from_directory(FRONTEND_DIR, 'support.html')

@app.route("/css/<path:filename>")
def css_files(filename):
	return send_from_directory(
		os.path.join(FRONTEND_DIR, "css"),
		filename
	)


@app.route("/js/<path:filename>")
def js_files(filename):
	return send_from_directory(
		os.path.join(FRONTEND_DIR, "js"),
		filename
	)
@app.route("/api/hospitals", methods=["GET"])
def get_nearby_hospitals():
	try:
		latitude = request.args.get("latitude")
		longitude = request.args.get("longitude")

		if not latitude or not longitude:
			return jsonify({
				"error": "Latitude and longitude are required"
			}), 400

		latitude = float(latitude)
		longitude = float(longitude)

		overpass_query = f"""
		[out:json];
		(
		  node["amenity"="hospital"](around:10000,{latitude},{longitude});
		  way["amenity"="hospital"](around:10000,{latitude},{longitude});
		  relation["amenity"="hospital"](around:10000,{latitude},{longitude});

		  node["healthcare"="hospital"](around:10000,{latitude},{longitude});
		  way["healthcare"="hospital"](around:10000,{latitude},{longitude});
		  relation["healthcare"="hospital"](around:10000,{latitude},{longitude});
		);
		out center tags;
		"""

		response = requests.post(
			"https://overpass-api.de/api/interpreter",
			data={"data": overpass_query},
			headers={
				"User-Agent": "MediDecode/1.0",
				"Accept": "application/json"
			},
			timeout=60
		)

		response.raise_for_status()

		data = response.json()

		hospitals = []

		# Words that should NOT appear in hospital names
		excluded_words = [
			"xerox",
			"medical",
			"medicals",
			"pharmacy",
			"chemist",
			"first aid",
			"firstaid",
			"fancy",
			"fancies",
			"laboratory",
			"lab",
			"diagnostic",
			"clinic"
		]

		def calculate_distance(lat1, lon1, lat2, lon2):
			from math import radians, sin, cos, sqrt, atan2

			R = 6371.0

			dlat = radians(lat2 - lat1)
			dlon = radians(lon2 - lon1)

			a = (
				sin(dlat / 2) ** 2
				+
				cos(radians(lat1))
				* cos(radians(lat2))
				* sin(dlon / 2) ** 2
			)

			c = 2 * atan2(
				sqrt(a),
				sqrt(1 - a)
			)

			return R * c

		for element in data.get("elements", []):

			tags = element.get("tags", {})

			name = tags.get("name", "").strip()

			if not name:
				continue

			# Remove obvious non-hospital results
			name_lower = name.lower()

			if any(
				word in name_lower
				for word in excluded_words
			):
				continue

			# Get coordinates
			if element["type"] == "node":

				hospital_lat = element.get("lat")
				hospital_lon = element.get("lon")

			else:

				center = element.get("center", {})

				hospital_lat = center.get("lat")
				hospital_lon = center.get("lon")

			if hospital_lat is None or hospital_lon is None:
				continue

			# Calculate distance from user
			distance_km = calculate_distance(
				latitude,
				longitude,
				hospital_lat,
				hospital_lon
			)

			hospitals.append({
				"id": element.get("id"),
				"name": name,
				"address": ", ".join(
				    part for part in [
					    tags.get("addr:housenumber"),
					    tags.get("addr:street"),
					    tags.get("addr:suburb"),
					    tags.get("addr:city"),
					    tags.get("addr:postcode")
				    ]
				    if part
			    ) or "Address not available",
				"specialties": tags.get(
					"healthcare:speciality",
					"Hospital"
				),
				"latitude": hospital_lat,
				"longitude": hospital_lon,
				"distance_km": round(
					distance_km,
					2
				),
				"distance": (
					str(round(distance_km, 1))
					+ " km"
				)
			})

		# Remove duplicate hospitals
		unique_hospitals = {}

		for hospital in hospitals:

			key = (
				hospital["name"].lower(),
				round(hospital["latitude"], 4),
				round(hospital["longitude"], 4)
			)

			unique_hospitals[key] = hospital

		hospitals = list(
			unique_hospitals.values()
		)

		# Nearest hospitals first
		hospitals.sort(
			key=lambda x: x["distance_km"]
		)

		return jsonify(hospitals)

	except requests.exceptions.RequestException as e:

		return jsonify({
			"error": "Unable to connect to hospital location service",
			"details": str(e)
		}), 500

	except Exception as e:

		return jsonify({
			"error": "Unable to find nearby hospitals",
			"details": str(e)
		}), 500
@app.route("/api/nearby-healthcare", methods=["GET"])
def get_nearby_healthcare():
    try:
        latitude = request.args.get("latitude")
        longitude = request.args.get("longitude")

        if not latitude or not longitude:
            return jsonify({
                "error": "Latitude and longitude are required"
            }), 400

        latitude = float(latitude)
        longitude = float(longitude)

        radius = 5000

        overpass_query = f"""
        [out:json][timeout:30];

        (
          nwr["amenity"="hospital"](around:{radius},{latitude},{longitude});
          nwr["amenity"="pharmacy"](around:{radius},{latitude},{longitude});
          nwr["amenity"="clinic"](around:{radius},{latitude},{longitude});
          nwr["healthcare"="laboratory"](around:{radius},{latitude},{longitude});
          nwr["healthcare"="clinic"](around:{radius},{latitude},{longitude});
        );

        out center tags;
        """

        endpoints = [
            "https://overpass-api.de/api/interpreter",
            "https://overpass.private.coffee/api/interpreter",
            "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
        ]

        data = None
        last_error = None

        for endpoint in endpoints:

            try:

                print("Trying healthcare server:", endpoint)

                response = requests.post(
                    endpoint,
                    data={"data": overpass_query},
                    headers={
                        "User-Agent": "MediDecode/1.0",
                        "Accept": "application/json"
                    },
                    timeout=40
                )

                response.raise_for_status()

                data = response.json()

                print(
                    "Healthcare server worked:",
                    endpoint
                )

                break

            except requests.exceptions.RequestException as e:

                print(
                    "Healthcare server failed:",
                    endpoint,
                    "|",
                    str(e)
                )

                last_error = e

        if data is None:
            return jsonify({
                "error": "Unable to connect to healthcare location service",
                "details": str(last_error)
            }), 503

        places = []

        def calculate_distance(lat1, lon1, lat2, lon2):

            from math import radians, sin, cos, sqrt, atan2

            R = 6371.0

            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)

            a = (
                sin(dlat / 2) ** 2
                +
                cos(radians(lat1))
                * cos(radians(lat2))
                * sin(dlon / 2) ** 2
            )

            c = 2 * atan2(
                sqrt(a),
                sqrt(1 - a)
            )

            return R * c

        for element in data.get("elements", []):

            tags = element.get("tags", {})

            name = tags.get("name", "").strip()

            if not name:
                continue

            # ----------------------------------------
            # Determine coordinates
            # ----------------------------------------

            if element.get("type") == "node":

                place_lat = element.get("lat")
                place_lon = element.get("lon")

            else:

                center = element.get("center", {})

                place_lat = center.get("lat")
                place_lon = center.get("lon")

            if place_lat is None or place_lon is None:
                continue

            # ----------------------------------------
            # Determine healthcare type
            # ----------------------------------------

            if tags.get("amenity") == "hospital":

                place_type = "Hospital"

            elif tags.get("amenity") == "pharmacy":

                place_type = "Medical Shop"

            elif tags.get("amenity") == "clinic":

                place_type = "Clinic"

            elif tags.get("healthcare") == "laboratory":

                place_type = "Diagnostic Lab"

            elif tags.get("healthcare") == "clinic":

                place_type = "Clinic"

            else:

                place_type = "Healthcare"

            # ----------------------------------------
            # Address
            # ----------------------------------------

            address = ", ".join(
                part
                for part in [
                    tags.get("addr:housenumber"),
                    tags.get("addr:street"),
                    tags.get("addr:suburb"),
                    tags.get("addr:city"),
                    tags.get("addr:postcode")
                ]
                if part
            ) or "Address not available"

            # ----------------------------------------
            # Distance
            # ----------------------------------------

            distance_km = calculate_distance(
                latitude,
                longitude,
                place_lat,
                place_lon
            )

            places.append({
                "id": element.get("id"),
                "name": name,
                "type": place_type,
                "address": address,
                "latitude": place_lat,
                "longitude": place_lon,
                "distance_km": round(distance_km, 2),
                "distance": (
                    str(round(distance_km, 1))
                    + " km"
                )
            })

        # ----------------------------------------
        # Remove duplicates
        # ----------------------------------------

        unique_places = {}

        for place in places:

            key = (
                place["name"].lower(),
                round(place["latitude"], 4),
                round(place["longitude"], 4)
            )

            unique_places[key] = place

        places = list(unique_places.values())

        # ----------------------------------------
        # Nearest locations first
        # ----------------------------------------

        places.sort(
            key=lambda x: x["distance_km"]
        )

        print(
            "Healthcare locations found:",
            len(places)
        )

        return jsonify(places), 200

    except ValueError:

        return jsonify({
            "error": "Invalid latitude or longitude"
        }), 400

    except Exception as e:

        print(
            "HEALTHCARE API ERROR:",
            str(e)
        )

        return jsonify({
            "error": "Unable to find nearby healthcare locations",
            "details": str(e)
        }), 500
@app.route("/api/medicalshops", methods=["GET"])
def get_nearby_medical_shops():
	try:
		latitude = request.args.get("latitude")
		longitude = request.args.get("longitude")

		if not latitude or not longitude:
			return jsonify({
				"error": "Latitude and longitude are required"
			}), 400

		latitude = float(latitude)
		longitude = float(longitude)

		# Search within 5 km of the user's current location.
		# Multiple Overpass servers are used so that the feature
		# can continue working if one public server is busy.
		overpass_query = f"""
		[out:json][timeout:20];
		(
		  node["amenity"="pharmacy"](around:5000,{latitude},{longitude});
		  way["amenity"="pharmacy"](around:5000,{latitude},{longitude});
		);
		out center tags;
		"""

		overpass_endpoints = [
			"https://maps.mail.ru/osm/tools/overpass/api/interpreter",
			"https://overpass-api.de/api/interpreter",
			"https://overpass.private.coffee/api/interpreter"
		]

		data = None
		last_error = None

		for endpoint in overpass_endpoints:
			try:
				print("Trying medical shop server:", endpoint)

				response = requests.post(
					endpoint,
					data={"data": overpass_query},
					headers={
						"User-Agent": "MediDecode/1.0",
						"Accept": "application/json"
					},
					timeout=20
				)

				response.raise_for_status()

				data = response.json()

				print(
					"Medical shop server worked:",
					endpoint
				)

				break

			except requests.exceptions.RequestException as e:
				print(
					"Medical shop server failed:",
					endpoint,
					"|",
					str(e)
				)

				last_error = e
				continue

		# If all Overpass servers failed
		if data is None:
			return jsonify({
				"error": "Unable to connect to medical shop location service",
				"details": str(last_error)
			}), 503

		medical_shops = []

		def calculate_distance(lat1, lon1, lat2, lon2):
			from math import radians, sin, cos, sqrt, atan2

			R = 6371.0

			dlat = radians(lat2 - lat1)
			dlon = radians(lon2 - lon1)

			a = (
				sin(dlat / 2) ** 2
				+
				cos(radians(lat1))
				* cos(radians(lat2))
				* sin(dlon / 2) ** 2
			)

			c = 2 * atan2(
				sqrt(a),
				sqrt(1 - a)
			)

			return R * c

		for element in data.get("elements", []):

			tags = element.get("tags", {})

			name = tags.get("name", "").strip()

			if not name:
				continue

			# Get coordinates
			if element.get("type") == "node":

				shop_lat = element.get("lat")
				shop_lon = element.get("lon")

			else:

				center = element.get("center", {})

				shop_lat = center.get("lat")
				shop_lon = center.get("lon")

			if shop_lat is None or shop_lon is None:
				continue

			# Calculate distance from user's location
			distance_km = calculate_distance(
				latitude,
				longitude,
				shop_lat,
				shop_lon
			)

			address = ", ".join(
				part for part in [
					tags.get("addr:housenumber"),
					tags.get("addr:street"),
					tags.get("addr:suburb"),
					tags.get("addr:city"),
					tags.get("addr:postcode")
				]
				if part
			) or "Address not available"

			medical_shops.append({
				"id": element.get("id"),
				"name": name,
				"address": address,
				"latitude": shop_lat,
				"longitude": shop_lon,
				"distance_km": round(
					distance_km,
					2
				),
				"distance": (
					str(round(distance_km, 1))
					+ " km"
				)
			})

		# Remove duplicate shops
		unique_shops = {}

		for shop in medical_shops:

			key = (
				shop["name"].lower(),
				round(shop["latitude"], 4),
				round(shop["longitude"], 4)
			)

			unique_shops[key] = shop

		medical_shops = list(
			unique_shops.values()
		)

		# Nearest shops first
		medical_shops.sort(
			key=lambda x: x["distance_km"]
		)

		return jsonify(medical_shops)

	except ValueError:

		return jsonify({
			"error": "Invalid latitude or longitude"
		}), 400

	except Exception as e:

		return jsonify({
			"error": "Unable to find nearby medical shops",
			"details": str(e)
		}), 500
        
@app.route("/api/register", methods=["POST"])
def register():
    try:
        data = request.get_json()

        name = data.get("name")
        age = data.get("age")
        gender = data.get("gender")
        blood_group = data.get("blood_group")
        height = data.get("height")
        weight = data.get("weight")
        phone = data.get("phone")
        email = data.get("email")
        password = data.get("password")
        address = data.get("address")
        emergency_contact = data.get("emergency_contact")
        medical_history = data.get("medical_history")

        if not name or not email or not password:
            return jsonify({
                "message": "Name, email and password are required"
            }), 400

        db = get_db_connection()
        cursor = db.cursor()

        # Check whether email already exists
        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            db.close()

            return jsonify({
                "message": "Email already registered"
            }), 409

        # Hash password
        password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        # Save user
        cursor.execute("""
            INSERT INTO users
            (name, age, gender, blood_group, height, weight,
             phone, email, password_hash, address, emergency_contact,medical_history)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            name,
            age,
            gender,
            blood_group,
            height,
            weight,
            phone,
            email,
            password_hash,
            address,
            emergency_contact,
            medical_history
        ))

        db.commit()

        cursor.close()
        db.close()

        return jsonify({
            "message": "Account created successfully"
        }), 201

    except Exception as e:
        return jsonify({
            "message": "Registration failed",
            "error": str(e)
        }), 500


@app.route("/api/login", methods=["POST"])
def login():
    db = None
    cursor = None

    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "message": "Email and password are required"
            }), 400

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({
                "message": "Email and password are required"
            }), 400

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute(
            "SELECT id, name, email, password_hash FROM users WHERE email = %s",
            (email,)
        )
        user = cursor.fetchone()

        if not user:
            return jsonify({
                "message": "Invalid email or password"
            }), 401

        user_id, user_name, user_email, password_hash = user

        if not bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8")):
            return jsonify({
                "message": "Invalid email or password"
            }), 401

        return jsonify({
            "message": "Login successful",
            "token": "login-token",
            "user": {
                "id": user_id,
                "name": user_name,
                "email": user_email
            }
        }), 200

    except Exception as e:
        return jsonify({
            "message": "Login failed",
            "error": str(e)
        }), 500

    finally:
        if cursor is not None:
            cursor.close()
        if db is not None:
            db.close()

@app.route("/api/profile/<int:user_id>", methods=["GET"])
def get_profile(user_id):
    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                name,
                age,
                gender,
                blood_group,
                height,
                weight,
                phone,
                email,
                address,
                emergency_contact,
                medical_history,
                created_at
            FROM users
            WHERE id = %s
        """, (user_id,))

        user = cursor.fetchone()

        if not user:
            return jsonify({
                "message": "User not found"
            }), 404

        return jsonify({
            "message": "Profile loaded successfully",
            "user": user
        }), 200

    except Exception as e:
        return jsonify({
            "message": "Failed to load profile",
            "error": str(e)
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if db is not None:
            db.close()
@app.route("/api/profile/<int:user_id>", methods=["PUT"])
def update_profile(user_id):
    db = None
    cursor = None

    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "message": "No profile data received"
            }), 400

        name = data.get("name")
        age = data.get("age")
        gender = data.get("gender")
        blood_group = data.get("blood_group")
        height = data.get("height")
        weight = data.get("weight")
        phone = data.get("phone")
        email = data.get("email")
        address = data.get("address")
        emergency_contact = data.get("emergency_contact")

        if not name or not email:
            return jsonify({
                "message": "Name and email are required"
            }), 400

        db = get_db_connection()
        cursor = db.cursor()

        # Check whether another user already has this email
        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE email = %s AND id != %s
            """,
            (email, user_id)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            return jsonify({
                "message": "Email already belongs to another account"
            }), 409

        cursor.execute(
            """
            UPDATE users
            SET
                name = %s,
                age = %s,
                gender = %s,
                blood_group = %s,
                height = %s,
                weight = %s,
                phone = %s,
                email = %s,
                address = %s,
                emergency_contact = %s
            WHERE id = %s
            """,
            (
                name,
                age,
                gender,
                blood_group,
                height,
                weight,
                phone,
                email,
                address,
                emergency_contact,
                user_id
            )
        )

        db.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "message": "User not found"
            }), 404

        return jsonify({
            "message": "Profile updated successfully"
        }), 200

    except Exception as e:

        if db is not None:
            db.rollback()

        return jsonify({
            "message": "Profile update failed",
            "error": str(e)
        }), 500

    finally:

        if cursor is not None:
            cursor.close()

        if db is not None:
            db.close()


@app.route("/api/users/me/settings", methods=["GET", "PUT"])
def user_settings():
    user_id = get_authenticated_user_id()
    if user_id is None:
        return jsonify({"message": "User authentication required"}), 401

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("SELECT id, preferred_language FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if user is None:
            return jsonify({"message": "User not found"}), 404

        cursor.execute("SELECT * FROM user_settings WHERE user_id = %s", (user_id,))
        settings = cursor.fetchone()

        if settings is None:
            cursor.execute(
                """
                INSERT INTO user_settings
                (user_id, dark_mode, notify_report_updates, notify_medicine_reminders, notify_health_alerts, share_data_for_research, two_factor_authentication)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    False,
                    True,
                    True,
                    True,
                    False,
                    False,
                )
            )
            db.commit()
            cursor.execute("SELECT * FROM user_settings WHERE user_id = %s", (user_id,))
            settings = cursor.fetchone()

        if request.method == "GET":
            response_settings = {
                "preferred_language": user.get("preferred_language") or "en",
                "dark_mode": bool(settings.get("dark_mode", False)),
                "notify_report_updates": bool(settings.get("notify_report_updates", True)),
                "notify_medicine_reminders": bool(settings.get("notify_medicine_reminders", True)),
                "notify_health_alerts": bool(settings.get("notify_health_alerts", True)),
                "share_data_for_research": bool(settings.get("share_data_for_research", False)),
                "two_factor_authentication": bool(settings.get("two_factor_authentication", False)),
            }
            return jsonify({"settings": response_settings}), 200

        payload = request.get_json(silent=True) or {}
        allowed_keys = {
            "preferred_language",
            "dark_mode",
            "notify_report_updates",
            "notify_medicine_reminders",
            "notify_health_alerts",
            "share_data_for_research",
            "two_factor_authentication",
        }

        update_fields = []
        update_values = []

        if "preferred_language" in payload:
            lang = str(payload.get("preferred_language", "en")).lower().strip()
            if lang not in SUPPORTED_LANGUAGES:
                lang = "en"
            cursor.execute("UPDATE users SET preferred_language = %s WHERE id = %s", (lang, user_id))
            update_fields.append("preferred_language")
            update_values.append(lang)

        if "dark_mode" in payload:
            dark_mode = bool(payload.get("dark_mode"))
            cursor.execute("UPDATE user_settings SET dark_mode = %s WHERE user_id = %s", (dark_mode, user_id))

        for key in [
            "notify_report_updates",
            "notify_medicine_reminders",
            "notify_health_alerts",
            "share_data_for_research",
            "two_factor_authentication",
        ]:
            if key in payload:
                cursor.execute(
                    f"UPDATE user_settings SET {key} = %s WHERE user_id = %s",
                    (bool(payload.get(key)), user_id)
                )

        db.commit()

        cursor.execute("SELECT * FROM user_settings WHERE user_id = %s", (user_id,))
        settings = cursor.fetchone()
        cursor.execute("SELECT preferred_language FROM users WHERE id = %s", (user_id,))
        updated_user = cursor.fetchone()

        return jsonify({
            "message": "Settings updated successfully",
            "settings": {
                "preferred_language": (updated_user.get("preferred_language") if updated_user else "en") or "en",
                "dark_mode": bool(settings.get("dark_mode", False)),
                "notify_report_updates": bool(settings.get("notify_report_updates", True)),
                "notify_medicine_reminders": bool(settings.get("notify_medicine_reminders", True)),
                "notify_health_alerts": bool(settings.get("notify_health_alerts", True)),
                "share_data_for_research": bool(settings.get("share_data_for_research", False)),
                "two_factor_authentication": bool(settings.get("two_factor_authentication", False)),
            }
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({"message": "Settings update failed", "error": str(e)}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if db is not None:
            db.close()


@app.route("/api/users/me/change-password", methods=["POST"])
def change_password():
    user_id = get_authenticated_user_id()
    if user_id is None:
        return jsonify({"message": "User authentication required"}), 401

    data = request.get_json(silent=True) or {}
    current_password = (data.get("current_password") or "").strip()
    new_password = (data.get("new_password") or "").strip()
    confirm_new_password = (data.get("confirm_new_password") or "").strip()

    if not current_password or not new_password or not confirm_new_password:
        return jsonify({"message": "Current password, new password, and confirmation are required"}), 400

    if new_password != confirm_new_password:
        return jsonify({"message": "New passwords do not match"}), 400

    if len(new_password) < 8:
        return jsonify({"message": "New password must be at least 8 characters long"}), 400

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        if result is None:
            return jsonify({"message": "User not found"}), 404

        stored_hash = result.get("password_hash")
        if not bcrypt.checkpw(current_password.encode("utf-8"), stored_hash.encode("utf-8")):
            return jsonify({"message": "Current password is incorrect"}), 401

        new_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, user_id))
        db.commit()
        return jsonify({"message": "Password changed successfully"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"message": "Password change failed", "error": str(e)}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if db is not None:
            db.close()


@app.route("/api/users/me/export-data", methods=["GET"])
def export_user_data():
    user_id = get_authenticated_user_id()
    if user_id is None:
        return jsonify({"message": "User authentication required"}), 401

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, name, email, age, gender, blood_group, height_cm, weight_kg, phone, address, emergency_contact, medical_history, preferred_language, account_type, created_at
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )
        user = cursor.fetchone()
        if user is None:
            return jsonify({"message": "User not found"}), 404

        cursor.execute("SELECT id, file_name, report_type, created_at FROM reports WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
        reports = cursor.fetchall()

        cursor.execute("SELECT id, user_id, type, title, message, is_read, created_at FROM notifications WHERE user_id = %s ORDER BY created_at DESC LIMIT 50", (user_id,))
        notifications = cursor.fetchall()

        for key in ["password_hash"]:
            user.pop(key, None)

        export = {
            "user": user,
            "reports": reports,
            "notifications": notifications,
            "exported_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        }
        return jsonify(export), 200
    except Exception as e:
        return jsonify({"message": "Data export failed", "error": str(e)}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if db is not None:
            db.close()


@app.route("/api/users/me/delete-account", methods=["POST"])
def delete_account():
    user_id = get_authenticated_user_id()
    if user_id is None:
        return jsonify({"message": "User authentication required"}), 401

    data = request.get_json(silent=True) or {}
    password = (data.get("password") or "").strip()
    confirm_text = (data.get("confirm_text") or "").strip()

    if not password or confirm_text != "DELETE MY ACCOUNT":
        return jsonify({"message": "Current password and confirmation text are required"}), 400

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        if result is None:
            return jsonify({"message": "User not found"}), 404

        stored_hash = result.get("password_hash")
        if not bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
            return jsonify({"message": "Current password is incorrect"}), 401

        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        db.commit()
        return jsonify({"message": "Account deleted successfully"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"message": "Account deletion failed", "error": str(e)}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if db is not None:
            db.close()


def extract_text_from_file(file_path, file_extension):
    """
    Extract text from medical reports using Tesseract OCR.

    Images are preprocessed before OCR to improve recognition.
    No AI is used.
    """

    extracted_text = ""

    if file_extension == ".pdf":

        pdf = pymupdf.open(file_path)

        # First try normal PDF text extraction
        for page in pdf:
            extracted_text += page.get_text()

        # If PDF has little/no selectable text, use OCR
        if len(extracted_text.strip()) < 20:

            extracted_text = ""

            for page in pdf:

                pix = page.get_pixmap(
                    matrix=pymupdf.Matrix(3, 3)
                )

                image = Image.frombytes(
                    "RGB",
                    [pix.width, pix.height],
                    pix.samples
                )

                # Convert to grayscale
                image = ImageOps.grayscale(image)

                # Increase contrast
                image = ImageOps.autocontrast(image)

                # Upscale
                image = image.resize(
                    (
                        image.width * 2,
                        image.height * 2
                    )
                )

                # Slight sharpening
                image = image.filter(
                    ImageFilter.SHARPEN
                )

                page_text = pytesseract.image_to_string(
                    image,
                    config="--oem 3 --psm 6"
                )

                extracted_text += page_text + "\n"

        pdf.close()

    else:

        # ============================================
        # JPG / JPEG / PNG
        # ============================================

        image = Image.open(file_path)

        # Make sure image is RGB
        image = image.convert("RGB")

        # --------------------------------------------
        # 1. Grayscale
        # --------------------------------------------

        gray = ImageOps.grayscale(image)

        # --------------------------------------------
        # 2. Increase contrast
        # --------------------------------------------

        gray = ImageOps.autocontrast(gray)

        # --------------------------------------------
        # 3. Upscale image
        # --------------------------------------------

        gray = gray.resize(
            (
                gray.width * 2,
                gray.height * 2
            )
        )

        # --------------------------------------------
        # 4. Sharpen
        # --------------------------------------------

        gray = gray.filter(
            ImageFilter.SHARPEN
        )

        # --------------------------------------------
        # 5. OCR
        # --------------------------------------------

        extracted_text = pytesseract.image_to_string(
            gray,
            config="--oem 3 --psm 6"
        )
    print("\n================ OCR TEXT ================\n")
    print(extracted_text)
    print("\n===========================================\n")
    return extracted_text.strip()
def clean_ocr_text(text):
    """
    Clean common OCR mistakes without using AI.
    """

    if not text:
        return ""

    # Normalize line endings
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Common OCR character corrections
    replacements = {
        "¢": "c",
        "«": "-",
        "»": "-",
        "—": "-",
        "–": "-",
        "| am": "I am",
        "|": "I",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Normalize spaces on each line while preserving line structure.
    lines = []
    blank_line_added = False

    for line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", line).strip()

        if not line:
            if not blank_line_added:
                lines.append("")
            blank_line_added = True
            continue

        lines.append(line)
        blank_line_added = False

    return "\n".join(lines).strip()


def extract_medical_parameters(raw_text):
    """
    Extract common medical parameters from OCR text using rule-based
    matching and provide simplified explanations.

    No AI is used.

    Output schema remains compatible with the existing frontend:
    {
        "name": "...",
        "detected": "...",
        "normal_range": "...",
        "meaning": "...",
        "risk": "..."
    }
    """

    if not raw_text:
        return []

    text = str(raw_text)

    # ------------------------------------------------------------
    # BASIC OCR NORMALIZATION
    # ------------------------------------------------------------
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("µ", "u").replace("μ", "u")
    text = text.replace("–", "-").replace("—", "-").replace("−", "-")
    text = text.replace("→", " ")
    text = text.replace("=>", " ")
    text = re.sub(r"[ \t]+", " ", text)

    # ------------------------------------------------------------
    # DEFAULT REFERENCE RANGES
    #
    # These are general adult ranges only.
    # A laboratory's own reference range should take priority
    # whenever it is present in the report.
    # ------------------------------------------------------------
    default_ranges = {
        "Hemoglobin": (12.5, 17.5),
        "RBC": (3.8, 5.1),
        "WBC": (4.0, 11.0),
        "Platelets": (1.5, 4.5),
        "Blood Sugar": (70.0, 99.0),
        "Fasting Blood Sugar": (70.0, 99.0),
        "Glucose": (70.0, 99.0),
        "Cholesterol": (0.0, 200.0),
        "HDL": (40.0, 60.0),
        "LDL": (0.0, 100.0),
        "Triglycerides": (0.0, 150.0),
        "Vitamin D": (30.0, 100.0),
        "Vitamin B12": (200.0, 900.0),
        "TSH": (0.5, 4.5),
        "Creatinine": (0.6, 1.1),
        "Urea": (15.0, 45.0),
        "Uric Acid": (3.5, 7.2),
        "ALT": (7.0, 56.0),
        "AST": (10.0, 40.0),
        "Bilirubin": (0.3, 1.2),
        "Calcium": (8.5, 10.5),
        "Sodium": (135.0, 145.0),
        "Potassium": (3.5, 5.1),
        "Heart Rate": (60.0, 100.0)
    }

    # ------------------------------------------------------------
    # MEDICAL PARAMETER ALIASES
    # ------------------------------------------------------------
    parameter_aliases = {

    "Hemoglobin": [
        "Hemoglobin",
        "Haemoglobin",
        "Hb",
        "Hgb"
    ],

    "RBC": [
        "Total RBC Count",
        "RBC Count",
        "Red Blood Cell Count",
        "Red Blood Cell",
        "RBC"
    ],

    "WBC": [
        "Total WBC Count",
        "WBC Count",
        "White Blood Cell Count",
        "White Blood Cell",
        "Leukocyte Count",
        "WBC"
    ],

    "Platelets": [
        "Platelet Count",
        "Platelets",
        "Platelet"
    ],

    "Fasting Blood Sugar": [
        "Fasting Blood Glucose",
        "Fasting Blood Sugar",
        "Fasting Sugar",
        "FBS"
    ],

    "Blood Sugar": [
        "Random Blood Sugar",
        "Blood Sugar",
        "RBS"
    ],

    "Glucose": [
        "Blood Glucose",
        "Glucose"
    ],

    "Cholesterol": [
        "Total Cholesterol",
        "TC"
    ],

    "HDL": [
        "HDL Cholesterol",
        "High Density Lipoprotein",
        "High-Density Lipoprotein",
        "HDL"
    ],

    "LDL": [
        "LDL Cholesterol",
        "Low Density Lipoprotein",
        "Low-Density Lipoprotein",
        "LDL"
    ],

    "VLDL": [
        "VLDL Cholesterol",
        "VLDL"
    ],

    "Triglycerides": [
        "Triglycerides",
        "Triglyceride",
        "TG"
    ],

    "Total Chol/HDL Ratio": [
        "Total Chol/HDL Ratio",
        "Total Cholesterol/HDL Ratio",
        "Chol/HDL Ratio"
    ],

    "Vitamin D": [
        "25-OH Vitamin D",
        "25 OH Vitamin D",
        "Vitamin D",
        "Vit D"
    ],

    "Vitamin B12": [
        "Vitamin B12",
        "Vit B12",
        "B12"
    ],

    "TSH": [
        "Thyroid Stimulating Hormone (TSH)",
        "Thyroid Stimulating Hormone",
        "TSH"
    ],

    "Creatinine": [
        "Serum Creatinine",
        "Creatinine",
        "Cr"
    ],

    "Urea": [
        "Blood Urea",
        "Serum Urea",
        "Urea"
    ],

    "Uric Acid": [
        "Serum Uric Acid",
        "Uric Acid",
        "UA"
    ],

    "ALT": [
        "Alanine Aminotransferase",
        "ALT",
        "SGPT"
    ],

    "AST": [
        "Aspartate Aminotransferase",
        "AST",
        "SGOT"
    ],

    "Bilirubin": [
        "Total Bilirubin",
        "Serum Bilirubin",
        "Bilirubin"
    ],

    "Calcium": [
        "Total Calcium",
        "Serum Calcium",
        "Calcium"
    ],

    "Sodium": [
        "Serum Sodium",
        "Sodium",
        "Na"
    ],

    "Potassium": [
        "Serum Potassium",
        "Potassium",
        "K"
    ],

    "Blood Pressure": [
        "Blood Pressure",
        "BP"
    ],

    "Heart Rate": [
        "Heart Rate",
        "Pulse Rate",
        "Pulse"
    ]
}

    # ------------------------------------------------------------
    # SIMPLE MEDICAL EXPLANATIONS
    # ------------------------------------------------------------
    explanations = {

        "Hemoglobin":
            "Hemoglobin is a protein in red blood cells that carries oxygen throughout your body.",

        "RBC":
            "RBCs are red blood cells that carry oxygen from your lungs to the rest of your body.",

        "WBC":
            "WBCs are white blood cells that help your body fight infections and other illnesses.",

        "Platelets":
            "Platelets help your blood form clots and stop bleeding.",

        "Fasting Blood Sugar":
            "Fasting blood sugar measures the amount of glucose in your blood after not eating for several hours.",

        "Blood Sugar":
            "Blood sugar measures the amount of glucose in your blood and helps show how your body is controlling sugar.",

        "Glucose":
            "Glucose is the main type of sugar in your blood and provides energy to your body's cells.",

        "Cholesterol":
            "Cholesterol is a fatty substance in your blood. Your body needs some cholesterol, but too much can increase heart and blood vessel risks.",

        "HDL":
            "HDL is often called the 'good' cholesterol because it helps carry excess cholesterol away from the blood vessels.",

        "LDL":
            "LDL is often called the 'bad' cholesterol because high levels can contribute to cholesterol buildup in blood vessels.",

        "Triglycerides":
            "Triglycerides are a type of fat in your blood. High levels can be associated with increased heart health risk.",

        "Vitamin D":
            "Vitamin D helps your body absorb calcium and supports healthy bones and muscles.",

        "Vitamin B12":
            "Vitamin B12 helps make healthy red blood cells and supports normal nerve function.",

        "TSH":
            "TSH is a hormone that helps control how your thyroid gland works.",

        "Creatinine":
            "Creatinine is a waste product produced by muscles. The kidneys normally remove it from the blood.",

        "Urea":
            "Urea is a waste product produced when the body breaks down proteins. The kidneys normally remove it from the blood.",

        "Uric Acid":
            "Uric acid is produced when the body breaks down certain substances called purines. The kidneys normally remove it from the body.",

        "ALT":
            "ALT is an enzyme found mainly in the liver. It is commonly measured to help assess liver health.",

        "AST":
            "AST is an enzyme found in the liver and other tissues. It is commonly measured when checking for tissue or liver problems.",

        "Bilirubin":
            "Bilirubin is a yellow substance produced when old red blood cells are broken down. The liver helps process and remove it.",

        "Calcium":
            "Calcium is an important mineral needed for healthy bones, muscles and normal nerve function.",

        "Sodium":
            "Sodium is an electrolyte that helps control fluid balance and supports normal nerve and muscle function.",

        "Potassium":
            "Potassium is an electrolyte that is important for normal heart, nerve and muscle function.",

        "Blood Pressure":
            "Blood pressure shows the force of blood pushing against the walls of your blood vessels.",

        "Heart Rate":
            "Heart rate is the number of times your heart beats in one minute."
    }

    # ------------------------------------------------------------
    # STATUS-AWARE EXPLANATIONS
    # ------------------------------------------------------------
    status_messages = {
        "Normal":
            "This result is within the usual reference range shown or used by the system.",

        "Low":
            "This result is below the usual reference range.",

        "Slightly Low":
            "This result is slightly below the usual reference range.",

        "High":
            "This result is above the usual reference range.",

        "Slightly High":
            "This result is slightly above the usual reference range.",

        "Unknown":
            "A reference range was not available, so the result could not be classified."
    }

    # ------------------------------------------------------------
    # RESULT STORAGE
    # ------------------------------------------------------------
    parameters = []
    seen = set()

    # ------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------
    def normalize_unit(unit):
        if not unit:
            return ""

        cleaned = re.sub(r"\s+", "", str(unit).strip())

        replacements = {
            "mgdl": "mg/dL",
            "mg/dl": "mg/dL",
            "gdl": "g/dL",
            "g/dl": "g/dL",
            "gm/dl": "g/dL",
            "ngml": "ng/mL",
            "ng/ml": "ng/mL",
            "mmhg": "mmHg",
            "uiu/ml": "uIU/mL",
            "miu/ml": "mIU/mL",
            "x10^3/ul": "x10^3/uL",
            "x10^3/µl": "x10^3/uL",
            "lakh/ul": "Lakh/uL",
            "lakhs/ul": "Lakh/uL",
            "lac/ul": "Lakh/uL",
            "bpm": "bpm",
            "/min": "/min",
            "min": "/min"
        }

        return replacements.get(cleaned.lower(), cleaned)

    def first_number(value):
        if value is None:
            return None

        match = re.search(
            r"[-+]?\d+(?:\.\d+)?",
            str(value)
        )

        if match:
            try:
                return float(match.group(0))
            except ValueError:
                return None

        return None

    def normalize_range(value):
        if not value:
            return "—"

        value = str(value).strip()

        if value in {"-", "--", "—"}:
            return "—"

        value = re.sub(r"\s+", " ", value)

        return value

    def classify_value(value, reference_range, default_range=None):
        numeric_value = first_number(value)

        if numeric_value is None:
            return "Unknown"

        # --------------------------------------------------------
        # Try report-provided reference range first
        # --------------------------------------------------------
        if reference_range and reference_range != "—":

            clean_range = re.sub(
                r"\s+",
                " ",
                str(reference_range).strip()
            )

            range_match = re.search(
                r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)",
                clean_range,
                re.IGNORECASE
            )

            if range_match:

                low = float(range_match.group(1))
                high = float(range_match.group(2))

                if numeric_value < low:
                    if numeric_value < low * 0.9:
                        return "Low"
                    return "Slightly Low"

                if numeric_value > high:
                    if numeric_value > high * 1.1:
                        return "High"
                    return "Slightly High"

                return "Normal"

            comparator_match = re.search(
                r"(<=|>=|<|>)\s*(\d+(?:\.\d+)?)",
                clean_range
            )

            if comparator_match:

                operator = comparator_match.group(1)
                threshold = float(comparator_match.group(2))

                if operator in {"<", "<="}:

                    if numeric_value > threshold:
                        return "High"

                    return "Normal"

                if operator in {">", ">="}:

                    if numeric_value < threshold:
                        return "Low"

                    return "Normal"

        # --------------------------------------------------------
        # Fall back to general default range
        # --------------------------------------------------------
        if default_range:

            low, high = default_range

            if numeric_value < low:

                if numeric_value < low * 0.9:
                    return "Low"

                return "Slightly Low"

            if numeric_value > high:

                if numeric_value > high * 1.1:
                    return "High"

                return "Slightly High"

            return "Normal"

        return "Unknown"

    def extract_reference_range(segment):
        if not segment:
            return "—"

        segment = re.sub(
            r"\s+",
            " ",
            str(segment).strip()
        )

        patterns = [

            # Example: 12 - 16 g/dL
            r"\d+(?:\.\d+)?\s*(?:-|to)\s*\d+(?:\.\d+)?"
            r"(?:\s*(?:mg/dL|g/dL|ng/mL|mmHg|mIU/L|uIU/mL|bpm|/min|Lakh/uL|x10\^3/uL))?",

            # Example: < 200
            r"(?:<=|>=|<|>)\s*\d+(?:\.\d+)?"
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                segment,
                re.IGNORECASE
            )

            if match:
                return normalize_range(match.group(0))

        return "—"

    def add_parameter(
        name,
        detected,
        normal_range="—",
        risk="Unknown"
    ):

        if not detected:
            return

        detected = str(detected).strip()

        if not detected:
            return

        # --------------------------------------------------------
        # Avoid duplicate parameters
        # --------------------------------------------------------

        normalized_detected = re.sub(
            r"\s+",
            " ",
            detected.strip().lower()
        )

        # Special handling for Blood Pressure
        if name == "Blood Pressure":
            bp_match = re.search(
                r"(\d{2,3})\s*/\s*(\d{2,3})",
                normalized_detected
            )

            if bp_match:
                normalized_detected = (
                    f"{bp_match.group(1)}/{bp_match.group(2)}"
                )

        key = (
            name.lower(),
            normalized_detected
        )

        if key in seen:
            return

        seen.add(key)       

        base_explanation = explanations.get(
            name,
            f"{name} is a medical measurement found in the report."
        )

        status_explanation = status_messages.get(
            risk,
            status_messages["Unknown"]
        )

        # --------------------------------------------------------
        # Combined patient-friendly explanation
        # --------------------------------------------------------
        meaning = (
            f"{base_explanation} "
            f"{status_explanation}"
        )

        parameters.append({
            "name": name,
            "detected": detected,
            "normal_range": normal_range or "—",
            "meaning": meaning,
            "risk": risk
        })

    # ------------------------------------------------------------
    # PARSE A SINGLE LINE
    # ------------------------------------------------------------
    def parse_line(line, canonical_name, aliases):

        if not line:
            return

        cleaned = re.sub(
            r"\s+",
            " ",
            str(line)
        ).strip()

        for alias in sorted(
            aliases,
            key=len,
            reverse=True
        ):

            alias_pattern = (
                rf"(?i)\b{re.escape(alias)}\b"
                rf"\s*(?:[:=]|-)?\s*"
                rf"(.+)"
            )

            match = re.search(
                alias_pattern,
                cleaned
            )

            if not match:
                continue

            tail = match.group(1).strip()

            # ----------------------------------------------------
            # Special case: Blood Pressure
            # ----------------------------------------------------
            if canonical_name == "Blood Pressure":

                bp_match = re.search(
                    r"(\d{2,3})\s*/\s*(\d{2,3})"
                    r"\s*(mmHg|mmhg)?",
                    tail,
                    re.IGNORECASE
                )

                if bp_match:

                    systolic = bp_match.group(1)
                    diastolic = bp_match.group(2)

                    detected = (
                        f"{systolic}/{diastolic}"
                    )

                    if bp_match.group(3):
                        detected += (
                            f" {bp_match.group(3)}"
                        )

                    # General classification for systolic value
                    systolic_value = float(systolic)

                    if systolic_value < 90:
                        risk = "Low"
                    elif systolic_value >= 140:
                        risk = "High"
                    elif systolic_value >= 120:
                        risk = "Slightly High"
                    else:
                        risk = "Normal"

                    add_parameter(
                        canonical_name,
                        detected,
                        "Generally below 120/80 mmHg",
                        risk
                    )

                    return

            # ----------------------------------------------------
            # Special case: Heart Rate
            # ----------------------------------------------------
            if canonical_name == "Heart Rate":

                hr_match = re.search(
                    r"(\d{2,3}(?:\.\d+)?)"
                    r"\s*(bpm|/min|min)?",
                    tail,
                    re.IGNORECASE
                )

                if hr_match:

                    value = hr_match.group(1)
                    unit = normalize_unit(
                        hr_match.group(2) or "bpm"
                    )

                    detected = f"{value} {unit}"

                    risk = classify_value(
                        value,
                        "60 - 100",
                        default_ranges["Heart Rate"]
                    )

                    add_parameter(
                        canonical_name,
                        detected,
                        "60 - 100 bpm",
                        risk
                    )

                    return

            # ----------------------------------------------------
            # General numeric value
            # ----------------------------------------------------
            value_match = re.search(
                r"(?P<value>[-+]?\d[\d,]*(?:\.\d+)?)"
                r"\s*"
                r"(?P<unit>[A-Za-z0-9^/.\-u]+)?",
                tail,
                re.IGNORECASE
            )

            if not value_match:
                continue

            value = value_match.group("value")
            value = value.replace(",", "")

            unit = normalize_unit(
                value_match.group("unit") or ""
            )

            detected = (
                f"{value} {unit}"
                if unit
                else value
            )

            # ----------------------------------------------------
            # Find reference range
            # ----------------------------------------------------
            suffix = tail[
                value_match.end():
            ].strip()

            normal_range = extract_reference_range(
                suffix
            )

            if normal_range == "—":
                normal_range = extract_reference_range(
                    cleaned
                )

            # ----------------------------------------------------
            # Classify result
            # ----------------------------------------------------
            risk = classify_value(
                value,
                normal_range,
                default_ranges.get(
                    canonical_name
                )
            )

            add_parameter(
                canonical_name,
                detected,
                normal_range,
                risk
            )

            return

    # ------------------------------------------------------------
    # PROCESS LINES
    # ------------------------------------------------------------
    lines = [
        re.sub(
            r"\s+",
            " ",
            line
        ).strip()
        for line in text.split("\n")
        if line.strip()
    ]

    # ------------------------------------------------------------
    # First pass: line-by-line extraction
    # ------------------------------------------------------------
    for line in lines:
        for canonical_name, aliases in parameter_aliases.items():
            before_count = len(parameters)

            parse_line(
                line,
                canonical_name,
                aliases
            )

        # Stop checking this line once a parameter was found
            if len(parameters) > before_count:
                break

    # ------------------------------------------------------------
    # Second pass:
    # Useful when OCR puts parameter and value in unusual format.
    # ------------------------------------------------------------
    if len(parameters) < 5:

        for canonical_name, aliases in parameter_aliases.items():

            for alias in sorted(
                aliases,
                key=len,
                reverse=True
            ):

                pattern = (
                    rf"(?i)\b{re.escape(alias)}\b"
                    rf"\s*(?:[:=]|-)?\s*"
                    rf"([-+]?\d+(?:\.\d+)?)"
                    rf"\s*"
                    rf"([A-Za-z0-9^/.\-u]+)?"
                )

                match = re.search(
                    pattern,
                    text
                )

                if not match:
                    continue

                value = match.group(1)

                unit = normalize_unit(
                    match.group(2) or ""
                )

                detected = (
                    f"{value} {unit}"
                    if unit
                    else value
                )

                risk = classify_value(
                    value,
                    "—",
                    default_ranges.get(
                        canonical_name
                    )
                )

                normal_range = "—"

                if canonical_name in default_ranges:

                    low, high = default_ranges[
                        canonical_name
                    ]

                    normal_range = (
                        f"{low:g} - {high:g}"
                    )

                add_parameter(
                    canonical_name,
                    detected,
                    normal_range,
                    risk
                )

                break

    # ------------------------------------------------------------
    # FINAL SAFETY:
    # Remove duplicate parameter entries with same name/value.
    # ------------------------------------------------------------
    unique_parameters = []
    final_seen = set()
    for parameter in parameters:

        key = (
            parameter["name"].lower(),
            parameter["detected"].lower()
        )   

        if key in final_seen:
            continue

        final_seen.add(key)
        unique_parameters.append(parameter)

    return unique_parameters    


def extract_medical_information(text):
    """Extract common medical report fields using rules and regular expressions."""

    information = {
        "patient": {},
        "medical_history": [],
        "allergies": [],
        "medications": [],
        "vital_signs": {},
        "diagnostic_findings": [],
        "lab_results": []
    }

    if not text:
        return information

    lines = [
        re.sub(r"^[+\-]\s*", "", line).strip()
        for line in text.splitlines()
    ]
    normalized_text = "\n".join(lines)

    def field_value(pattern):
        match = re.search(pattern, normalized_text, re.IGNORECASE | re.MULTILINE)
        return match.group(1).strip() if match else None

    patient_fields = {
        "name": r"^\s*Patient\s+Name\s*:\s*(.+)$",
        "date_of_birth": r"^\s*Date\s+of\s+Birth\s*:\s*(.+)$",
        "gender": r"^\s*Gender\s*:\s*(.+)$",
        "patient_id": r"^\s*Patient\s+ID\s*:\s*(.+)$"
    }

    for field_name, pattern in patient_fields.items():
        value = field_value(pattern)
        if value:
            information["patient"][field_name] = value

    heading_pattern = re.compile(
        r"^(patient information|medical history|examination findings|"
        r"diagnostic tests|laboratory results|allergies|medications?)$",
        re.IGNORECASE
    )

    in_history = False
    for line in lines:
        if not line:
            continue

        if heading_pattern.match(line):
            in_history = line.lower() == "medical history"
            continue

        allergy_line = re.search(r"\ballerg(?:y|ies)\b", line, re.IGNORECASE)
        if in_history and not allergy_line and not re.search(
            r"^(?:c\s+)?Currently\s+taking\b|^Medication[s]?\s*:|"
            r"Blood\s+Pressure|Heart\s+Rate|"
            r"\b(?:MRI|CT|X-ray|Ultrasound|ECG|CBC)\b|"
            r"^[^:]+:\s*[-+]?\d+(?:\.\d+)?\b",
            line,
            re.IGNORECASE
        ):
            information["medical_history"].append(line)

        if allergy_line:
            information["allergies"].append(line)

        medication_match = re.search(
            r"^(?:c\s+)?(?:Currently\s+taking|Medication[s]?)\s*:?\s*(.+)$",
            line,
            re.IGNORECASE
        )
        if medication_match:
            information["medications"].append(medication_match.group(1).strip())

        blood_pressure = re.search(
            r"Blood\s+Pressure\s*:?\s*(\d+)\s*/\s*(\d+)\s*(mmHg)?",
            line,
            re.IGNORECASE
        )
        if blood_pressure:
            information["vital_signs"]["blood_pressure"] = {
                "systolic": int(blood_pressure.group(1)),
                "diastolic": int(blood_pressure.group(2)),
                "unit": blood_pressure.group(3) or "mmHg"
            }

        heart_rate = re.search(
            r"Heart\s+Rate\s*:?\s*(\d+(?:\.\d+)?)\s*(bpm)?",
            line,
            re.IGNORECASE
        )
        if heart_rate:
            heart_rate_value = float(heart_rate.group(1))
            if heart_rate_value.is_integer():
                heart_rate_value = int(heart_rate_value)
            information["vital_signs"]["heart_rate"] = {
                "value": heart_rate_value,
                "unit": heart_rate.group(2) or "bpm"
            }

        if re.search(r"\b(MRI|CT|X-ray|Ultrasound|ECG|CBC|Complete\s+Blood\s+Count)\b", line, re.IGNORECASE):
            information["diagnostic_findings"].append(line)

    reference_pattern = re.compile(
        r"Reference\s+Range\s*:?\s*"
        r"([-+]?\d+(?:\.\d+)?)\s*-\s*"
        r"([-+]?\d+(?:\.\d+)?)\s*([^\s]+)?",
        re.IGNORECASE
    )
    lab_pattern = re.compile(
        r"^([^:]+):\s*([-+]?\d+(?:\.\d+)?)\s*([^\s]+)?\s*$"
    )

    for index, line in enumerate(lines):
        lab_match = lab_pattern.match(line)
        if not lab_match or re.search(r"Blood Pressure|Heart Rate", line, re.IGNORECASE):
            continue

        result = {
            "test_name": lab_match.group(1).strip(),
            "value": float(lab_match.group(2)),
            "unit": lab_match.group(3) or ""
        }

        reference_match = reference_pattern.search(line)
        if index + 1 < len(lines):
            reference_match = reference_match or reference_pattern.search(lines[index + 1])

        if reference_match:
            low = float(reference_match.group(1))
            high = float(reference_match.group(2))
            value = result["value"]
            result["reference_range"] = {"low": low, "high": high}
            result["status"] = "LOW" if value < low else "HIGH" if value > high else "NORMAL"

        if result["value"].is_integer():
            result["value"] = int(result["value"])

        information["lab_results"].append(result)

    return information

@app.route("/api/upload", methods=["POST"])
def upload_report():
    db = None
    cursor = None

    try:
        if "report" not in request.files:
            return jsonify({
                "message": "No file uploaded"
            }), 400

        uploaded_file = request.files["report"]

        if uploaded_file.filename == "":
            return jsonify({
                "message": "No file uploaded"
            }), 400

        user_id_header = request.headers.get("X-User-ID")

        if user_id_header is None or user_id_header == "":
            return jsonify({
                "message": "User ID is required"
            }), 400

        try:
            user_id = int(user_id_header)
        except (TypeError, ValueError):
            return jsonify({
                "message": "Invalid user ID"
            }), 400

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute(
            "SELECT id FROM users WHERE id = %s",
            (user_id,)
        )

        if cursor.fetchone() is None:
            return jsonify({
                "message": "User not found"
            }), 400

        file_extension = os.path.splitext(
            uploaded_file.filename
        )[1].lower()

        if file_extension not in ALLOWED_EXTENSIONS:
            return jsonify({
                "message": "Invalid file type. Allowed types: PDF, JPG, JPEG, PNG"
            }), 400

        uploaded_file.seek(0, os.SEEK_END)
        file_size = uploaded_file.tell()
        uploaded_file.seek(0)

        if file_size > MAX_FILE_SIZE:
            return jsonify({
                "message": "File too large. Maximum size is 10 MB"
            }), 413

        upload_folder = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "uploads"
        )

        os.makedirs(upload_folder, exist_ok=True)

        safe_filename = secure_filename(uploaded_file.filename)

        unique_filename = (
            f"{uuid.uuid4().hex}_{safe_filename}"
        )

        file_path = os.path.join(
            upload_folder,
            unique_filename
        )

        # Save uploaded file
        uploaded_file.save(file_path)

        # Determine report type
        report_type = file_extension.lstrip(".").lower()

        # Extract text from the uploaded report
        raw_text = extract_text_from_file(
            file_path,
            file_extension
        )

        cleaned_text = clean_ocr_text(raw_text)
        medical_information = extract_medical_information(cleaned_text)
        language = get_requested_language()
        medical_information = translate_medical_information(
            medical_information,
            language
        )
        

        # Save report and extracted text
        cursor.execute(
            """
            INSERT INTO reports
            (user_id, file_name, report_type, raw_text)
            VALUES (%s, %s, %s, %s)
            """,
            (
                user_id,
                unique_filename,
                report_type,
                raw_text
            )
        )

                # Get the newly created report ID
        report_id = cursor.lastrowid
        

        # ------------------------------------------------------------
        # CREATE AUTOMATIC REPORT UPLOAD NOTIFICATION
        # ------------------------------------------------------------

        cursor.execute(
            """
            INSERT INTO notifications
            (user_id, type, title, message)
            VALUES (%s, %s, %s, %s)
            """,
            (
                user_id,
                "report",
                "Report Uploaded",
                "Your medical report has been processed and simplified."
            )
        )

        # Save both the report and notification
        db.commit()

        return jsonify({
            "message": "Report uploaded successfully",
            "report_id": report_id,
            "text_length": len(cleaned_text),
            "medical_information": medical_information
        }), 201

    except Exception as e:
        import traceback
        error_msg = str(e)
        print("UPLOAD ERROR:", error_msg)
        print(traceback.format_exc())
        return jsonify({
            "message": "Upload failed: " + error_msg,
            "error": error_msg
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if db is not None:
            db.close()

@app.route("/api/reports", methods=["GET"])
def get_reports():
    db = None
    cursor = None

    try:
        # Get logged-in user ID from frontend
        user_id_header = request.headers.get("X-User-ID")

        if not user_id_header:
            return jsonify({
                "message": "User ID is required"
            }), 400

        try:
            user_id = int(user_id_header)
        except (TypeError, ValueError):
            return jsonify({
                "message": "Invalid user ID"
            }), 400

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Make sure the user exists
        cursor.execute(
            "SELECT id FROM users WHERE id = %s",
            (user_id,)
        )

        if cursor.fetchone() is None:
            return jsonify({
                "message": "User not found"
            }), 404

        # Get ONLY this user's reports
        cursor.execute(
            """
            SELECT
                id,
                user_id,
                file_name,
                report_type,
                created_at
            FROM reports
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (user_id,)
        )

        reports = cursor.fetchall()

        return jsonify({
            "reports": reports,
            "count": len(reports)
        }), 200

    except Exception as e:
        print("GET REPORTS ERROR:", str(e))

        return jsonify({
            "message": "Database error",
            "error": str(e)
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if db is not None:
            db.close()


@app.route("/api/reports/<int:report_id>", methods=["GET"])
def get_report(report_id):
    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, user_id, file_name, report_type, raw_text, created_at
            FROM reports
            WHERE id = %s
            """,
            (report_id,)
        )

        report = cursor.fetchone()

        if report is None:
            return jsonify({
                "message": "Report not found"
            }), 404

        # Extract structured medical parameters from raw_text
        raw_text = report.get("raw_text") or ""

        language = get_requested_language()

        parameters = extract_medical_parameters(raw_text)

        report["parameters"] = translate_parameters(
            parameters,
            language
        )

        cleaned_text = clean_ocr_text(raw_text)

        medical_information = extract_medical_information(
            cleaned_text
        )

        report["medical_information"] = translate_medical_information(
            medical_information,
            language
        )

        report["language"] = language

        return jsonify({
            "report": report
        }), 200

    except Exception as e:
        import traceback
        error_msg = str(e)
        print("GET REPORT ERROR:", error_msg)
        print(traceback.format_exc())
        return jsonify({
            "message": "Database error: " + error_msg,
            "error": error_msg
        }), 500

    finally:
        if cursor is not None:
            cursor.close()
        if db is not None:
            db.close()
@app.route("/api/reports/<int:report_id>", methods=["DELETE"])
def delete_report(report_id):
    try:
        user_id = request.headers.get("X-User-ID")

        if not user_id:
            return jsonify({
                "message": "User ID is required"
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Make sure this report belongs to this user
        cursor.execute(
            """
            SELECT id, file_name
            FROM reports
            WHERE id = %s AND user_id = %s
            """,
            (report_id, user_id)
        )

        report = cursor.fetchone()

        if not report:
            cursor.close()
            conn.close()

            return jsonify({
                "message": "Report not found"
            }), 404

        # Delete database record
        cursor.execute(
            """
            DELETE FROM reports
            WHERE id = %s AND user_id = %s
            """,
            (report_id, user_id)
        )

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "message": "Report deleted successfully",
            "report_id": report_id
        }), 200

    except Exception as e:
        print("DELETE REPORT ERROR:", e)

        try:
            conn.rollback()
            cursor.close()
            conn.close()
        except:
            pass

        return jsonify({
            "message": "Unable to delete report",
            "error": str(e)
        }), 500
# ============================================================
# NOTIFICATIONS
# ============================================================

@app.route("/notifications.html")
def notifications_page():
    return send_from_directory(FRONTEND_DIR, "notifications.html")


@app.route("/api/notifications", methods=["GET"])
def get_notifications():
    user_id = get_authenticated_user_id()

    if user_id is None:
        return jsonify({
            "message": "User authentication required"
        }), 401

    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                type,
                title,
                message,
                is_read,
                created_at
            FROM notifications
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 50
        """, (user_id,))

        notifications = cursor.fetchall()

        # Convert database values into JSON-friendly values
        for notification in notifications:
            notification["is_read"] = bool(notification["is_read"])

            if notification["created_at"]:
                notification["created_at"] = (
                    notification["created_at"].isoformat()
                )

        return jsonify({
            "success": True,
            "notifications": notifications
        }), 200

    except Exception as e:
        print("GET NOTIFICATIONS ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Unable to load notifications",
            "error": str(e)
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if db is not None:
            db.close()


@app.route("/api/notifications/unread-count", methods=["GET"])
def get_unread_notification_count():
    user_id = get_authenticated_user_id()

    if user_id is None:
        return jsonify({
            "message": "User authentication required"
        }), 401

    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM notifications
            WHERE user_id = %s
              AND is_read = FALSE
        """, (user_id,))

        count = cursor.fetchone()[0]

        return jsonify({
            "success": True,
            "unread_count": count
        }), 200

    except Exception as e:
        print("UNREAD COUNT ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Unable to get unread notification count",
            "error": str(e)
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if db is not None:
            db.close()


@app.route("/api/notifications/<int:notification_id>/read", methods=["PUT"])
def mark_notification_as_read(notification_id):
    user_id = get_authenticated_user_id()

    if user_id is None:
        return jsonify({
            "message": "User authentication required"
        }), 401

    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("""
            UPDATE notifications
            SET is_read = TRUE
            WHERE id = %s
              AND user_id = %s
        """, (notification_id, user_id))

        if cursor.rowcount == 0:
            return jsonify({
                "success": False,
                "message": "Notification not found"
            }), 404

        db.commit()

        return jsonify({
            "success": True,
            "message": "Notification marked as read"
        }), 200

    except Exception as e:
        if db:
            db.rollback()

        print("MARK NOTIFICATION READ ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Unable to mark notification as read",
            "error": str(e)
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if db is not None:
            db.close()


@app.route("/api/notifications/mark-all-read", methods=["PUT"])
def mark_all_notifications_as_read():
    user_id = get_authenticated_user_id()

    if user_id is None:
        return jsonify({
            "message": "User authentication required"
        }), 401

    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("""
            UPDATE notifications
            SET is_read = TRUE
            WHERE user_id = %s
              AND is_read = FALSE
        """, (user_id,))

        updated_count = cursor.rowcount

        db.commit()

        return jsonify({
            "success": True,
            "message": "All notifications marked as read",
            "updated_count": updated_count
        }), 200

    except Exception as e:
        if db:
            db.rollback()

        print("MARK ALL NOTIFICATIONS ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Unable to mark all notifications as read",
            "error": str(e)
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if db is not None:
            db.close()


@app.route("/api/notifications", methods=["POST"])
def create_notification():
    user_id = get_authenticated_user_id()

    if user_id is None:
        return jsonify({
            "message": "User authentication required"
        }), 401

    data = request.get_json(silent=True) or {}

    title = (data.get("title") or "").strip()
    message = (data.get("message") or "").strip()
    notification_type = (data.get("type") or "info").strip()

    if not title or not message:
        return jsonify({
            "success": False,
            "message": "Title and message are required"
        }), 400

    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO notifications
            (user_id, type, title, message, is_read)
            VALUES (%s, %s, %s, %s, FALSE)
        """, (
            user_id,
            notification_type,
            title,
            message
        ))

        db.commit()

        notification_id = cursor.lastrowid

        return jsonify({
            "success": True,
            "message": "Notification created successfully",
            "notification_id": notification_id
        }), 201

    except Exception as e:
        if db:
            db.rollback()

        print("CREATE NOTIFICATION ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Unable to create notification",
            "error": str(e)
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if db is not None:
            db.close()    
print("REGISTERED ROUTES:")
for rule in app.url_map.iter_rules():
    print(rule)
@app.route("/api/reports/<int:report_id>/download", methods=["GET"])
def download_report(report_id):
    try:
        user_id = request.headers.get("X-User-ID")

        if not user_id:
            return jsonify({
                "message": "User ID is required"
            }), 401

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, file_name
            FROM reports
            WHERE id = %s AND user_id = %s
        """, (report_id, user_id))

        report = cursor.fetchone()

        cursor.close()
        conn.close()

        if not report:
            return jsonify({
                "message": "Report not found"
            }), 404

        file_name = report["file_name"]

        if not file_name:
            return jsonify({
                "message": "File name not found"
            }), 404

        return send_from_directory(
            app.config["UPLOAD_FOLDER"],
            file_name,
            as_attachment=True
        )

    except Exception as e:
        print("DOWNLOAD ERROR:", e)

        return jsonify({
            "message": "Unable to download report",
            "error": str(e)
        }), 500
@app.route("/api/feedback", methods=["POST"])
def submit_feedback():
    user_id = get_authenticated_user_id()

    if user_id is None:
        return jsonify({
            "message": "User authentication required"
        }), 401

    data = request.get_json(silent=True) or {}

    rating = data.get("rating")
    category = (data.get("category") or "").strip()
    message = (data.get("message") or "").strip()

    # Validate rating
    try:
        rating = int(rating)
    except (TypeError, ValueError):
        return jsonify({
            "message": "Please select a rating"
        }), 400

    if rating < 1 or rating > 5:
        return jsonify({
            "message": "Rating must be between 1 and 5"
        }), 400

    if not category:
        return jsonify({
            "message": "Category is required"
        }), 400

    if not message:
        return jsonify({
            "message": "Feedback message is required"
        }), 400

    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute(
            """
            INSERT INTO feedback
            (user_id, rating, category, message)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, rating, category, message)
        )

        db.commit()

        return jsonify({
            "message": "Feedback submitted successfully"
        }), 201

    except Exception as e:
        if db:
            db.rollback()

        print("FEEDBACK ERROR:", e)

        return jsonify({
            "message": "Unable to submit feedback",
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()    
@app.route('/login.html')
def login_page():
    return send_from_directory(FRONTEND_DIR, 'login.html') 
  
if __name__ == "__main__":
    app.run(debug=True, port=5000)
