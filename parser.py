import argparse
import json
import logging
import os
import sys
import time
from copy import deepcopy
from pathlib import Path

import docx
import openai
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from langchain.chains.openai_tools import create_extraction_chain_pydantic
from langchain.chat_models import ChatOpenAI
from openai import OpenAI

import threading

from pydantic_models_prompts import Education, WorkExperience
from pydantic_models_prompts import (
    basic_details_prompt, fallback_basic_info_prompt,
    skills_prompt, fallback_skills_prompt,
    fallback_education_prompt, companies_prompt, work_experience_prompt
)
from utils import extract_emails, extract_github_and_linkedin_urls
from utils import output_template

logger = logging.getLogger()
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)

logger.addHandler(stream_handler)

load_dotenv()


class ResumeManager:
    def __init__(self, resume_f, model_name, extension=None):
        self.output = deepcopy(output_template)
        self.resume = get_resume_content(resume_f, extension)
        self.model_name = model_name
        self.model = ChatOpenAI(model=model_name, request_timeout=5, max_retries=1)
        self.companies = []

    def process_file(self):
        all_threads = []
        for target in [
            self.extract_work_experience(),
            self.extract_basic_info(),
            self.extract_education(),
            self.extract_skills()
        ]:
            thread = threading.Thread(target=target)
            all_threads.append(thread)
            thread.start()

        for thread in all_threads:
            thread.join()

    def extract_pydantic(self, target):
        start = time.time()
        chain = create_extraction_chain_pydantic(target, self.model)

        result = chain.invoke({"input": self.resume})
        end = time.time()
        seconds = end - start
        return result, seconds

    def query_model(self, query, json_mode=True):
        start = time.time()

        if json_mode:
            completion = OpenAI().chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user",
                           "content": query}],
                response_format={'type': 'json_object'},
                timeout=8,
            )

        else:
            completion = OpenAI().chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user",
                           "content": query}],
                timeout=8,
            )

        end = time.time()
        seconds = end - start
        result = completion.choices[0].message.content
        return result, seconds

    def extract_basic_info(self):
        query = basic_details_prompt.format(resume=self.resume)
        output, seconds = self.query_model(query)
        output = json.loads(output)
        logger.debug(f"# Basic Info Extract:\n{output}")
        logger.info(f"# Basic Info Extraction took {seconds} seconds")

        try:
            self.output['candidate_name'] = output['name']
        except KeyError:
            query = fallback_basic_info_prompt.format(query='name', resume=self.resume)
            name, _ = self.query_model(query, json_mode=False)
            self.output['candidate_name'] = name

        try:
            self.output['job_title'] = output['job_title']
        except KeyError:
            query = fallback_basic_info_prompt.format(query='current or last job title', resume=self.resume)
            title, _ = self.query_model(query, json_mode=False)
            self.output['job_title'] = title

        try:
            self.output['bio'] = output['bio']
        except KeyError:
            pass

        if 'location' in output:
            self.output['contact_info']['location'] = output['location']
        if 'phone' in output:
            self.output['contact_info']['phone_number'] = output['phone']

        self.output['contact_info']['email_address'] = extract_emails(self.resume)
        self.output['contact_info']['personal_urls'] = extract_github_and_linkedin_urls(self.resume)

    def extract_skills(self):
        try:
            query = skills_prompt.format(resume=self.resume)
            output, seconds = self.query_model(query)
            output = json.loads(output)
            logger.debug(f"# Skills Extract:\n{output}")
            logger.info(f"# Skills Extraction took {seconds} seconds")
            self.output['skills'] = output['skills']
            if 'professional_development' in output:
                self.output['professional_development'] = output['professional_development']
            if 'other' in output:
                self.output['other_info'] = output['other']

        except openai.APITimeoutError:
            logger.warning("Skills extraction timed out")
            query = fallback_skills_prompt.format(self.resume)
            output, seconds = self.query_model(query, json_mode=False)
            logger.debug(f"# Skills Extract:\n{output}")
            logger.info(f"# Skills Extraction took {seconds} seconds")
            self.output['skills'] = output

    def extract_education(self):
        try:
            output, seconds = self.extract_pydantic(Education)
            logger.debug(f"# Education Extract:\n{output}")
            logger.info(f"# Education Extraction took {seconds} seconds")
            self.output['education'] = [json.loads(x.json().encode('utf-8')) for x in output]

        except openai.APITimeoutError:
            logger.warning("Education extraction timed out")
            query = fallback_education_prompt.format(resume=self.resume)
            output, seconds = self.query_model(query, json_mode=False)
            logger.debug(f"# Education Extract:\n{output}")
            logger.info(f"# Education Extraction took {seconds} seconds")
            self.output['education'] = output

    def extract_work_experience(self):
        try:
            output, seconds = self.extract_pydantic(WorkExperience)
            logger.debug(f"# Work Experience Extract:\n{output}")
            logger.info(f"# Work Experience Extraction took {seconds} seconds")
            self.output['work_output'] = [json.loads(x.json().encode('utf-8')) for x in output]
        except openai.APITimeoutError:
            logger.warning("Work extraction timed out")
            self.fallback_extract_work_experience()

    def fallback_extract_work_experience(self):
        query = companies_prompt.format(resume=self.resume)
        output, _ = self.query_model(query, json_mode=False)

        all_threads = []

        for line in output.split('\n'):
            if "answer" in line.lower():
                continue
            entry = line.split(',')
            company_name = entry[0].rstrip()
            if not company_name:
                continue
            try:
                role = entry[1].rstrip()
            except IndexError:
                role = ""

            thread = threading.Thread(target=self.get_intermediary_work_experience, args=(company_name, role))
            all_threads.append(thread)
            thread.start()

        for thread in all_threads:
            thread.join()

    def get_intermediary_work_experience(self, company_name, role):
        query = work_experience_prompt.format(resume=self.resume, role=role, company=company_name)
        output, seconds = self.query_model(query, json_mode=True)
        parsed_output = json.loads(output, strict=False)
        logger.debug(f"# Intermediary Work Experience Extract:\n{parsed_output}")
        logger.info(f"# Intermediary Work Experience Extraction took {seconds} seconds")
        self.output['work_output'].append(parsed_output)


