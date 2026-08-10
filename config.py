import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'bba_ca_ai_interview_prep_system_2024_key'
    
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DB_PATH = os.path.join(BASE_DIR, 'database', 'interview_prep.db')
    
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'pdf'}
