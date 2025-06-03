from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime
import streamlit as st
import json
import os.path
import pickle

# Use Streamlit secrets for configuration
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_google_sheets_credentials():
    creds = None
    
    # Check if we're running on Streamlit Cloud
    if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
        try:
            creds_dict = json.loads(st.secrets.gcp_service_account.GOOGLE_SHEETS_CREDENTIALS)
            
            # Use OAuth credentials directly in cloud environment
            if 'web' in creds_dict:
                client_config = {
                    'web': {
                        'client_id': creds_dict['web']['client_id'],
                        'client_secret': creds_dict['web']['client_secret'],
                        'auth_uri': creds_dict['web']['auth_uri'],
                        'token_uri': creds_dict['web']['token_uri'],
                        'redirect_uris': creds_dict['web']['redirect_uris']
                    }
                }
                
                # Initialize flow with client configuration
                flow = InstalledAppFlow.from_client_config(
                    client_config,
                    SCOPES,
                    redirect_uri=creds_dict['web']['redirect_uris'][0]
                )
                
                # Get the authorization URL
                auth_url, _ = flow.authorization_url(prompt='consent')
                
                # Show the authentication URL to the user
                st.markdown("""
                ### Google Sheets Authentication Required
                Please click the link below to authenticate with Google Sheets:
                """)
                st.markdown(f"[Click here to authenticate]({auth_url})")
                
                # Wait for the authentication code
                code = st.text_input("Enter the authentication code:", key="auth_code")
                if code:
                    try:
                        flow.fetch_token(code=code)
                        creds = flow.credentials
                        st.success("Authentication successful!")
                    except Exception as e:
                        st.error(f"Error fetching token: {str(e)}")
                        return None
        except Exception as e:
            st.error(f"Error loading credentials from secrets: {str(e)}")
            return None
    else:
        # Local development using files
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
    
    return creds

def get_spreadsheet_info():
    """Get spreadsheet ID and sheet name from config"""
    if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
        return (
            st.secrets.gcp_service_account.SPREADSHEET_ID,
            st.secrets.gcp_service_account.SHEET_NAME
        )
    else:
        # Default values for local development
        return (
            '19Ipiaq8dsg9JLSGqFtY9qRBPb-OaLhxDsuuBG12Wbas',
            'Mac'
        )

def sync_to_sheets(tasks):
    """
    Sync tasks to Google Sheets with recent start time and accumulated total time
    """
    try:
        creds = get_google_sheets_credentials()
        if not creds:
            return False, "Failed to get credentials"
            
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()
        
        SPREADSHEET_ID, SHEET_NAME = get_spreadsheet_info()

        # First, get existing data
        range_name = f'{SHEET_NAME}!A2:F'  # Including Recent Start column
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name
        ).execute()
        existing_rows = result.get('values', [])
        
        # Clean up tasks before syncing by removing duplicates
        # Keep only the latest entry for each case number
        unique_tasks = {}
        for task in tasks:
            case_number = task['case_number']
            if case_number in unique_tasks:
                # Compare timestamps to keep the most recent one
                existing_task = unique_tasks[case_number]
                if (task['start_time'] and not existing_task['start_time']) or \
                   (task['start_time'] and existing_task['start_time'] and 
                    task['start_time'] > existing_task['start_time']):
                    unique_tasks[case_number] = task
            else:
                unique_tasks[case_number] = task
        
        # Use the deduplicated tasks list
        tasks = list(unique_tasks.values())
        
        # Prepare new/updated data
        new_rows = []
        updated_rows = []
        
        # Create a mapping of case numbers to row index and existing data
        existing_case_numbers = {}
        for idx, row in enumerate(existing_rows):
            if row and len(row) >= 6:  # Make sure row has all columns
                case_number = row[0]
                row_num = idx + 2  # +2 because of header and 1-based index
                try:
                    total_time = float(row[5]) * 3600 if row[5] else 0  # Convert hours to seconds
                except ValueError:
                    total_time = 0
                
                existing_case_numbers[case_number] = {
                    'row_num': row_num,
                    'start_time': row[2],  # Original start time
                    'recent_start': row[3],  # Recent start time
                    'total_time': total_time
                }
        
        # Process each task
        for task in tasks:
            # Get timestamps
            current_time = task['stop_time'].strftime('%Y-%m-%d %H:%M:%S') if task['stop_time'] else ''
            recent_start = task['start_time'].strftime('%Y-%m-%d %H:%M:%S') if task['start_time'] else ''
            
            if task['case_number'] in existing_case_numbers:
                # Use the original start time from the sheet
                original_start_time = existing_case_numbers[task['case_number']]['start_time']
                if not original_start_time and task['start_time']:
                    original_start_time = recent_start
                
                # Always use the most recent start time
                if task['start_time']:
                    recent_start = task['start_time'].strftime('%Y-%m-%d %H:%M:%S')
                elif existing_case_numbers[task['case_number']]['recent_start']:
                    recent_start = existing_case_numbers[task['case_number']]['recent_start']
            else:
                original_start_time = recent_start

            row_data = [
                task['case_number'],
                task['task_name'],
                original_start_time,
                recent_start,
                current_time,
                f"{task['total_time'] / 3600:.2f}"
            ]
            
            task_id = task['case_number'].strip()
            if task_id in existing_case_numbers:
                row_num = existing_case_numbers[task_id]['row_num']
                updated_rows.append({
                    'range': f'{SHEET_NAME}!A{row_num}:F{row_num}',
                    'values': [row_data]
                })
            else:
                new_rows.append(row_data)

        # Perform updates first
        if updated_rows:
            body = {
                'valueInputOption': 'USER_ENTERED',
                'data': updated_rows
            }
            sheet.values().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body=body
            ).execute()

        # Then append new rows
        if new_rows:
            body = {
                'values': new_rows
            }
            sheet.values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=f'{SHEET_NAME}!A2:F2',
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()

        return True, "Synchronization successful!"
    except Exception as e:
        return False, f"Error during synchronization: {str(e)}"

