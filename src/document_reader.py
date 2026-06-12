from pathlib import Path
from pypdf import PdfReader
from docx import Document



def _extract_plain_text(path: Path) -> str:
    return path.read_text(encoding = "utf-8")
    
def _extract_pdf(path: Path) -> str:
    reader = PdfReader(path)

    pages_text = [page.extract_text() for page in reader.pages if page.extract_text()]
    return "\n".join(pages_text)

def _extract_docx(path: Path) -> str:
    doc = Document(path)

    paragraphs_text = [paragraph.text for paragraph in doc.paragraphs if paragraph.text]
    return "\n".join(paragraphs_text)

EXTRACTOR_MAP = {
    ".txt": _extract_plain_text,
    ".md": _extract_plain_text,
    ".csv": _extract_plain_text,
    ".pdf": _extract_pdf,
    ".docx": _extract_docx
}

def extract_text(file_path):
    """
    Reads files and extracts text based off file format.
    Supported Formats: .txt, .md, .csv, .pdf, .docx
    """

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Could not find file: {file_path}")
    
    extension = path.suffix.lower()

    extractor_function = EXTRACTOR_MAP.get(path.suffix.lower())

    if not extractor_function:
        raise ValueError(f"Unsupported file type: {extension}")
    
    return extractor_function(path).strip()