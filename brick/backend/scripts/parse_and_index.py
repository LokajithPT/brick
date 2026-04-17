import os
import sys
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import fitz
except ImportError:
    import pymupdf as fitz

SCRIPT_DIR = Path(__file__).parent.parent.parent
PDF_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = SCRIPT_DIR / "assets"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_all_pages(pdf_path: str, output_dir: str, namespace: str) -> list[dict]:
    os.makedirs(output_dir, exist_ok=True)

    doc = fitz.open(pdf_path)
    pages = []
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]

    print(f"  Total pages: {len(doc)}")

    for page_num in range(len(doc)):
        page_filename = f"{base_name}_p{page_num + 1}.png"
        page_path = os.path.join(output_dir, page_filename)

        page = doc[page_num]

        text = ""
        try:
            text = page.get_text("text")
            if text:
                text = text.strip()
        except Exception as e:
            print(f"  Warning: Could not extract text from page {page_num + 1}: {e}")

        try:
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            pix.save(page_path)
        except Exception as e:
            print(f"  Warning: Could not render page {page_num + 1}: {e}")
            page_path = None

        page_obj = {
            "page_num": page_num + 1,
            "text": text,
            "page_image": page_path,
            "page_url": f"/images/{namespace}/{page_filename}" if page_path else None,
            "has_content": bool(text) or page_path is not None,
        }
        pages.append(page_obj)

        if (page_num + 1) % 25 == 0:
            print(f"  Processed {page_num + 1}/{len(doc)} pages...")

    doc.close()
    return pages


def generate_structured_markdown(pages: list[dict], namespace: str) -> str:
    lines = []
    lines.append(f"# {namespace.upper()} - Document Index\n")
    lines.append("## Page Index\n")

    sections = {}
    for page in pages:
        text = page["text"].lower() if page["text"] else ""

        section_name = "Other"
        keywords = {
            "kitchen": ["kitchen", "range", "hood", "cabinet", "fridge", "dishwasher"],
            "bathroom": ["bath", "shower", "sink", "toilet", "vanity", "water closet"],
            "bedroom": ["bedroom", "bed", "closet"],
            "living": ["living room", "great room", "fireplace"],
            "dining": ["dining", "bar"],
            "floor": ["floor", "flooring", "plan", "finish"],
            "lighting": ["light", "lighting", "fixture"],
            "exterior": ["exterior", "outdoor", "patio", "pool", "bbq"],
            "plumbing": ["plumb", "pipe", "drain", "water"],
            "electrical": ["electric", "outlet", "switch", "amp"],
        }

        for section, kws in keywords.items():
            if any(kw in text for kw in kws):
                section_name = section.capitalize()
                break

        if section_name not in sections:
            sections[section_name] = []
        sections[section_name].append(page["page_num"])

    for section, page_nums in sorted(sections.items()):
        lines.append(
            f"- **{section}**: Pages {min(page_nums)}-{max(page_nums)} ({len(page_nums)} pages)"
        )

    lines.append("\n---\n")

    for i, page in enumerate(pages):
        lines.append(f"\n{'=' * 60}")
        lines.append(f"PAGE {page['page_num']}")
        lines.append(f"{'=' * 60}\n")

        if page["text"]:
            lines.append(page["text"])

        if page["page_url"]:
            lines.append(f"\n[PAGE_IMAGE]: <> ({page['page_url']})")

        lines.append("")

    return "\n".join(lines)


def generate_index_json(pages: list[dict], namespace: str) -> dict:
    index = {"namespace": namespace, "total_pages": len(pages), "pages": {}}

    for page in pages:
        index["pages"][str(page["page_num"])] = {
            "text_preview": page["text"][:200] + "..."
            if len(page["text"]) > 200
            else page["text"],
            "text_length": len(page["text"]),
            "has_image": page["page_url"] is not None,
            "image_url": page["page_url"],
        }

    return index


def main():
    import warnings

    warnings.filterwarnings("ignore")

    files = [
        ("Marlette Permit Set 8.20.2025.pdf", "permit_set"),
        ("MARLETTE_WORKING DESIGN BOOK_02.16.2026.pdf", "working_design_book"),
    ]

    all_assets = []

    for filename, namespace in files:
        filepath = os.path.join(PDF_DIR, filename)
        if not os.path.exists(filepath):
            print(f"Skipping {filename} - not found")
            continue

        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        assets_dir = os.path.join(OUTPUT_DIR, namespace)

        print(f"\n{'=' * 60}")
        print(f"Processing: {filename} ({file_size_mb:.1f} MB)")
        print(f"{'=' * 60}")

        print("Extracting pages...")
        pages = extract_all_pages(filepath, assets_dir, namespace)

        pages_with_content = sum(1 for p in pages if p["has_content"])
        print(f"Pages with content: {pages_with_content}/{len(pages)}")

        print("Generating markdown...")
        markdown = generate_structured_markdown(pages, namespace)
        md_path = os.path.join(OUTPUT_DIR, f"{namespace}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        print(f"Saved: {md_path}")

        print("Generating index...")
        index = generate_index_json(pages, namespace)
        index_path = os.path.join(OUTPUT_DIR, f"{namespace}_index.json")
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)
        print(f"Saved: {index_path}")

        all_assets.append(
            {
                "namespace": namespace,
                "pages": len(pages),
                "md_file": md_path,
                "index_file": index_path,
                "assets_dir": assets_dir,
            }
        )

    master_index = {"documents": all_assets}
    with open(os.path.join(OUTPUT_DIR, "master_index.json"), "w") as f:
        json.dump(master_index, f, indent=2)

    print(f"\n{'=' * 60}")
    print("DONE!")
    print(f"{'=' * 60}")
    for asset in all_assets:
        print(f"  - {asset['namespace']}: {asset['pages']} pages")
    print(f"\nAll assets in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
