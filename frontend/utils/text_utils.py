from html import escape


def sanitize_text(text: str) -> str:
    return text.replace("\r\n", "\n").strip()


def format_html_preview(text: str) -> str:
    return "<br>".join(escape(text).split("\n"))