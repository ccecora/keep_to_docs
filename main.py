import gkeepapi
from google.oauth2 import service_account
from googleapiclient.discovery import build

# =============================
# Step 1: Access Google Keep Notes
# =============================
def fetch_google_keep_notes(email, password):
    # Authenticate with Google Keep
    keep = gkeepapi.Keep()
    keep.login(email, password)
    
    # Fetch notes
    notes = keep.all()
    notes_data = [{"title": note.title, "content": note.text} for note in notes]
    return notes_data

# =============================
# Step 2: Write to Google Docs
# =============================
def write_to_google_doc(credentials_path, doc_title, notes_data):
    # Authenticate with Google Docs API
    SCOPES = ['https://www.googleapis.com/auth/documents']
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path, scopes=SCOPES)
    service = build('docs', 'v1', credentials=credentials)
    
    # Create a new Google Doc
    document = service.documents().create(body={'title': doc_title}).execute()
    document_id = document.get('documentId')
    print(f"Document created with ID: {document_id}")
    
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
    service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()
    print("Notes written to the Google Doc.")
    return document_id

# =============================
# Main Execution
# =============================
if __name__ == "__main__":
    # Google Keep credentials
    EMAIL = "your_email@gmail.com"
    PASSWORD = "your_app_password"  # Use App Password if 2FA is enabled
    
    # Google Docs credentials file
    CREDENTIALS_PATH = 'path/to/credentials.json'
    DOC_TITLE = "My Google Keep Notes"
    
    # Fetch notes from Google Keep
    keep_notes = fetch_google_keep_notes(EMAIL, PASSWORD)
    print(f"Fetched {len(keep_notes)} notes from Google Keep.")
    
    # Write the notes to a Google Doc
    document_id = write_to_google_doc(CREDENTIALS_PATH, DOC_TITLE, keep_notes)
    print(f"Google Doc created with ID: {document_id}")
