import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

# Initialize session state variables
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
    # Try to load tasks from Google Sheets
    try:
        from sheets_integration import load_from_sheets
        success, loaded_tasks = load_from_sheets()
        if success:
            st.session_state.tasks = loaded_tasks
    except Exception as e:
        st.error(f"Failed to load tasks from Google Sheets: {str(e)}")

# Set page configuration
st.set_page_config(
    page_title="Task Tracker",
    page_icon="✅",
    layout="wide"
)

# Title and description
st.title("Task Tracker")
st.markdown("Track your tasks and synchronize with Google Sheets")

# Create two columns for task input and controls
col1, col2 = st.columns(2)

# Delete all tasks button
if st.session_state.tasks:  # Only show if there are tasks
    if st.button("🗑️ Delete All Tasks", type="secondary"):
        try:
            from sheets_integration import delete_from_sheets
            case_numbers = [task['case_number'] for task in st.session_state.tasks]
            success, message = delete_from_sheets(case_numbers)
            if success:
                st.session_state.tasks = []
                st.success("All tasks have been deleted!")
                st.rerun()
            else:
                st.error(f"Failed to delete tasks: {message}")
        except Exception as e:
            st.error(f"Error deleting tasks: {str(e)}")

# Task input form
with col1:
    with st.form(key="task_form"):
        task_name = st.text_input("Task Name")
        case_number = st.text_input("Case Number")
        submit_button = st.form_submit_button("Add Task")
        
        if submit_button and task_name and case_number:
            # Check if task with same case number exists
            existing_task = None
            for task in st.session_state.tasks:
                if task['case_number'] == case_number:
                    existing_task = task
                    break
            
            if existing_task:
                st.error(f"Task with Case Number '{case_number}' already exists!")
            else:
                new_task = {
                    "task_name": task_name,
                    "case_number": case_number,
                    "start_time": None,
                    "stop_time": None,
                    "total_time": 0,  # in seconds
                    "is_running": False,
                    "previous_time": 0  # Store previous accumulated time
                }
                st.session_state.tasks.append(new_task)
                st.success(f"Task '{task_name}' added successfully!")

# Display tasks
with col2:
    st.subheader("Sync to Google Sheets")
    if st.button("Synch to GS"):
        try:
            from sheets_integration import sync_to_sheets
            success, message = sync_to_sheets(st.session_state.tasks)
            if success:
                st.success(message)
            else:
                st.error(message)
        except Exception as e:
            st.error(f"Failed to sync: {str(e)}")

# Display task list
st.subheader("Task List")
for idx, task in enumerate(st.session_state.tasks):
    col_info, col_buttons = st.columns([3, 1])
    
    with col_info:
        st.write(f"**Task:** {task['task_name']} (Case: {task['case_number']})")
        if task['start_time']:
            st.write(f"Started: {task['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        if task['stop_time']:
            st.write(f"Last Stopped: {task['stop_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        total_hours = task['total_time'] / 3600
        st.write(f"Total Time: {total_hours:.2f} hours")
    
    with col_buttons:
        # Create a vertical layout for buttons
        button_col1, button_col2 = st.columns(2)
        
        with button_col1:
            if not task['is_running']:
                if st.button("▶️", key=f"start_{idx}", help="Start Task"):
                    task['is_running'] = True
                    # Always update start_time when starting a new session
                    task['start_time'] = datetime.now()
                    # Store the current total time before starting new session
                    task['previous_time'] = task['total_time']
                    st.rerun()
            else:
                if st.button("⏹️", key=f"stop_{idx}", help="Stop Task"):
                    task['is_running'] = False
                    task['stop_time'] = datetime.now()                # Add only this session's time to the previous total
                    if task['start_time']:
                        # Calculate only the time for this session
                        current_session = (task['stop_time'] - task['start_time']).total_seconds()
                        task['total_time'] = task['previous_time'] + current_session
                    st.rerun()
        
        with button_col2:
            if not task['is_running']:
                if st.button("🗑️", key=f"delete_{idx}", help="Delete Task"):
                    try:
                        from sheets_integration import delete_from_sheets
                        success, message = delete_from_sheets([task['case_number']])
                        if success:
                            st.session_state.tasks.remove(task)
                            st.success(f"Task '{task['task_name']}' deleted!")
                            st.rerun()
                        else:
                            st.error(f"Failed to delete task: {message}")
                    except Exception as e:
                        st.error(f"Error deleting task: {str(e)}")

# Update running tasks
for task in st.session_state.tasks:
    if task['is_running']:
        current_time = datetime.now()
        if task['start_time']:            # Calculate only this session's time and add to previous total
            current_session = (current_time - task['start_time']).total_seconds()
            task['total_time'] = task['previous_time'] + current_session