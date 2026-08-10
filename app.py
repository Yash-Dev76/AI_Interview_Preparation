import os
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from config import Config
from ai.resume_analyzer import analyze_resume
from ai.interview_evaluator import evaluate_interview_answer

app = Flask(__name__)
app.config.from_object(Config)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db():
    return mysql.connector.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB']
    )

def update_overall_performance(student_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT score FROM resumes WHERE student_id = %s ORDER BY uploaded_at DESC LIMIT 1", (student_id,))
    res = cursor.fetchone()
    resume_score = res['score'] if res else 0

    cursor.execute("SELECT AVG(score) as avg_score FROM interview_answers WHERE student_id = %s", (student_id,))
    res = cursor.fetchone()
    interview_score = int(res['avg_score']) if res and res['avg_score'] is not None else 0

    cursor.execute("SELECT score, total_questions FROM aptitude_results WHERE student_id = %s ORDER BY attempted_at DESC LIMIT 1", (student_id,))
    res = cursor.fetchone()
    aptitude_score = int((res['score'] / res['total_questions']) * 100) if res and res['total_questions'] > 0 else 0

    overall_score = int((resume_score + interview_score + aptitude_score) / 3)

    cursor.execute("""
        INSERT INTO performance (student_id, resume_score, interview_score, aptitude_score, overall_score)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
        resume_score=%s, interview_score=%s, aptitude_score=%s, overall_score=%s
    """, (student_id, resume_score, interview_score, aptitude_score, overall_score,
          resume_score, interview_score, aptitude_score, overall_score))
    
    db.commit()
    cursor.close()
    db.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        college = request.form['college'].strip()
        department = request.form['department'].strip()

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)
        
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO students (name, email, password, college, department)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, email, hashed_pw, college, department))
            db.commit()
            cursor.close()
            db.close()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.Error:
            flash('Error: Email might already be registered.', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students WHERE email = %s", (email,))
        student = cursor.fetchone()
        cursor.close()
        db.close()

        if student and check_password_hash(student['password'], password):
            session['student_id'] = student['id']
            session['student_name'] = student['name']
            flash('Welcome back!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'student_id' not in session:
        flash('Please login to access your dashboard.', 'warning')
        return redirect(url_for('login'))

    student_id = session['student_id']
    update_overall_performance(student_id)

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM performance WHERE student_id = %s", (student_id,))
    perf = cursor.fetchone()
    cursor.close()
    db.close()

    return render_template('dashboard.html', perf=perf)

@app.route('/profile')
def profile():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT name, email, college, department, created_at FROM students WHERE id = %s", (session['student_id'],))
    student = cursor.fetchone()
    cursor.close()
    db.close()

    return render_template('profile.html', student=student)

@app.route('/resume', methods=['GET', 'POST'])
def resume():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'resume_file' not in request.files:
            flash('No file selected.', 'danger')
            return redirect(request.url)

        file = request.files['resume_file']
        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(request.url)

        if file and file.filename.lower().endswith('.pdf'):
            filename = secure_filename(f"student_{session['student_id']}_{file.filename}")
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)

            results = analyze_resume(save_path)

            skills_str = ", ".join(results['detected_skills'])
            missing_str = ", ".join(results['missing_skills'])
            suggestions_str = " | ".join(results['suggestions'])

            db = get_db()
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO resumes (student_id, filename, score, skills, missing_skills, suggestions)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (session['student_id'], filename, results['score'], skills_str, missing_str, suggestions_str))
            db.commit()
            cursor.close()
            db.close()

            update_overall_performance(session['student_id'])
            return render_template('resume_result.html', results=results)
        else:
            flash('Only PDF files are allowed!', 'danger')

    return render_template('resume.html')

