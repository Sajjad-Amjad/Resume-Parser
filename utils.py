import re

output_template = {
    'candidate_name': '',
    'contact_info': {
        'location': '',
        'phone_number': '',
        'email_address': '',
        'personal_urls': []
    },
    'job_title': '',
    'bio': '',
    'work_output': [],
    'skills': [],
    'education': [],
    'professional_development': [],  # list of certifications, research publications, awards, open source contributions
    'other_info': [],  # list of language skills, interests, hobbies, extracurricular activities
}


work_experience_template = {
    'company_name': '',
    'job_title': '',
    'start_date': '',
    'end_date': '',
    'description': ''
}

education_template = {
    'qualification': '',
    'establishment': '',
    'country': '',
    'year': ''
}


github_pattern = r'(https://github\.com/[A-Za-z0-9_-]+)'
linkedin_pattern = r'(https://www\.linkedin\.com/in/[A-Za-z0-9_-]+)'
email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'


def extract_emails(content):
    return re.findall(email_pattern, content)


def extract_github_and_linkedin_urls(text):
    # TODO: add personal websites
    github_urls = re.findall(github_pattern, text)
    linkedin_urls = re.findall(linkedin_pattern, text)
    return github_urls + linkedin_urls
