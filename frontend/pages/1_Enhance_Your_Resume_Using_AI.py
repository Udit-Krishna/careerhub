import streamlit as st
import asyncio
import os
import requests

main_page = __import__("Home_Page")

if st.session_state.user_email and st.session_state.user_name:
    
    st.title("Enhance your Resume using AI")
    # Sidebar for navigation
    tabs = ["Education", "Work Experience", "Projects"]
    selected_tab = st.sidebar.radio("Select Resume Section", tabs)
       
     # Education Tab
    if selected_tab == "Education":
        st.subheader("Education Details")
        # Display existing education entries
        for i, edu in enumerate(st.session_state.education):
            with st.expander(f"Education {i+1}", expanded=True):
                edu["degree"] = st.text_input("Degree", edu.get("degree", ""), key=f"degree_{i}", disabled=True)
                edu["university"] = st.text_input("University / College", edu.get("university", ""), key=f"university_{i}", disabled=True)
                edu["start_year"] = st.number_input("Year of Start", 1900, 2100, edu.get("start_year", 2020), key=f"start_year_{i}", disabled=True)
                edu["graduation_year"] = st.number_input("Year of Graduation", 1900, 2100, edu.get("graduation_year", 2024), key=f"grad_year_{i}", disabled=True)
                edu["gpa"] = st.number_input("CGPA", 0.0, 10.0, edu.get("gpa", 0.0), step=0.1, key=f"gpa_{i}", disabled=True)
                edu["description"] = st.text_area("Description (Write in multiple lines for bulleted points)", edu.get("description", ""), key=f"description_{i}", disabled=True)
                if st.button("Enhance Education Description Using AI", type='secondary', key=f'edu-desc-ai-button-{i}'):
                    st.write(edu["description"])
        

    # Work Experience Tab
    elif selected_tab == "Work Experience":
        st.subheader("Work Experience")
        for i, work in enumerate(st.session_state.work_experience):
            with st.expander(f"Work Experience {i+1}", expanded=True):
                work["job_title"] = st.text_input("Job Title", work.get("job_title", ""), key=f"job_title_{i}", disabled=True)
                work["company"] = st.text_input("Company Name", work.get("company", ""), key=f"company_{i}", disabled=True)
                work["location"] = st.text_input("Location", work.get("location", ""), key=f"location_{i}", disabled=True)
                work["start_year"] = st.number_input("Year of Start", 1900, 2100, work.get("start_year", 2020), key=f"start_year_{i}", disabled=True)
                work["end_year"] = st.number_input("Year of End", 1900, 2100, work.get("end_year", 2024), key=f"end_year_{i}", disabled=True)
                work["work_desc"] = st.text_area("Job Description (Write in multiple lines for bulleted points)", work.get("work_desc", ""), key=f"work_desc_{i}", disabled=True)
                if st.button("Enhance Job Description Using AI", type='secondary', key=f'work-desc-ai-button-{i}'):
                    st.write(work["work_desc"])
                    requests.post("http://localhost:8000/ai-resume-enhance",
                            json={"category": 'work', "content": work},
                    )

    # Projects Tab
    elif selected_tab == "Projects":
        st.subheader("Projects")
        for i, proj in enumerate(st.session_state.projects):
            with st.expander(f"Project {i+1}", expanded=True):
                proj["project_name"] = st.text_input("Project Name", proj.get("project_name", ""), key=f"project_name_{i}", disabled=True)
                proj["project_tech"] = st.text_area("Technologies Used", proj.get("project_tech", ""), key=f"project_tech_{i}", disabled=True)
                proj["project_link"] = st.text_input("Project URL", proj.get("project_link", ""), key=f"project_link_{i}", disabled=True)
                proj["project_desc"] = st.text_area("Project Description (Write in multiple lines for bulleted points)", proj.get("project_desc", ""), key=f"project_desc_{i}", disabled=True)                
                if st.button("Enhance Project Description Using AI", type='secondary', key=f'proj-desc-ai-button-{i}'):
                    st.write(proj["project_desc"])
    
    # Submit Button
    if st.button("Save Details", type="primary"):
        st.success("Your details have been saved successfully! 🎉")
        data = {}
        data['personal_details'] = st.session_state['personal_details']
        data['education'] = st.session_state['education']
        data['work_experience'] = st.session_state['work_experience']
        data['projects'] = st.session_state['projects']
        data['skills'] = st.session_state['skills']
        requests.post("http://localhost:8000/update-details",
            json={"unique_id": st.session_state.user_email, "content": data},
        )

else:
    st.switch_page("Home_Page.py")