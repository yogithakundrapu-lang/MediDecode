-- ==========================================================================
-- MediDecode — Database Schema
-- Run: mysql -u root -p < database.sql
-- ==========================================================================

CREATE DATABASE IF NOT EXISTS medidecode CHARACTER SET utf8mb4;
USE medidecode;

-- ---------- Users ----------
CREATE TABLE IF NOT EXISTS users (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    name                VARCHAR(120)    NOT NULL,
    email               VARCHAR(150)    NOT NULL UNIQUE,
    password_hash       VARCHAR(255)    NOT NULL,
    age                 INT,
    gender              VARCHAR(20),
    blood_group         VARCHAR(5),
    height_cm           DECIMAL(5,2),
    weight_kg           DECIMAL(5,2),
    phone               VARCHAR(20),
    address             TEXT,
    emergency_contact   VARCHAR(150),
    medical_history     TEXT,
    preferred_language  VARCHAR(5)      DEFAULT 'en',
    profile_photo_url   VARCHAR(255),
    account_type        VARCHAR(20)     DEFAULT 'standard',
    created_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ---------- User settings ----------
CREATE TABLE IF NOT EXISTS user_settings (
    id                           INT AUTO_INCREMENT PRIMARY KEY,
    user_id                      INT NOT NULL UNIQUE,
    dark_mode                    BOOLEAN DEFAULT FALSE,
    notify_report_updates        BOOLEAN DEFAULT TRUE,
    notify_medicine_reminders    BOOLEAN DEFAULT TRUE,
    notify_health_alerts         BOOLEAN DEFAULT TRUE,
    share_data_for_research      BOOLEAN DEFAULT FALSE,
    two_factor_authentication    BOOLEAN DEFAULT FALSE,
    updated_at                   TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------- Reports ----------
CREATE TABLE IF NOT EXISTS reports (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT             NOT NULL,
    file_name       VARCHAR(255)    NOT NULL,
    report_type     VARCHAR(60),
    raw_text        LONGTEXT,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------- Report parameters (per-value breakdown) ----------
CREATE TABLE IF NOT EXISTS report_parameters (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    report_id           INT             NOT NULL,
    parameter_name      VARCHAR(100)    NOT NULL,
    detected_value      VARCHAR(50),
    unit                VARCHAR(30),
    normal_range        VARCHAR(50),
    simple_meaning      TEXT,
    risk_level          VARCHAR(20),   -- Normal / Slightly High / Slightly Low / High / Low
    foods_to_eat        TEXT,
    foods_to_avoid      TEXT,
    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------- Health metrics history (for graphs) ----------
CREATE TABLE IF NOT EXISTS health_metrics (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT             NOT NULL,
    report_id       INT,
    bmi             DECIMAL(5,2),
    blood_pressure  VARCHAR(15),
    sugar_level     DECIMAL(6,2),
    cholesterol     DECIMAL(6,2),
    health_score    INT,
    recorded_at     TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ---------- Notifications ----------
CREATE TABLE IF NOT EXISTS notifications (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT             NOT NULL,
    type        VARCHAR(30)     NOT NULL, -- report_uploaded / health_alert / medicine_reminder / appointment
    title       VARCHAR(150)    NOT NULL,
    message     TEXT,
    is_read     BOOLEAN         DEFAULT FALSE,
    created_at  TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------- Feedback ----------
CREATE TABLE IF NOT EXISTS feedback (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT             NOT NULL,
    rating      INT,
    category    VARCHAR(60),
    message     TEXT,
    created_at  TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------- Medicine reminders ----------
CREATE TABLE IF NOT EXISTS medicine_reminders (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT             NOT NULL,
    medicine    VARCHAR(120)    NOT NULL,
    dosage      VARCHAR(60),
    time_of_day TIME,
    active      BOOLEAN         DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------- Reference ranges (used by the OCR/simplifier engine) ----------
CREATE TABLE IF NOT EXISTS parameter_reference (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    parameter_name      VARCHAR(100)    NOT NULL UNIQUE,
    unit                VARCHAR(30),
    low_bound           DECIMAL(8,2),
    high_bound          DECIMAL(8,2),
    simple_meaning      TEXT,
    low_meaning         TEXT,
    high_meaning        TEXT,
    foods_to_eat        TEXT,
    foods_to_avoid      TEXT
) ENGINE=InnoDB;

INSERT INTO parameter_reference (parameter_name, unit, low_bound, high_bound, simple_meaning, low_meaning, high_meaning, foods_to_eat, foods_to_avoid) VALUES
('Hemoglobin', 'g/dL', 13.0, 17.0, 'Carries oxygen in your blood.', 'Low hemoglobin can cause tiredness and weakness (anemia).', 'High hemoglobin can thicken the blood.', 'Leafy greens, red meat, beans, iron-fortified cereal', 'Excess tea/coffee with meals (blocks iron absorption)'),
('Blood Sugar (Fasting)', 'mg/dL', 70.0, 99.0, 'Measures glucose in your blood after fasting.', 'Low blood sugar can cause dizziness and fatigue.', 'High blood sugar is an early sign of diabetes risk.', 'Whole grains, vegetables, nuts', 'Sugary drinks, refined carbs, sweets'),
('Cholesterol (Total)', 'mg/dL', 0.0, 200.0, 'A fat used to build healthy cells.', NULL, 'High cholesterol raises heart disease risk.', 'Oats, nuts, olive oil, fatty fish', 'Fried food, red meat, butter'),
('Platelets', 'Lakh/µL', 1.5, 4.5, 'Help your blood clot properly.', 'Low platelets can increase bruising and bleeding risk.', 'High platelets can increase clotting risk.', 'Leafy greens, citrus fruits', 'Excessive alcohol'),
('Vitamin D', 'ng/mL', 30.0, 100.0, 'Supports bone health and immunity.', 'Low Vitamin D can cause fatigue and weak bones.', NULL, 'Eggs, fortified milk, sunlight exposure', 'Excessive caffeine (reduces absorption)');
