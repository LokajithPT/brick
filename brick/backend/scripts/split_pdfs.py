import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import pymupdf as fitz
except ImportError:
    import fitz

SCRIPT_DIR = Path(__file__).parent.parent.parent
PDF_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = SCRIPT_DIR / "tmp" / "pdf_chunks"
MAX_PAGES_PER_CHUNK = 50


def split_pdf(input_path: str, output_dir: str, pages_per_chunk: int = 50):
    os.makedirs(output_dir, exist_ok=True)

    doc = fitz.open(input_path)
    total_pages = len(doc)
    base_name = os.path.splitext(os.path.basename(input_path))[0]

    chunks = []
    for i in range(0, total_pages, pages_per_chunk):
        end = min(i + pages_per_chunk, total_pages)
        chunk_path = os.path.join(output_dir, f"{base_name}_p{i + 1}-{end}.pdf")

        chunk_doc = fitz.open()
        for page_num in range(i, end):
            chunk_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

        chunk_doc.save(chunk_path)
        chunk_doc.close()

        chunks.append(chunk_path)
        print(f"Created: {chunk_path} ({end - i} pages)")

    doc.close()
    return chunks


if __name__ == "__main__":
    files = [
        ("Marlette Permit Set 8.20.2025.pdf", "permit_set"),
        ("MARLETTE_WORKING DESIGN BOOK_02.16.2026.pdf", "working_design_book"),
    ]

    for filename, namespace in files:
        filepath = os.path.join(PDF_DIR, filename)
        output_dir = os.path.join(OUTPUT_DIR, namespace)

        print(f"\nSplitting: {filename}")
        chunks = split_pdf(filepath, output_dir)
        print(f"Created {len(chunks)} chunks")
