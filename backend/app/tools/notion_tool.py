import httpx
from typing import Optional

NOTION_API = "https://api.notion.com/v1"


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def verify_token(token: str) -> dict:
    resp = httpx.get(f"{NOTION_API}/users/me", headers=_headers(token))
    resp.raise_for_status()
    return resp.json()


def search_pages(token: str, query: str = "", max_results: int = 10) -> dict:
    """
    Search Notion pages. Filter to only 'page' objects (not databases).
    Uses empty query to list ALL accessible pages when query is empty.
    """
    payload: dict = {
        "page_size": min(max_results, 20),
        "filter": {"value": "page", "property": "object"},  # Only pages, not databases
    }
    if query and query.strip():
        payload["query"] = query.strip()

    resp = httpx.post(f"{NOTION_API}/search", headers=_headers(token), json=payload)
    resp.raise_for_status()
    data = resp.json()

    results = []
    for r in data.get("results", []):
        if r.get("object") != "page":
            continue
        results.append({
            "id": r.get("id", "").replace("-", ""),  # Normalize UUID format
            "id_dashed": r.get("id"),                # Keep original too
            "title": _extract_title(r),
            "url": r.get("url"),
            "object": r.get("object"),
        })

    if results:
        pages_info = "\n".join([
            f"- {r['title']} (ID: {r['id']})"
            for r in results
        ])
        return {
            "pages": results,
            "count": len(results),
            "summary": f"Found {len(results)} accessible page(s):\n{pages_info}\n\nUse one of these IDs as parent_page_id."
        }

    return {
        "pages": [],
        "count": 0,
        "summary": (
            "No accessible pages found. "
            "Please share at least one Notion page with your integration: "
            "open a page in Notion → click '···' → 'Add connections' → select your integration."
        )
    }


def get_page_content(token: str, page_id: str) -> dict:
    page_id = _normalize_page_id(page_id)
    page = httpx.get(f"{NOTION_API}/pages/{page_id}", headers=_headers(token))
    page.raise_for_status()
    page_data = page.json()

    blocks_resp = httpx.get(f"{NOTION_API}/blocks/{page_id}/children", headers=_headers(token))
    blocks_resp.raise_for_status()
    blocks_data = blocks_resp.json()

    text_blocks = []
    for block in blocks_data.get("results", []):
        text = _extract_block_text(block)
        if text:
            text_blocks.append(text)

    return {
        "id": page_id,
        "title": _extract_title(page_data),
        "url": page_data.get("url"),
        "content": "\n".join(text_blocks),
    }


def create_page(token: str, parent_page_id: str, title: str, content: str) -> dict:
    # Strict validation — never proceed with a placeholder
    INVALID_IDS = {"none", "not available", "not_available", "search_result_id",
                   "unknown", "n/a", "na", "", "null", "undefined"}

    cleaned_id = parent_page_id.strip().lower()
    if cleaned_id in INVALID_IDS or len(cleaned_id) < 8:
        return {
            "error": (
                f"Invalid parent_page_id '{parent_page_id}'. "
                "You must use search_notion_pages first and copy an exact ID from the results. "
                "Never use placeholders."
            )
        }

    # Normalize UUID format (add dashes if missing)
    normalized_id = _normalize_page_id(parent_page_id.strip())
    children = _markdown_to_blocks(content)

    body = {
        "parent": {"page_id": normalized_id},
        "properties": {
            "title": {"title": [{"text": {"content": title}}]}
        },
        "children": children,
    }

    resp = httpx.post(f"{NOTION_API}/pages", headers=_headers(token), json=body)
    if not resp.is_success:
        error_detail = resp.text
        return {
            "error": f"Notion API error {resp.status_code}: {error_detail}. "
                     f"Ensure the parent page is shared with your integration."
        }

    data = resp.json()
    return {"id": data.get("id"), "url": data.get("url"), "title": title}


def append_to_page(token: str, page_id: str, content: str) -> dict:
    page_id = _normalize_page_id(page_id)
    children = _markdown_to_blocks(content)
    resp = httpx.patch(
        f"{NOTION_API}/blocks/{page_id}/children",
        headers=_headers(token),
        json={"children": children},
    )
    resp.raise_for_status()
    return {"success": True, "page_id": page_id}


def _normalize_page_id(page_id: str) -> str:
    """Convert 32-char hex to UUID format if needed."""
    clean = page_id.replace("-", "").strip()
    if len(clean) == 32:
        return f"{clean[:8]}-{clean[8:12]}-{clean[12:16]}-{clean[16:20]}-{clean[20:]}"
    return page_id.strip()


def _extract_title(obj: dict) -> str:
    props = obj.get("properties", {})
    for key in ["title", "Name", "Title"]:
        if key in props:
            title_arr = props[key].get("title", [])
            if title_arr:
                return title_arr[0].get("plain_text", "Untitled")
    return "Untitled"


def _extract_block_text(block: dict) -> str:
    btype = block.get("type", "")
    content = block.get(btype, {})
    rich_text = content.get("rich_text", [])
    return "".join(rt.get("plain_text", "") for rt in rich_text)


def _markdown_to_blocks(text: str) -> list:
    blocks = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("### "):
            blocks.append(_block("heading_3", stripped[4:]))
        elif stripped.startswith("## "):
            blocks.append(_block("heading_2", stripped[3:]))
        elif stripped.startswith("# "):
            blocks.append(_block("heading_1", stripped[2:]))
        elif stripped.startswith("- ") or stripped.startswith("* "):
            blocks.append(_block("bulleted_list_item", stripped[2:]))
        elif stripped[0].isdigit() and len(stripped) > 2 and stripped[1] in ".)" :
            blocks.append(_block("numbered_list_item", stripped[2:].strip()))
        else:
            blocks.append(_block("paragraph", stripped))
    return blocks


def _block(btype: str, text: str) -> dict:
    return {
        "object": "block",
        "type": btype,
        btype: {"rich_text": [{"type": "text", "text": {"content": text}}]}
    }
