# Task Tracker with Google Sheets Integration

A Streamlit-based task tracking application that helps you monitor time spent on different tasks and synchronizes data with Google Sheets.

## Features

- Create and manage tasks with case numbers
- Track time spent on tasks with start/stop functionality
- Real-time task timing with accurate session tracking
- Synchronization with Google Sheets
- Persistent storage of task data
- Delete individual tasks or all tasks at once
- Maintains accurate time calculations across sessions

## Time Tracking Details

- **Original Start Time**: When a task is first created
- **Recent Start Time**: Updated each time a task is started
- **Stop Time**: When a task is stopped
- **Total Time**: Accumulates time across all sessions

## Setup

1. Install the required packages:
```bash
pip install -r requirements.txt
```

2. Set up Google Sheets API:
   - Create a project in Google Cloud Console
   - Enable Google Sheets API
   - Create credentials (OAuth 2.0 Client ID)
   - Download the credentials and save as `credentials.json` in the project root

3. First run will require Google authorization:
   - Run the application
   - Follow the OAuth flow in your browser
   - Grant necessary permissions
   - The app will save the token for future use

## Usage

1. Start the application:
```bash
streamlit run main.py
```

2. Create a new task:
   - Enter task name and case number
   - Click "Add Task"

3. Task Operations:
   - ▶️ Start a task
   - ⏹️ Stop a task
   - 🗑️ Delete a task
   - "Delete All Tasks" to clear everything
   - "Synch to GS" to synchronize with Google Sheets

4. Google Sheets Integration:
   - Tasks are automatically loaded from Google Sheets on startup
   - Click "Synch to GS" to manually sync changes
   - View detailed task history in Google Sheets

## File Structure

- `main.py`: Main application code with Streamlit UI
- `sheets_integration.py`: Google Sheets integration functionality
- `requirements.txt`: Python package dependencies
- `credentials.json`: Google Sheets API credentials
- `token.pickle`: Stored OAuth tokens

## Important Notes

- Only one task can be running at a time
- Total time is preserved across sessions
- Duplicates are automatically handled during sync
- Manual edits in Google Sheets are preserved
- Recent start time updates with each new session

## Dependencies

- streamlit
- google-auth-oauthlib
- google-auth
- google-api-python-client
- pandas
