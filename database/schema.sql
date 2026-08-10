CREATE DATABASE IF NOT EXISTS interview_prep_db;
USE interview_prep_db;

-- Students Table
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    college VARCHAR(150) NOT NULL,
    department VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Admins Table
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

-- Resumes Table
CREATE TABLE IF NOT EXISTS resumes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    score INT NOT NULL,
    skills TEXT,
    missing_skills TEXT,
    suggestions TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- Interview Questions Table
CREATE TABLE IF NOT EXISTS interview_questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question TEXT NOT NULL,
    keywords TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Interview Answers Table
CREATE TABLE IF NOT EXISTS interview_answers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    question_id INT NOT NULL,
    answer TEXT NOT NULL,
    score INT NOT NULL,
    relevance INT NOT NULL,
    completeness INT NOT NULL,
    feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES interview_questions(id) ON DELETE CASCADE
);

-- Aptitude Questions Table
CREATE TABLE IF NOT EXISTS aptitude_questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question TEXT NOT NULL,
    option_a VARCHAR(255) NOT NULL,
    option_b VARCHAR(255) NOT NULL,
    option_c VARCHAR(255) NOT NULL,
    option_d VARCHAR(255) NOT NULL,
    correct_answer VARCHAR(1) NOT NULL,
    category VARCHAR(50) NOT NULL
);

-- Aptitude Results Table
CREATE TABLE IF NOT EXISTS aptitude_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    score INT NOT NULL,
    total_questions INT NOT NULL,
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- Overall Performance Table
CREATE TABLE IF NOT EXISTS performance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL UNIQUE,
    resume_score INT DEFAULT 0,
    interview_score INT DEFAULT 0,
    aptitude_score INT DEFAULT 0,
    overall_score INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- Default Admin Account (Username: admin, Password: adminpassword)
INSERT IGNORE INTO admins (id, username, password) VALUES 
(1, 'admin', 'scrypt:32768:8:1$K7e9S6hP9U3a$5db1ed7ca06126cae15f335bcfc99ea9ebbc9df602883015baedeb559cefb1c136340f1aef20822180bd9bf2bf4bfdf96f7e4465df5efc4f746ef32a4e235a90');

-- Sample Interview Questions
INSERT IGNORE INTO interview_questions (id, question, keywords) VALUES
(1, 'Tell me about yourself and your academic background.', 'bba, computer, software, developer, python, project, college, student, learning, goal'),
(2, 'What are your key technical strengths?', 'python, sql, database, html, css, flask, javascript, logic, problem solving, web'),
(3, 'Describe a challenge you faced during a project and how you solved it.', 'challenge, solved, database, bug, team, fixed, learned, algorithm, research, feature'),
(4, 'Where do you see yourself in five years?', 'developer, lead, learning, career, company, growth, skill, technology, professional, industry');

-- Sample Aptitude Questions
INSERT IGNORE INTO aptitude_questions (id, question, option_a, option_b, option_c, option_d, correct_answer, category) VALUES
(1, 'If 20% of a number is 40, what is the total number?', '100', '150', '200', '250', 'C', 'Quantitative Aptitude'),
(2, 'Which number comes next in the sequence: 2, 6, 12, 20, 30, ...?', '36', '40', '42', '48', 'C', 'Logical Reasoning'),
(3, 'Find the antonym of the word "EXPAND".', 'Shrink', 'Grow', 'Extend', 'Widen', 'A', 'Verbal Ability'),
(4, 'A train running at 60 km/h passes a pole in 9 seconds. What is the length of the train in meters?', '120 m', '150 m', '180 m', '200 m', 'B', 'Quantitative Aptitude'),
(5, 'Point out the correctly spelled word.', 'Accomodation', 'Accommodation', 'Acommodation', 'Accomodasion', 'B', 'Verbal Ability');
