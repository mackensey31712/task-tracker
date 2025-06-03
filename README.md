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

2. Set up Google Cloud Project and Google Sheets API:
   a. Go to Google Cloud Console (https://console.cloud.google.com)
   b. Create a new project or select existing project
   c. Enable Google Sheets API
   d. Create a Service Account:
      - Go to "IAM & Admin" > "Service Accounts"
      - Click "Create Service Account"
      - Name it (e.g., "tasktracker-service")
      - Grant "Editor" role
      - Create and download the JSON key file
      - Save the key file in your project directory (it will be ignored by git)
   e. Share your Google Sheet with the service account email

3. Configure the application:
   a. Create `.streamlit` directory and `secrets.toml` file:
   ```powershell
   New-Item -ItemType Directory -Path .streamlit
   ```
   
   b. Add your credentials to `.streamlit/secrets.toml`:
   ```toml
   [gcp_service_account]
   GOOGLE_SHEETS_CREDENTIALS = '''
   # Paste your service account JSON content here
   '''
   SPREADSHEET_ID = "your-spreadsheet-id"
   SHEET_NAME = "Mac"
   ```

4. Setup version control:
   - Initialize git repository
   - Use `.gitignore` to exclude sensitive files:
     - credentials.json
     - token.pickle
     - .streamlit/secrets.toml
     - service account JSON files
     - Python cache and virtual environment files

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

## Deployment

1. Create a GitHub repository for your project

2. Deploy to Streamlit Cloud:
   - Sign up at https://share.streamlit.io
   - Connect your GitHub repository
   - Configure secrets in Streamlit Cloud dashboard
   - Deploy the application

3. Post-deployment:
   - Test all functionality
   - Verify Google Sheets integration
   - Monitor the application in Streamlit Cloud dashboard

For detailed deployment instructions, see `DeployingInStreamlit.txt`.

## File Structure

- `main.py`: Main application code with Streamlit UI
- `sheets_integration.py`: Google Sheets integration using Service Account authentication
- `requirements.txt`: Python package dependencies
- `.streamlit/secrets.toml`: Configuration and credentials (not in repo)
- `DeployingInStreamlit.txt`: Detailed deployment guide

## Important Notes

- Only one task can be running at a time
- Total time is preserved across sessions
- Duplicates are automatically handled during sync
- Manual edits in Google Sheets are preserved
- Recent start time updates with each new session

## Security Notes

1. Credential Protection:
   - Never commit credential files to Git
   - Use `.gitignore` to exclude sensitive files
   - Store credentials securely using Streamlit secrets
   - Rotate service account keys periodically

2. Authentication:
   - Uses Service Account authentication
   - No OAuth2 user authentication required
   - Share Google Sheet with service account email

## Dependencies

- streamlit
- google-auth
- google-api-python-client
- pandas