@app.route('/interview', methods=['GET', 'POST'])
def interview():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        question_id = request.form['question_id']
        answer = request.form['answer']

        cursor.execute("SELECT keywords FROM interview_questions WHERE id = %s", (question_id,))
        q = cursor.fetchone()

        if q:
            evaluation = evaluate_interview_answer(answer, q['keywords'])
            feedback_str = " ".join(evaluation['feedback'])

            cursor.execute("""
                INSERT INTO interview_answers (student_id, question_id, answer, score, relevance, completeness, feedback)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (session['student_id'], question_id, answer, evaluation['score'], evaluation['relevance'], evaluation['completeness'], feedback_str))
            db.commit()

            update_overall_performance(session['student_id'])
            cursor.close()
            db.close()
            return render_template('interview_result.html', eval=evaluation, answer=answer)

    cursor.execute("SELECT * FROM interview_questions ORDER BY RAND() LIMIT 1")
    question = cursor.fetchone()
    cursor.close()
    db.close()

    return render_template('interview.html', question=question)

@app.route('/aptitude', methods=['GET', 'POST'])
def aptitude():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        cursor.execute("SELECT id, correct_answer FROM aptitude_questions")
        questions = cursor.fetchall()

        score = 0
        total = len(questions)

        for q in questions:
            selected_option = request.form.get(f"q_{q['id']}")
            if selected_option and selected_option == q['correct_answer']:
                score += 1

        cursor.execute("""
            INSERT INTO aptitude_results (student_id, score, total_questions)
            VALUES (%s, %s, %s)
        """, (session['student_id'], score, total))
        db.commit()

        update_overall_performance(session['student_id'])
        cursor.close()
        db.close()
        return render_template('aptitude_result.html', score=score, total=total)

    cursor.execute("SELECT * FROM aptitude_questions LIMIT 10")
    questions = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('aptitude.html', questions=questions)

@app.route('/performance')
def performance():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM performance WHERE student_id = %s", (session['student_id'],))
    perf = cursor.fetchone()
    cursor.close()
    db.close()

    return render_template('performance.html', perf=perf)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admins WHERE username = %s", (username,))
        admin = cursor.fetchone()
        cursor.close()
        db.close()

        if admin and check_password_hash(admin['password'], password):
            session['admin_id'] = admin['id']
            session['admin_user'] = admin['username']
            flash('Admin authentication successful.', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials.', 'danger')

    return render_template('admin/login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) as total_students FROM students")
    students_cnt = cursor.fetchone()['total_students']

    cursor.execute("SELECT COUNT(*) as total_iq FROM interview_questions")
    iq_cnt = cursor.fetchone()['total_iq']

    cursor.execute("SELECT COUNT(*) as total_aq FROM aptitude_questions")
    aq_cnt = cursor.fetchone()['total_aq']
    cursor.close()
    db.close()

    return render_template('admin/dashboard.html', students_cnt=students_cnt, iq_cnt=iq_cnt, aq_cnt=aq_cnt)

@app.route('/admin/students')
def admin_students():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students ORDER BY created_at DESC")
    students = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('admin/students.html', students=students)

@app.route('/admin/interview-questions', methods=['GET', 'POST'])
def admin_interview_questions():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        question = request.form['question'].strip()
        keywords = request.form['keywords'].strip()
        cursor.execute("INSERT INTO interview_questions (question, keywords) VALUES (%s, %s)", (question, keywords))
        db.commit()
        flash('Interview question added.', 'success')

    cursor.execute("SELECT * FROM interview_questions ORDER BY id DESC")
    questions = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('admin/interview_questions.html', questions=questions)

@app.route('/admin/delete-interview-question/<int:qid>')
def delete_interview_question(qid):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM interview_questions WHERE id = %s", (qid,))
    db.commit()
    cursor.close()
    db.close()
    flash('Question deleted.', 'info')
    return redirect(url_for('admin_interview_questions'))

@app.route('/admin/aptitude-questions', methods=['GET', 'POST'])
def admin_aptitude_questions():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        question = request.form['question'].strip()
        opt_a = request.form['option_a'].strip()
        opt_b = request.form['option_b'].strip()
        opt_c = request.form['option_c'].strip()
        opt_d = request.form['option_d'].strip()
        correct = request.form['correct_answer'].strip().upper()
        category = request.form['category'].strip()

        cursor.execute("""
            INSERT INTO aptitude_questions (question, option_a, option_b, option_c, option_d, correct_answer, category)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (question, opt_a, opt_b, opt_c, opt_d, correct, category))
        db.commit()
        flash('Aptitude question added.', 'success')

    cursor.execute("SELECT * FROM aptitude_questions ORDER BY id DESC")
    questions = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('admin/aptitude_questions.html', questions=questions)

@app.route('/admin/delete-aptitude-question/<int:qid>')
def delete_aptitude_question(qid):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM aptitude_questions WHERE id = %s", (qid,))
    db.commit()
    cursor.close()
    db.close()
    flash('Question deleted.', 'info')
    return redirect(url_for('admin_aptitude_questions'))

@app.route('/admin/results')
def admin_results():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*, s.name, s.email, s.college 
        FROM performance p
        JOIN students s ON p.student_id = s.id
        ORDER BY p.overall_score DESC
    """)
    results = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('admin/results.html', results=results)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Admin logged out.', 'info')
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(debug=True)