def load_from_sheets():
    """
    Load tasks from Google Sheets
    """
    try:
        creds = get_google_sheets_credentials()
        if not creds:
            return False, "Failed to get credentials"
            
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()
        
        SPREADSHEET_ID, SHEET_NAME = get_spreadsheet_info()

        range_name = f'{SHEET_NAME}!A2:F'  # Including Recent Start column
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name
        ).execute()
        rows = result.get('values', [])

        tasks = []
        for row in rows:
            if len(row) >= 6:  # Make sure row has all required columns
                start_time = None
                recent_start = None
                stop_time = None
                total_time = 0

                # Parse original start time
                if row[2]:  # If start time exists
                    try:
                        start_time = datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        pass

                # Parse recent start time
                if row[3]:  # If recent start exists
                    try:
                        recent_start = datetime.strptime(row[3], '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        pass
                
                # Parse stop time
                if row[4]:  # If stop time exists
                    try:
                        stop_time = datetime.strptime(row[4], '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        pass

                # Parse total time
                if row[5]:  # If total time exists
                    try:
                        total_time = float(row[5]) * 3600  # Convert hours to seconds
                    except ValueError:
                        pass

                task = {
                    "case_number": row[0],
                    "task_name": row[1],
                    "start_time": start_time,  # This will be the original start time
                    "stop_time": stop_time,
                    "total_time": total_time,
                    "is_running": False,
                    "previous_time": total_time  # Initialize previous_time with total_time
                }
                tasks.append(task)

        return True, tasks
    except Exception as e:
        return False, f"Error loading from sheets: {str(e)}"

def delete_from_sheets(case_numbers):
    """
    Delete tasks from Google Sheets by case number
    """
    try:
        creds = get_google_sheets_credentials()
        if not creds:
            return False, "Failed to get credentials"
            
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()
        
        SPREADSHEET_ID, SHEET_NAME = get_spreadsheet_info()

        # First, get existing data
        range_name = f'{SHEET_NAME}!A2:F'
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name
        ).execute()
        existing_rows = result.get('values', [])

        # Find rows to delete
        rows_to_clear = []
        for idx, row in enumerate(existing_rows):
            if row and row[0] in case_numbers:
                row_num = idx + 2  # +2 because of header and 1-based index
                rows_to_clear.append(f'{SHEET_NAME}!A{row_num}:F{row_num}')

        # Clear the rows
        if rows_to_clear:
            requests = [{
                'updateCells': {
                    'range': {
                        'sheetId': 0,  # Assuming it's the first sheet
                        'startRowIndex': row_num - 1,
                        'endRowIndex': row_num,
                        'startColumnIndex': 0,
                        'endColumnIndex': 6
                    },
                    'fields': '*'
                }
            } for row_num in [int(r.split('!')[1].split(':')[0][1:]) for r in rows_to_clear]]

            batch_update_request = {
                'requests': requests
            }

            sheet.batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body=batch_update_request
            ).execute()

        return True, "Deletion successful!"
    except Exception as e:
        return False, f"Error during deletion: {str(e)}"
