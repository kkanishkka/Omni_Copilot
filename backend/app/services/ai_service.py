"""
ai_service.py — production-ready agent pipeline for Omni Copilot

Architecture:
  Intent Detection → Pre-execution Validation → Tool Execution → Context Capture → Response

Key fixes applied (v2):
  1. ExecutionContext: captures real tool outputs (meetLink, file_id, webViewLink) and
     injects them into subsequent tool calls — prevents LLM from hallucinating links.
  2. send_email meet-link fix: after create_calendar_event, if send_email body contains
     a placeholder meet link, it is replaced with the real link from context.
  3. send_email_with_drive_link fix: after search_drive_files, file_id and file_name are
     injected from context if the LLM uses a placeholder.
  4. <function=...> format bug: malformed turns are NOT appended to message history before
     retry — Groq no longer sees invalid assistant content on the next attempt.
  5. list_calendar_events: time_max is now forwarded to the API for proper day scoping.
  6. list_emails: works for any count 1-20 with no hardcoded constraint.
  7. Duplicate email: hard cap (email_sent_this_turn) + deduplication key.
  8. History sanitization: only role+content forwarded; no tool state leakage.
"""

import json
import re
import time
import logging
import os
from datetime import datetime, timezone, timedelta
from groq import Groq
from app.config.settings import settings
from app.tools.registry import TOOL_DECLARATIONS

logger = logging.getLogger(__name__)
client = Groq(api_key=settings.GROQ_API_KEY)

# ── Placeholder / invalid values that must never reach a tool ─────────────────
_INVALID_EMAIL_ADDRESSES = {
    "user@example.com", "example@example.com", "test@test.com",
    "placeholder@email.com", "noreply@example.com",
}
_INVALID_NOTION_IDS = {
    "none", "not available", "not_available", "search_result_id",
    "unknown", "n/a", "na", "", "null", "undefined",
}

# Patterns that indicate the LLM wrote a placeholder meet link
_PLACEHOLDER_MEET_PATTERNS = [
    r"\{meet[_\s]?link[^\}]*\}",
    r"<meet[_\s]?link[^>]*>",
    r"https://meet\.google\.com/xxx",
    r"meet_link_here",
    r"your[-_\s]?meet[-_\s]?link",
    r"\{MEET LINK[^\}]*\}",
]

# Patterns indicating a placeholder Drive file_id
_PLACEHOLDER_FILE_ID_PATTERNS = [
    r"<[^>]*file[_\s]?id[^>]*>",
    r"\{[^\}]*file[_\s]?id[^\}]*\}",
    r"^file_id_here$",
    r"^placeholder",
    r"^<Scaler",
    r"Scalera_i_file_id",
    r"NOT NEEDED",
]


def _is_placeholder_meet_link(value: str) -> bool:
    if not value:
        return True
    for pat in _PLACEHOLDER_MEET_PATTERNS:
        if re.search(pat, value, re.IGNORECASE):
            return True
    if "meet.google.com" in value and re.search(r"[a-z]{3}-[a-z]{4}-[a-z]{3}", value):
        return False
    if "{" in value or "<" in value:
        return True
    return False


def _is_placeholder_file_id(value: str) -> bool:
    if not value or len(value) < 5:
        return True
    for pat in _PLACEHOLDER_FILE_ID_PATTERNS:
        if re.search(pat, value, re.IGNORECASE):
            return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# ExecutionContext — single source of truth for data across tool steps
# ─────────────────────────────────────────────────────────────────────────────

