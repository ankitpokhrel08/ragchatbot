import re

def parse_file(filepath: str) -> str:
    """Read a .md or .txt file and return clean plain text."""

    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    # If plain text — return as is
    if filepath.endswith(".txt"):
        return text.strip()

    # If markdown — strip formatting noise
    if filepath.endswith(".md"):
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Remove images ![alt](url)
        text = re.sub(r"!\[.*?\]\(.*?\)", "", text)

        # Remove links but keep link text [text](url) -> text
        text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)

        # Remove headings hashes but keep text
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

        # Remove bold and italic markers
        text = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", text)
        text = re.sub(r"_{1,3}(.*?)_{1,3}", r"\1", text)

        # Remove horizontal rules
        text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)

        # Remove inline code backticks but keep content
        text = re.sub(r"`([^`]+)`", r"\1", text)

        # Remove code blocks entirely (not useful for RAG)
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

        # Remove blockquote markers
        text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)

        # Remove bullet/list markers
        text = re.sub(r"^[\s]*[-*+]\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^[\s]*\d+\.\s+", "", text, flags=re.MULTILINE)

        # Collapse multiple blank lines into one
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    raise ValueError(f"Unsupported file type: {filepath}. Only .md and .txt supported.")