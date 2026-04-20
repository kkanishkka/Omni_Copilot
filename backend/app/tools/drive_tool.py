from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from app.integrations.google_auth import build_credentials
from app.utils.file_parser import parse_file
import io


def get_drive_service(token_data: dict):
    creds = build_credentials(token_data)
    return build("drive", "v3", credentials=creds)


def search_files(token_data: dict, query: str, max_results: int = 10) -> dict:
    service = get_drive_service(token_data)
    q = f"name contains '{query}' and trashed=false"
    results = service.files().list(
        q=q,
        pageSize=max_results,
        fields="files(id, name, mimeType, modifiedTime, size, webViewLink)",
    ).execute()
    return {"files": results.get("files", [])}


def list_files(token_data: dict, max_results: int = 20) -> dict:
    service = get_drive_service(token_data)
    results = service.files().list(
        pageSize=max_results,
        orderBy="modifiedTime desc",
        fields="files(id, name, mimeType, modifiedTime, size, webViewLink)",
    ).execute()
    return {"files": results.get("files", [])}


def get_file_content(token_data: dict, file_id: str, file_name: str = "") -> dict:
    service = get_drive_service(token_data)
    file_meta = service.files().get(fileId=file_id, fields="name,mimeType").execute()
    name = file_name or file_meta.get("name", "file")
    mime = file_meta.get("mimeType", "")

    buffer = io.BytesIO()

    # Google Docs → export as docx
    if "google-apps.document" in mime:
        request = service.files().export_media(
            fileId=file_id,
            mimeType="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        name = name + ".docx"
    elif "google-apps.spreadsheet" in mime:
        request = service.files().export_media(
            fileId=file_id,
            mimeType="text/csv",
        )
        name = name + ".csv"
    else:
        request = service.files().get_media(fileId=file_id)

    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()

    content = buffer.getvalue()
    text = parse_file(content, name)

    return {
        "file_id": file_id,
        "file_name": name,
        "content": text or "[Binary file - cannot display text content]",
        "mime_type": mime,
    }


def create_google_doc(token_data: dict, title: str, content: str) -> dict:
    """Create a new Google Doc with the given content."""
    service = get_drive_service(token_data)
    file_metadata = {
        "name": title,
        "mimeType": "application/vnd.google-apps.document"
    }
    # Create the doc
    doc = service.files().create(body=file_metadata, fields="id, webViewLink").execute()
    file_id = doc.get("id")

    # Update the doc content using Google Docs API (building a separate service for it)
    from googleapiclient.discovery import build
    creds = build_credentials(token_data)
    docs_service = build("docs", "v1", credentials=creds)

    requests = [
        {
            "insertText": {
                "location": {"index": 1},
                "text": content
            }
        }
    ]
    docs_service.documents().batchUpdate(documentId=file_id, body={"requests": requests}).execute()

    return {
        "file_id": file_id,
        "title": title,
        "webViewLink": doc.get("webViewLink")
    }


def share_file(token_data: dict, file_id: str, email: str, role: str = "reader") -> dict:
    """Share a file with a specific email address."""
    service = get_drive_service(token_data)
    user_permission = {
        "type": "user",
        "role": role,
        "emailAddress": email
    }
    result = service.permissions().create(
        fileId=file_id,
        body=user_permission,
        fields="id",
        sendNotificationEmail=True
    ).execute()

    return {"success": True, "permission_id": result.get("id"), "shared_with": email}