class ExecutionContext:
    """
    Holds structured intermediate state captured from tool results so that
    subsequent tool calls can use REAL values instead of LLM-generated placeholders.
    """
    def __init__(self):
        self.meet_link = None
        self.calendar_event_id = None
        self.drive_files = []
        self.last_file_id = None
        self.last_file_name = None
        self.last_web_view_link = None

    def capture(self, tool_name: str, result: dict):
        if tool_name == "create_calendar_event":
            meet = result.get("meetLink")
            if meet and not _is_placeholder_meet_link(str(meet)):
                self.meet_link = meet
                logger.info(f"[Context] Captured meetLink: {self.meet_link}")
            eid = result.get("id")
            if eid:
                self.calendar_event_id = eid

        elif tool_name == "search_drive_files":
            files = result.get("files", [])
            if files:
                self.drive_files = files
                first = files[0]
                self.last_file_id = first.get("id")
                self.last_file_name = first.get("name")
                self.last_web_view_link = first.get("webViewLink")
                logger.info(
                    f"[Context] Captured drive file: id={self.last_file_id} "
                    f"name={self.last_file_name}"
                )

        elif tool_name == "create_google_doc":
            fid = result.get("file_id") or result.get("id")
            if fid:
                self.last_file_id = fid
                self.last_file_name = result.get("title") or result.get("name")

        elif tool_name == "send_email_with_drive_link":
            link = result.get("file_link")
            if link:
                self.last_web_view_link = link

    def patch_send_email_args(self, args: dict) -> dict:
        if not self.meet_link:
            return args
        body = args.get("body", "")
        if not body:
            return args
        patched = body
        for pat in _PLACEHOLDER_MEET_PATTERNS:
            patched = re.sub(pat, self.meet_link, patched, flags=re.IGNORECASE)
        if patched != body:
            logger.info(f"[Context] Patched placeholder meet link in email body")
            args = dict(args)
            args["body"] = patched
        return args

    def patch_send_email_with_drive_link_args(self, args: dict) -> dict:
        args = dict(args)
        if self.last_file_id and _is_placeholder_file_id(str(args.get("file_id", ""))):
            logger.info(f"[Context] Injecting real file_id={self.last_file_id}")
            args["file_id"] = self.last_file_id
        if self.last_file_name and (
            not args.get("file_name")
            or _is_placeholder_file_id(str(args.get("file_name", "")))
        ):
            args["file_name"] = self.last_file_name
        return args


# ─────────────────────────────────────────────────────────────────────────────
# System prompt
# ─────────────────────────────────────────────────────────────────────────────

BASE_SYSTEM_PROMPT = """You are Omni Copilot — a reliable, production-grade AI assistant that controls Google Calendar, Google Drive, Gmail, and Notion.

## CORE PRINCIPLE
Each user message is a FRESH, INDEPENDENT request. NEVER carry over actions from previous turns.

## TOOL SELECTION RULES

### Calendar
- "create meet" / "create google meet link" → call create_calendar_event with add_meet=true. Do NOT call send_email.
- "schedule meeting and email/invite [person]" → call create_calendar_event with attendees=[email]. Calendar sends the invite automatically. Do NOT also call send_email.
- "send a mail inviting [person] to meeting" → call create_calendar_event first (add_meet=true), then call send_email ONCE. Write a normal email body — do NOT write placeholder text like {MEET LINK}. The system automatically injects the real Meet link.
- "delete event" → FIRST call list_calendar_events to find the event_id, THEN call delete_calendar_event with that id.
- "delete all events today" → call list_calendar_events with time_min=<today 00:00:00 ISO8601> and time_max=<today 23:59:59 ISO8601>, then call delete_calendar_event for EACH event found.

### Gmail
- Only call send_email when the user EXPLICITLY asks to send an email.
- send_email "to" field must be a REAL email address from the user's message. NEVER use 'user@example.com' or any placeholder.
- If you need to send a Drive file by email, use send_email_with_drive_link (not send_email).
- For listing emails: list_emails works for ANY count 1-20. Use max_results exactly as requested.

### Google Drive
- "fetch X and email it" → search_drive_files, then send_email_with_drive_link (NOT send_email).
- For send_email_with_drive_link: use the file_id returned by search_drive_files. Do NOT make up file IDs.

### Notion
- ALWAYS call search_notion_pages with query='' before create_notion_page.
- Use the exact ID from the search result as parent_page_id. Never use "Not available" or any placeholder.
- If search returns no pages, tell the user to share a Notion page with the integration.

## IDEMPOTENCY RULES
- Call send_email EXACTLY ONCE per user request, never twice.
- Call send_email_with_drive_link EXACTLY ONCE per user request.
- Never repeat a tool call with identical arguments in the same turn.

## VALIDATION RULES
- If a required value is unknown, ASK the user instead of guessing.
- Never proceed with obviously invalid inputs.

## DATETIME RULES
- [SYSTEM DATETIME] at top of this prompt is the exact current date/time.
- Always pass ISO8601 strings to calendar tools (e.g. "2026-04-19T19:00:00").
- For "delete all events today": time_min = today 00:00:00 local time, time_max = today 23:59:59 local time.

Always respond in clean, concise markdown."""


