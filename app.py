import time

import streamlit as st

from parser import ResumeManager


def main():
    st.title("My Resume Parser")
    resume_f = st.file_uploader("file upload", type="pdf", label_visibility='hidden')

    btn = st.button("Process")

    if btn:
        with st.spinner("Processing ..."):
            start_time = time.time()
            resume_manager = ResumeManager(resume_f, 'gpt-3.5-turbo-1106', extension='.pdf')
            resume_manager.process_file()
            st.write(resume_manager.output)
            end_time = time.time()
            seconds = end_time - start_time
            m, s = divmod(seconds, 60)
            st.write(f"Total time {int(m)} min {int(s)} seconds")


if __name__ == "__main__":
    main()
