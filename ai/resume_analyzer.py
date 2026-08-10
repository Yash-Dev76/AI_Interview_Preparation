import os
import re
from pypdf import PdfReader

ALL_SKILLS = [
    'python', 'java', 'c++', 'html', 'css', 'javascript', 'bootstrap', 
    'sql', 'mysql', 'flask', 'django', 'git', 'github', 'rest api', 
    'data structures', 'communication', 'problem solving', 'machine learning'
]

REQUIRED_SECTIONS = ['education', 'skills', 'projects', 'certifications', 'experience']

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + " "
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text.lower()

def analyze_resume(file_path):
    text = extract_text_from_pdf(file_path)
    
    if not text.strip():
        return {
            'score': 0,
            'detected_skills': [],
            'missing_skills': ALL_SKILLS[:5],
            'suggestions': ['The uploaded PDF text could not be extracted. Ensure it is not a scanned image.']
        }

    detected_skills = []
    missing_skills = []
    
    for skill in ALL_SKILLS:
        if re.search(r'\b' + re.escape(skill) + r'\b', text):
            detected_skills.append(skill.title())
        else:
            missing_skills.append(skill.title())

    found_sections = []
    for section in REQUIRED_SECTIONS:
        if re.search(r'\b' + re.escape(section) + r'\b', text):
            found_sections.append(section)

    section_score = (len(found_sections) / len(REQUIRED_SECTIONS)) * 50
    skill_score = min(50, (len(detected_skills) / 8) * 50)
    total_score = int(section_score + skill_score)

    suggestions = []
    if len(found_sections) < len(REQUIRED_SECTIONS):
        missing_sec = [s.title() for s in REQUIRED_SECTIONS if s not in found_sections]
        suggestions.append(f"Add missing standard resume sections: {', '.join(missing_sec)}.")
    
    if len(detected_skills) < 5:
        suggestions.append("Include more specific technical skills and tools related to your domain.")
        
    suggestions.append("Ensure measurable project descriptions with tools and technologies used.")
    suggestions.append("Add links to GitHub profiles or live project demos.")

    return {
        'score': min(100, max(0, total_score)),
        'detected_skills': detected_skills if detected_skills else ["None detected"],
        'missing_skills': missing_skills[:6],
        'suggestions': suggestions
    }
