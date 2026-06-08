import re
import pdfplumber


def parse_file(filepath: str, strip_math: bool = False, strip_code: bool = True) -> str:
    """Read a .md, .txt, or .pdf file and return clean plain text."""

    if filepath.endswith(".txt"):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read().strip()

    if filepath.endswith(".md"):
        return _parse_markdown(filepath, strip_math, strip_code)

    if filepath.endswith(".pdf"):
        return _parse_pdf(filepath)

    if filepath.endswith(".docx"):
        return _parse_docx(filepath)

    raise ValueError(f"Unsupported file type: {filepath}. Supported: .md .txt .pdf .docx")


# ── MARKDOWN ──────────────────────────────────────────────────────────────────

def _parse_markdown(filepath: str, strip_math: bool = False, strip_code: bool = True) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Remove images
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)

    # Remove links but keep text
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)

    # Remove heading hashes but keep text
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

    # Remove bold and italic
    text = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,3}(.*?)_{1,3}", r"\1", text)

    # Remove horizontal rules
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)

    # Remove inline code but keep content
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # Strip or keep code blocks
    if strip_code:
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    else:
        text = re.sub(r"```(?:\w+)?\n?", "", text)

    # Remove blockquote markers
    text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)

    # Remove list markers
    text = re.sub(r"^[\s]*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[\s]*\d+\.\s+", "", text, flags=re.MULTILINE)

    # Strip math if requested
    if strip_math:
        text = re.sub(r"\$\$.*?\$\$", "", text, flags=re.DOTALL)
        text = re.sub(r"\$[^$]+\$", "", text)
        text = re.sub(r"\\[a-zA-Z]+\{.*?\}", "", text)

    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ── PDF ───────────────────────────────────────────────────────────────────────

def _parse_pdf(filepath: str) -> str:
    """
    Extract text and tables from PDF.

    Strategy:
    - Each page: extract tables first, then remaining text
    - Tables converted to markdown format before embedding
    - Pages separated clearly so chunks don't bleed across pages
    """
    pages_content = []

    with pdfplumber.open(filepath) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):

            page_parts = []

            # ── Extract tables ─────────────────────────────────────────────
            tables = page.extract_tables()
            table_bboxes = []

            for table in tables:
                if not table:
                    continue

                # convert table to markdown
                md_table = _table_to_markdown(table)
                if md_table:
                    page_parts.append(md_table)

                # track table bounding boxes to exclude from text extraction
                for table_obj in page.find_tables():
                    table_bboxes.append(table_obj.bbox)

            # ── Extract text (excluding table areas) ───────────────────────
            if table_bboxes:
                # crop page to exclude table regions
                remaining_text = _extract_text_excluding_tables(page, table_bboxes)
            else:
                remaining_text = page.extract_text()

            if remaining_text:
                cleaned = _clean_pdf_text(remaining_text)
                if cleaned:
                    page_parts.append(cleaned)

            if page_parts:
                pages_content.append(f"[Page {page_num}]\n" + "\n\n".join(page_parts))

    if not pages_content:
        return ""

    return "\n\n".join(pages_content).strip()


def _table_to_markdown(table: list) -> str:
    """
    Convert pdfplumber table (list of lists) to markdown table string.

    Input:  [["Name", "Age", "City"], ["John", "25", "NYC"]]
    Output: | Name | Age | City |
            |------|-----|------|
            | John | 25  | NYC  |
    """
    if not table or len(table) < 1:
        return ""

    # clean cells — replace None with empty string, strip whitespace
    cleaned = []
    for row in table:
        cleaned_row = [str(cell).strip() if cell is not None else "" for cell in row]
        cleaned.append(cleaned_row)

    if not cleaned:
        return ""

    # first row = header
    header = cleaned[0]
    separator = ["---"] * len(header)
    rows = cleaned[1:] if len(cleaned) > 1 else []

    # build markdown
    lines = []
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(separator) + " |")
    for row in rows:
        # pad row if fewer columns than header
        while len(row) < len(header):
            row.append("")
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def _extract_text_excluding_tables(page, table_bboxes: list) -> str:
    """Extract text from page regions that don't overlap with tables."""
    words = page.extract_words()
    if not words:
        return ""

    filtered_words = []
    for word in words:
        word_bbox = (word["x0"], word["top"], word["x1"], word["bottom"])
        in_table = any(_bbox_overlap(word_bbox, t_bbox) for t_bbox in table_bboxes)
        if not in_table:
            filtered_words.append(word["text"])

    return " ".join(filtered_words)


def _bbox_overlap(bbox1: tuple, bbox2: tuple) -> bool:
    """Check if two bounding boxes overlap."""
    x0_1, y0_1, x1_1, y1_1 = bbox1
    x0_2, y0_2, x1_2, y1_2 = bbox2
    return not (x1_1 < x0_2 or x1_2 < x0_1 or y1_1 < y0_2 or y1_2 < y0_1)


def _clean_pdf_text(text: str) -> str:
    """Clean raw PDF extracted text."""
    if not text:
        return ""

    # normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)

    # fix hyphenated line breaks (word- \nbreak -> wordbreak)
    text = re.sub(r"-\n(\w)", r"\1", text)

    # collapse excessive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ── DOCX ──────────────────────────────────────────────────────────────────────

def _parse_docx(filepath: str) -> str:
    """
    Extract text and tables from Word documents.

    Strategy:
    - Iterate document body in order — paragraphs and tables
    - Tables converted to same markdown format as PDF tables
    - Preserves document reading order
    """
    try:
        from docx import Document
    except ImportError:
        raise ImportError(
            "❌ python-docx not installed.\n"
            "   Run: pip install python-docx"
        )

    doc = Document(filepath)
    parts = []

    for block in doc.element.body:
        tag = block.tag.split("}")[-1]  # strip namespace

        if tag == "p":
            # paragraph
            from docx.oxml.ns import qn
            para_text = "".join(
                node.text for node in block.iter()
                if node.tag == qn("w:t") and node.text
            )
            para_text = para_text.strip()
            if para_text:
                parts.append(para_text)

        elif tag == "tbl":
            # table — convert to markdown
            from docx import Document as DocxDocument
            from docx.table import Table
            tbl = Table(block, doc)
            md_table = _docx_table_to_markdown(tbl)
            if md_table:
                parts.append(md_table)

    if not parts:
        return ""

    return "\n\n".join(parts).strip()


def _docx_table_to_markdown(table) -> str:
    """
    Convert python-docx Table object to markdown table string.
    Reuses same markdown format as _table_to_markdown() for PDF.
    """
    rows = []
    for row in table.rows:
        cells = [cell.text.strip() for cell in row.cells]
        rows.append(cells)

    if not rows:
        return ""

    # deduplicate merged cells — python-docx repeats merged cell text
    cleaned_rows = []
    for row in rows:
        cleaned = []
        for i, cell in enumerate(row):
            if i == 0 or cell != row[i - 1]:
                cleaned.append(cell)
            else:
                cleaned.append("")
        cleaned_rows.append(cleaned)

    return _table_to_markdown(cleaned_rows)