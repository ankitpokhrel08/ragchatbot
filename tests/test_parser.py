import os
import pytest
import tempfile


def write_temp_file(suffix: str, content: str) -> str:
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False, encoding="utf-8"
    )
    f.write(content)
    f.close()
    return f.name


def test_parse_txt():
    from ragchatbot.parser import parse_file
    path = write_temp_file(".txt", "Hello world. This is plain text.")
    try:
        result = parse_file(path)
        assert "Hello world" in result
    finally:
        os.unlink(path)


def test_parse_markdown_strips_formatting():
    from ragchatbot.parser import parse_file
    content = "# Heading\n\n**bold** and _italic_ text.\n\n- list item"
    path = write_temp_file(".md", content)
    try:
        result = parse_file(path)
        assert "Heading" in result
        assert "bold" in result
        assert "**" not in result
        assert "#" not in result
    finally:
        os.unlink(path)


def test_parse_markdown_removes_links():
    from ragchatbot.parser import parse_file
    content = "Click [here](https://example.com) for more."
    path = write_temp_file(".md", content)
    try:
        result = parse_file(path)
        assert "here" in result
        assert "https://example.com" not in result
    finally:
        os.unlink(path)


def test_parse_unsupported_raises():
    from ragchatbot.parser import parse_file
    path = write_temp_file(".csv", "a,b,c")
    try:
        with pytest.raises(ValueError, match="Unsupported file type"):
            parse_file(path)
    finally:
        os.unlink(path)


def test_parse_pdf():
    """Basic smoke test — just verify PDF returns a non-empty string."""
    import pdfplumber
    import tempfile
    from ragchatbot.parser import parse_file

    # create a minimal PDF using pdfplumber's underlying library
    try:
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Refund policy: 30 days.", ln=True)
        path = tempfile.mktemp(suffix=".pdf")
        pdf.output(path)
        result = parse_file(path)
        assert "Refund" in result or len(result) > 0
        os.unlink(path)
    except ImportError:
        pytest.skip("fpdf not installed — skipping PDF creation test")