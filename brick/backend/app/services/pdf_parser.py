import os
import json
import fitz


def parse_pdf_to_index(
    pdf_path: str, output_dir: str, doc_id: str, progress_callback=None
) -> dict:
    os.makedirs(output_dir, exist_ok=True)

    doc = fitz.open(pdf_path)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    total_pages = len(doc)

    pages = {}

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_num_actual = page_num + 1

        text = ""
        try:
            text = page.get_text("text").strip()
        except:
            pass

        page_filename = f"{base_name}_p{page_num_actual}.png"
        page_path = os.path.join(output_dir, page_filename)

        try:
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            pix.save(page_path)
        except:
            page_path = None

        pages[str(page_num_actual)] = {
            "page_num": page_num_actual,
            "text_preview": text[:500] if text else "",
            "text_length": len(text),
            "has_image": page_path is not None,
            "image": page_filename,
        }

        if progress_callback:
            progress_callback(doc_id, page_num_actual, total_pages, "parsing")

    doc.close()

    index_data = {
        "document_id": os.path.basename(pdf_path),
        "total_pages": len(pages),
        "pages": pages,
        "created_at": str(os.path.getmtime(pdf_path)),
    }

    index_path = os.path.join(output_dir, "index.json")
    with open(index_path, "w") as f:
        json.dump(index_data, f, indent=2)

    markdown_path = os.path.join(output_dir, "content.md")
    with open(markdown_path, "w") as f:
        f.write(f"# {base_name}\n\n")
        for page_num_str, page_data in sorted(pages.items(), key=lambda x: int(x[0])):
            f.write(f"\n## Page {page_num_str}\n\n")
            if page_data["text_preview"]:
                f.write(page_data["text_preview"] + "\n")
            f.write(f"\n[Page Image](./{page_data['image']})\n")

    if progress_callback:
        progress_callback(doc_id, total_pages, total_pages, "completed")

    return index_data


def search_pages(index_data: dict, query: str, top_k: int = 10) -> list:
    query_terms = [t.lower() for t in query.replace("?", "").split() if len(t) > 2]
    results = []

    for page_num_str, page_data in index_data["pages"].items():
        page_num = int(page_num_str)
        text = page_data.get("text_preview", "").lower()
        text_len = page_data.get("text_length", 0)

        score = 0
        for term in query_terms:
            if term in text:
                score += 10
            if term in text[:200]:
                score += 5

        if text_len > 200:
            score += text_len / 100
        elif text_len < 100:
            score *= 0.5

        if score > 5:
            results.append(
                {
                    "page": page_num,
                    "score": score,
                    "text": page_data.get("text_preview", ""),
                    "image": page_data.get("image"),
                    "has_image": page_data.get("has_image", False),
                }
            )

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]
