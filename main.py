from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import json
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# =============================
# Step 1: Read Google Keep Notes from Takeout
# =============================
def read_keep_notes_from_takeout(takeout_dir):
    """Read Keep notes from Google Takeout export directory."""
    logger.info(f"Reading Keep notes from: {takeout_dir}")
    
    notes_data = []
    takeout_path = Path(takeout_dir)
    
    try:
        # Walk through all JSON files in the Takeout directory
        for json_file in takeout_path.glob("*.json"):
            logger.debug(f"Reading file: {json_file}")
            
            with open(json_file, 'r', encoding='utf-8') as f:
                note = json.load(f)
                
                # Extract title and content
                title = note.get('title', 'Untitled')
                content = note.get('textContent', '')
                
                # Skip empty notes
                if not title and not content:
                    continue
                
                notes_data.append({
                    "title": title,
                    "content": content
                })
        
        logger.info(f"Successfully read {len(notes_data)} notes")
        return notes_data
    
    except Exception as e:
        logger.error(f"Error reading notes: {str(e)}")
        raise

# =============================
# Step 2: Write to Google Docs
# =============================
def write_to_google_doc(credentials_path, doc_title, notes_data):
    """Write notes to a Google Doc."""
    logger.info(f"Creating Google Doc: {doc_title}")
    
    # Authenticate with Google Docs API
    SCOPES = [
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/drive.file'  # Added scope for sharing
    ]
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path, scopes=SCOPES)
    
    # Create services for both Docs and Drive
    docs_service = build('docs', 'v1', credentials=credentials)
    drive_service = build('drive', 'v3', credentials=credentials)
    
    # Create a new Google Doc
    document = docs_service.documents().create(body={'title': doc_title}).execute()
    document_id = document.get('documentId')
    logger.info(f"Created document with ID: {document_id}")
    
    # Share the document with your personal account
    user_email = os.getenv('GOOGLE_KEEP_EMAIL')
    if not user_email:
        raise ValueError("GOOGLE_KEEP_EMAIL environment variable is not set")
    logger.info(f"Attempting to share document with: {user_email}")
    
    # First, share the document with editor role
    permission = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': user_email.strip()
    }
    logger.info(f"Creating permission: {permission}")
    
    drive_service.permissions().create(
        fileId=document_id,
        body=permission,
        fields='id',
        sendNotificationEmail=False
    ).execute()
    logger.info(f"Successfully shared document with {user_email}")
    
    # Prepare the content to write to the document
    requests = []
    for note in notes_data:
        title = note['title']
        content = note['content']
        requests.append({
            'insertText': {
                'location': {'index': 1},
                'text': f"Title: {title}\nContent: {content}\n\n"
            }
        })
    
    # Write the notes to the document
    docs_service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()
    logger.info("Notes written to the Google Doc")
    return document_id

# =============================
# Main Execution
# =============================
if __name__ == "__main__":
    # Get configuration from environment variables
    TAKEOUT_DIR = os.getenv('KEEP_TAKEOUT_DIR')
    CREDENTIALS_PATH = os.getenv('GOOGLE_DOCS_CREDENTIALS_PATH')
    DOC_TITLE = os.getenv('GOOGLE_DOCS_TITLE')
    
    # Validate environment variables
    if not all([TAKEOUT_DIR, CREDENTIALS_PATH, DOC_TITLE]):
        raise ValueError("Missing required environment variables. Please check your .env file.")
    
    # Read notes from Takeout export
    keep_notes = read_keep_notes_from_takeout(TAKEOUT_DIR)
    print(f"Read {len(keep_notes)} notes from Takeout export.")
    
    # Write the notes to a Google Doc
    document_id = write_to_google_doc(CREDENTIALS_PATH, DOC_TITLE, keep_notes)
    print(f"Google Doc created with ID: {document_id}")