def get_resume_content(file_path, extension=None):
    if not extension:
        extension = os.path.splitext(file_path)[1]
    if extension == '.pdf':
        pdf_reader = PdfReader(file_path)
        content = ""
        for page in pdf_reader.pages:
            text = page.extract_text()
            for line in text.split('\n'):
                line = line.rstrip()
                if line:
                    content += line
                    content += '\n'
    elif extension in ['.docx', '.doc']:
        doc = docx.Document(file_path)
        content = ""
        for paragraph in doc.paragraphs:
            content += paragraph.text + "\n"

    else:
        sys.exit(f"Unsupported file type {extension}")
    return content


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse a Resume with Open AI GPT models")
    parser.add_argument("file_path", help="Path to the resume, accepted types .pdf or .docx")
    parser.add_argument("--model_name", default='gpt-3.5-turbo-1106',
                        help="Name of the model, default to gpt-3.5-turbo-1106")

    args = parser.parse_args()
    logging.info(f"Processing {args.file_path}")

    resume_manager = ResumeManager(args.file_path, args.model_name)

    start_time = time.time()
    resume_manager.process_file()
    end_time = time.time()

    resume_name = Path(args.file_path).stem
    output_file_path = f"parsed_outputs/{resume_name}_output.json"
    with open(output_file_path, 'w') as file:
        json.dump(resume_manager.output, file, indent=2)

    print(json.dumps(resume_manager.output, indent=2))

    seconds = end_time - start_time
    m, s = divmod(seconds, 60)
    logger.info(f"Total time {int(m)} min {int(s)} seconds")