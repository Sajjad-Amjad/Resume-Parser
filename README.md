# LLM Powered Resume Parser Tool

This tool is designed to simplify the process of extracting key information from resumes in PDF and Word formats. It provides both a command line interface (CLI) script and a Streamlit web application for user-friendly interaction.

It relies on the OpenAI API, and an API key is required for proper functionality. Make sure to secure your API key and follow OpenAI's usage guidelines.

## Getting Started

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Sajjad-Amjad/Resume-Parser.git
   cd Resume-Parser
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Environment Variables:**
   - Create a `.env` file in the root directory.
   - Add your OpenAI API key to the `.env` file:
     ```dotenv
     OPENAI_API_KEY=your_api_key_here
     ```

## Usage

### CLI Script

Run the following command in the terminal:

```bash
python3 parser.py path/to/resume.pdf
```

### Streamlit Web Application

Run the following command in the terminal:

```bash
streamlit run app.py
```

Access the application in your web browser at [http://localhost:8501](http://localhost:8501) to upload your resume.

## Output

The tool extracts and parses any resume in the following output class model:

```
## Ouput Pydantic models:
class Output(BaseModel):
    'candidate_name': str,
    'job_title': str,
    'bio': str,
    'contact_info': ContactInfo,
    'work_output': List[WorkEperience],
    'skills': List[str],
    'education': List[Education],
    'professional_development': List[str],  # list of certifications, research publications, awards, open source contributions
    'other_info': List[str],  # list of language skills, interests, hobbies, extracurricular activities

class ContactInfo(BaseModel):
    'location': str,
    'phone_number': str,
    'email_address': str,
    'personal_urls': List[str]

class WorkEperience(BaseModel):
    'company_name': str,
    'job_title': str,
    'start_date': str,
    'end_date': str,
    'description': str

class WorkEperience(BaseModel):
    'qualification': str,
    'establishment': str,
    'country': str,
    'year': str,
```