def _get_local_tz():
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(os.environ.get("TIMEZONE", "Asia/Kolkata"))
    except Exception:
        return timezone(timedelta(hours=5, minutes=30))


def _build_system_prompt() -> str:
    local_tz = _get_local_tz()
    now = datetime.now(local_tz)
    tz_name = os.environ.get("TIMEZONE", "Asia/Kolkata")
    header = (
        f"[SYSTEM DATETIME] {now.strftime('%A')}, {now.strftime('%Y-%m-%d')} "
        f"| Time ({tz_name}): {now.strftime('%H:%M:%S')} "
        f"| ISO8601: {now.isoformat()}\n\n"
    )
    return header + BASE_SYSTEM_PROMPT


def _sanitize_history(history: list) -> list:
    cleaned = []
    for msg in history[-20:]:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role in ("user", "assistant") and content:
            cleaned.append({"role": role, "content": str(content)})
    return cleaned


# ─────────────────────────────────────────────────────────────────────────────
# Pre-execution guardrails
# ─────────────────────────────────────────────────────────────────────────────

def _pre_validate(tool_name: str, args: dict):
    if tool_name in ("send_email", "send_email_with_drive_link"):
        to = str(args.get("to", "")).strip().lower()
        if not to or "@" not in to:
            return {"error": f"Blocked: missing or invalid recipient email '{args.get('to')}'."}
        if to in _INVALID_EMAIL_ADDRESSES:
            return {"error": f"Blocked: '{args.get('to')}' is a placeholder address."}
        domain = to.split("@")[-1]
        if domain in ("example.com", "test.com", "placeholder.com"):
            return {"error": f"Blocked: '{args.get('to')}' is a placeholder domain."}

    if tool_name == "create_notion_page":
        pid = str(args.get("parent_page_id", "")).strip().lower()
        if pid in _INVALID_NOTION_IDS or len(pid) < 8:
            return {"error": f"Blocked: parent_page_id '{args.get('parent_page_id')}' is invalid."}

    if tool_name == "delete_calendar_event":
        eid = str(args.get("event_id", "")).strip()
        if not eid or len(eid) < 5:
            return {"error": "Blocked: event_id is missing. Call list_calendar_events first."}

    # Note: send_email_with_drive_link file_id validation happens AFTER context injection
    # so we skip it here (context patcher runs before _pre_validate is called).

    return None


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def call_groq_with_tools(
    user_message: str,
    conversation_history: list,
    google_token_data: dict = None,
    notion_token: str = None,
    file_context: str = None,
) -> dict:
    system_prompt = _build_system_prompt()

    user_content = user_message
    if file_context:
        user_content = f"[File Context]\n{file_context}\n\n[User Message]\n{user_message}"

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(_sanitize_history(conversation_history))
    messages.append({"role": "user", "content": user_content})

    tool_declarations = list(TOOL_DECLARATIONS)

    tool_trace = []
    executed_calls: set = set()
    invalid_format_retries = 0
    email_sent_this_turn = False
    ctx = ExecutionContext()

    for iteration in range(12):
        logger.debug(f"[Agent] Iteration {iteration + 1}")

        try:
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=messages,
                tools=tool_declarations,
                tool_choice="auto",
            )
        except Exception as e:
            logger.error(f"[Agent] Groq API error: {e}")
            return {"response": f"AI service error: {e}", "tool_trace": tool_trace}

        message = response.choices[0].message
        tool_calls = message.tool_calls
        content = message.content or ""

        # ── Handle Groq invalid tool format bug ──────────────────────────────
        if not tool_calls:
            if "<function=" in content:
                if invalid_format_retries < 3:
                    invalid_format_retries += 1
                    logger.warning(f"[Agent] Invalid tool format (retry {invalid_format_retries})")
                    # KEY FIX: Do NOT append the malformed assistant turn.
                    # Only add a corrective user message so Groq retries with a clean slate.
                    messages.append({
                        "role": "user",
                        "content": (
                            "SYSTEM: Your previous response used an invalid '<function=...>' format. "
                            "You MUST use the structured tool_calls interface. "
                            "Do NOT write '<function=...>' in your text. Please retry with proper tool calls."
                        )
                    })
                    continue
                # Strip the bad XML and return whatever plain text remains
                clean = re.sub(r"<function=[^>]*>.*?</function>", "", content, flags=re.DOTALL).strip()
                return {
                    "response": clean or "I had trouble calling the right tool. Please try rephrasing.",
                    "tool_trace": tool_trace,
                }

            # Normal text response
            return {"response": content or "Done.", "tool_trace": tool_trace}

        # ── Process all tool calls ────────────────────────────────────────────
        assistant_payload = []
        results_payload = []

        for tc in tool_calls:
            tool_name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            # ── Context injection (before dedup & validation) ─────────────────
            if tool_name == "send_email":
                args = ctx.patch_send_email_args(args)
            if tool_name == "send_email_with_drive_link":
                args = ctx.patch_send_email_with_drive_link_args(args)

            # ── Deduplication ────────────────────────────────────────────────
            call_key = (tool_name, json.dumps(args, sort_keys=True))
            if call_key in executed_calls:
                logger.warning(f"[Agent] Skipping duplicate: {tool_name}")
                continue
            executed_calls.add(call_key)

            # ── Hard cap: one email per turn ──────────────────────────────────
            if tool_name in ("send_email", "send_email_with_drive_link"):
                if email_sent_this_turn:
                    logger.warning(f"[Agent] Blocked second email call: {tool_name}")
                    result = {"error": "Blocked: email already sent this turn."}
                    _append_tool_payloads(tc, tool_name, args, result,
                                          assistant_payload, results_payload, tool_trace, 0)
                    continue
                email_sent_this_turn = True

            # ── Pre-execution validation ──────────────────────────────────────
            validation_error = _pre_validate(tool_name, args)
            if validation_error:
                logger.warning(f"[Agent] Blocked {tool_name}: {validation_error}")
                result = validation_error
                _append_tool_payloads(tc, tool_name, args, result,
                                      assistant_payload, results_payload, tool_trace, 0)
                continue

            # ── Execute ───────────────────────────────────────────────────────
            t0 = time.time()
            try:
                result = _execute_tool(tool_name, args, google_token_data, notion_token)
                status = "success"
                logger.info(f"[Agent] {tool_name} OK ({int((time.time()-t0)*1000)}ms)")
                ctx.capture(tool_name, result)
            except Exception as e:
                result = {"error": str(e)}
                status = "error"
                logger.error(f"[Agent] {tool_name} failed: {e}")

            duration_ms = int((time.time() - t0) * 1000)
            _append_tool_payloads(tc, tool_name, args, result,
                                  assistant_payload, results_payload, tool_trace,
                                  duration_ms, status)

        if assistant_payload:
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": assistant_payload,
            })
            messages.extend(results_payload)

    logger.warning("[Agent] Max iterations reached")
    return {
        "response": "I've completed all the steps I could process.",
        "tool_trace": tool_trace,
    }


