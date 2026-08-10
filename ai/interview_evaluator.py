import re

def evaluate_interview_answer(student_answer, target_keywords_str):
    clean_answer = student_answer.strip().lower()
    
    if not clean_answer:
        return {
            'score': 0,
            'relevance': 0,
            'completeness': 0,
            'feedback': ['No answer provided. Please write a detailed response.']
        }

    words = re.findall(r'\b\w+\b', clean_answer)
    word_count = len(words)

    target_keywords = [k.strip().lower() for k in target_keywords_str.split(',') if k.strip()]
    
    matched_keywords = []
    for kw in target_keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', clean_answer):
            matched_keywords.append(kw)

    if target_keywords:
        relevance = int((len(matched_keywords) / len(target_keywords)) * 100)
    else:
        relevance = 70

    if word_count < 15:
        completeness = 40
    elif 15 <= word_count <= 60:
        completeness = 80
    else:
        completeness = 100

    relevance = min(100, relevance)
    completeness = min(100, completeness)

    score = int((relevance * 0.6) + (completeness * 0.4))

    feedback = []
    if matched_keywords:
        feedback.append(f"Good job! Relevant keywords used: {', '.join(matched_keywords)}.")
    else:
        feedback.append("Try to include more specific technical terms and core concepts in your response.")

    if word_count < 20:
        feedback.append("Your answer is brief. Elaborate further with concrete examples.")
    elif word_count > 80:
        feedback.append("Your response is detailed. Keep it concise and focused during real interviews.")
    else:
        feedback.append("Answer length is well-balanced.")

    return {
        'score': min(100, max(0, score)),
        'relevance': relevance,
        'completeness': completeness,
        'feedback': feedback
    }
