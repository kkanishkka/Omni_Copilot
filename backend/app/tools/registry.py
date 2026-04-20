"""
Tool registry — Groq-compatible function declarations.
Key design decisions:
- delete_calendar_event is registered so the LLM can delete by event_id (found via list first)
- send_email_with_drive_link is registered to attach Drive files properly
- All descriptions are precise to prevent wrong tool selection (e.g. no auto-email on Meet creation)
"""

TOOL_DECLARATIONS = [
    # ── Calendar ──────────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_calendar_events",
            "description": (
                "List upcoming events from Google Calendar. "
                "Use this to find event IDs before deleting or modifying events."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Number of events to return (default 10, max 20)"
                    },
                    "time_min": {
                        "type": "string",
                        "description": "ISO8601 datetime for earliest event. Default = now."
                    },
                    "time_max": {
                        "type": "string",
                        "description": "ISO8601 datetime for latest event. Use to scope to today only."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_calendar_event",
            "description": (
                "Create a new event on Google Calendar, optionally with a Google Meet link. "
                "ONLY creates the event — does NOT send email unless attendees are specified. "
                "If the user just wants a Meet link, set add_meet=true and summary to something short. "
                "Do NOT call send_email after this unless the user explicitly asked to send an email."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Event title"},
                    "start_time": {"type": "string", "description": "ISO8601 start datetime (e.g. 2026-04-19T19:00:00)"},
                    "end_time": {"type": "string", "description": "ISO8601 end datetime"},
                    "description": {"type": "string", "description": "Event description"},
                    "location": {"type": "string", "description": "Event location"},
                    "add_meet": {
                        "type": "boolean",
                        "description": "Set true to generate a Google Meet link. Required when user asks for a Meet link."
                    },
                    "attendees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Email addresses of attendees. Providing attendees sends Google Calendar invites automatically — do NOT also call send_email unless user explicitly asked for a separate email."
                    }
                },
                "required": ["summary", "start_time", "end_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_calendar_event",
            "description": (
                "Delete a specific event from Google Calendar by its event ID. "
                "You MUST call list_calendar_events first to find the correct event_id. "
                "For 'delete all events today', list events for today then call this for each one."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "The Google Calendar event ID to delete (from list_calendar_events results)"
                    }
                },
                "required": ["event_id"]
            }
        }
    },

    # ── Drive ─────────────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "search_drive_files",
            "description": "Search for files in Google Drive by name. Returns file IDs and shareable links.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "File name search term"},
                    "max_results": {"type": "integer", "description": "Max files to return (default 5)"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_drive_file_content",
            "description": "Extract text content from a Google Drive file. For binary/PDF files, returns a note that it cannot be displayed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_id": {"type": "string", "description": "Google Drive file ID"},
                    "file_name": {"type": "string", "description": "Optional filename hint"}
                },
                "required": ["file_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_google_doc",
            "description": "Create a new Google Doc with specified title and content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Document title"},
                    "content": {"type": "string", "description": "Text content"}
                },
                "required": ["title", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "share_file",
            "description": "Share a Google Drive file with another user and send them a notification email with the link.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_id": {"type": "string", "description": "ID of the file to share"},
                    "email": {"type": "string", "description": "Recipient email address"},
                    "role": {
                        "type": "string",
                        "enum": ["reader", "commenter", "writer"],
                        "description": "Access level (default 'reader')"
                    }
                },
                "required": ["file_id", "email"]
            }
        }
    },

    # ── Gmail ─────────────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_emails",
            "description": "List and summarize emails from Gmail. Works for any count 1–20.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Number of emails to retrieve (1–20, default 5)"
                    },
                    "query": {
                        "type": "string",
                        "description": "Gmail search filter. Examples: 'is:unread', 'from:boss@co.com', 'subject:invoice'"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_email_content",
            "description": "Get the full body of a specific email by its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message_id": {"type": "string", "description": "Gmail message ID"}
                },
                "required": ["message_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": (
                "Send a plain-text email via Gmail. "
                "ONLY use this when the user EXPLICITLY asks to send an email. "
                "Do NOT use this just because a calendar event was created. "
                "Do NOT use 'user@example.com' or placeholder addresses — only real email addresses from the user's request. "
                "If recipient email is unknown, ask the user before calling this tool."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient email address — must be a real email from the user's message, never a placeholder"
                    },
                    "subject": {"type": "string", "description": "Email subject line"},
                    "body": {"type": "string", "description": "Email body text"}
                },
                "required": ["to", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email_with_drive_link",
            "description": (
                "Send an email that includes a Google Drive file's shareable link. "
                "Use this instead of send_email when the user asks to 'send a file via email' or 'email a Drive file'. "
                "This fetches the shareable link and embeds it properly in the email body."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body text (the drive link will be appended)"},
                    "file_id": {"type": "string", "description": "Google Drive file ID to include the link for"},
                    "file_name": {"type": "string", "description": "Display name of the file"}
                },
                "required": ["to", "subject", "body", "file_id", "file_name"]
            }
        }
    },

    # ── Notion ────────────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "search_notion_pages",
            "description": (
                "Search for pages accessible to the Notion integration. "
                "ALWAYS call this before create_notion_page to find a valid parent_page_id. "
                "Use query='' (empty string) to list ALL accessible pages."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term. Pass empty string '' to list all accessible pages."
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Max pages to return (default 10)"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_notion_page",
            "description": "Get the content of a Notion page by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id": {"type": "string", "description": "Notion page ID"}
                },
                "required": ["page_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_notion_page",
            "description": (
                "Create a new Notion page under a parent page. "
                "parent_page_id MUST be a real ID from search_notion_pages results. "
                "NEVER use placeholders like 'None', 'Not available', or 'search_result_id'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "parent_page_id": {
                        "type": "string",
                        "description": "Real Notion page ID from search_notion_pages (e.g. '1a2b3c4d-...'). Never a placeholder."
                    },
                    "title": {"type": "string", "description": "Page title"},
                    "content": {"type": "string", "description": "Page content (supports markdown headings and bullets)"}
                },
                "required": ["parent_page_id", "title", "content"]
            }
        }
    }
]