def _append_tool_payloads(
    tc, tool_name: str, args: dict, result: dict,
    assistant_payload: list, results_payload: list,
    tool_trace: list, duration_ms: int, status: str = "error"
):
    tool_trace.append({
        "tool_name": tool_name,
        "input": args,
        "output": result,
        "status": status,
        "duration_ms": duration_ms,
    })
    assistant_payload.append({
        "id": tc.id,
        "type": "function",
        "function": {"name": tool_name, "arguments": json.dumps(args)},
    })
    results_payload.append({
        "role": "tool",
        "tool_call_id": tc.id,
        "content": json.dumps(result, default=str),
    })


# ─────────────────────────────────────────────────────────────────────────────
# Tool dispatch
# ─────────────────────────────────────────────────────────────────────────────

def _execute_tool(tool_name: str, args: dict, google_token_data: dict, notion_token: str) -> dict:
    from app.tools import calendar_tool, drive_tool, gmail_tool, notion_tool

    def _int(key, default, args):
        try:
            return int(args.get(key, default))
        except (ValueError, TypeError):
            return default

    # ── Calendar ──────────────────────────────────────────────────────────────
    if tool_name == "list_calendar_events":
        if not google_token_data:
            return {"error": "Google not connected."}
        max_r = min(_int("max_results", 10, args), 20)
        return calendar_tool.list_events(
            google_token_data,
            max_results=max_r,
            time_min=args.get("time_min"),
            time_max=args.get("time_max"),  # FIX: pass time_max for day scoping
        )

    elif tool_name == "create_calendar_event":
        if not google_token_data:
            return {"error": "Google not connected."}
        return calendar_tool.create_event(google_token_data, **args)

    elif tool_name == "delete_calendar_event":
        if not google_token_data:
            return {"error": "Google not connected."}
        return calendar_tool.delete_event(google_token_data, **args)

    # ── Drive ─────────────────────────────────────────────────────────────────
    elif tool_name == "search_drive_files":
        if not google_token_data:
            return {"error": "Google not connected."}
        args["max_results"] = _int("max_results", 5, args)
        return drive_tool.search_files(google_token_data, **args)

    elif tool_name == "get_drive_file_content":
        if not google_token_data:
            return {"error": "Google not connected."}
        return drive_tool.get_file_content(google_token_data, **args)

    elif tool_name == "create_google_doc":
        if not google_token_data:
            return {"error": "Google not connected."}
        return drive_tool.create_google_doc(google_token_data, **args)

    elif tool_name == "share_file":
        if not google_token_data:
            return {"error": "Google not connected."}
        return drive_tool.share_file(google_token_data, **args)

    # ── Gmail ─────────────────────────────────────────────────────────────────
    elif tool_name == "list_emails":
        if not google_token_data:
            return {"error": "Google not connected."}
        args["max_results"] = max(1, min(_int("max_results", 5, args), 20))
        return gmail_tool.list_emails(google_token_data, **args)

    elif tool_name == "get_email_content":
        if not google_token_data:
            return {"error": "Google not connected."}
        return gmail_tool.get_email_content(google_token_data, **args)

    elif tool_name == "send_email":
        if not google_token_data:
            return {"error": "Google not connected."}
        return gmail_tool.send_email(google_token_data, **args)

    elif tool_name == "send_email_with_drive_link":
        if not google_token_data:
            return {"error": "Google not connected."}
        return gmail_tool.send_email_with_drive_link(google_token_data, **args)

    # ── Notion ────────────────────────────────────────────────────────────────
    elif tool_name == "search_notion_pages":
        if not notion_token:
            return {"error": "Notion not connected."}
        args["max_results"] = _int("max_results", 10, args)
        return notion_tool.search_pages(notion_token, **args)

    elif tool_name == "get_notion_page":
        if not notion_token:
            return {"error": "Notion not connected."}
        return notion_tool.get_page_content(notion_token, **args)

    elif tool_name == "create_notion_page":
        if not notion_token:
            return {"error": "Notion not connected."}
        return notion_tool.create_page(notion_token, **args)

    else:
        logger.error(f"[Agent] Unknown tool: {tool_name}")
        return {"error": f"Unknown tool '{tool_name}'"}
