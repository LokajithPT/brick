import os
import json
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from app.config import DOCUMENTS_DIR


class DocumentStore:
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else DOCUMENTS_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.base_dir / "index.json"
        self.uploads_dir = self.base_dir / "uploads"
        self.parsed_dir = self.base_dir / "parsed"
        self.uploads_dir.mkdir(exist_ok=True)
        self.parsed_dir.mkdir(exist_ok=True)
        self._load_index()

    def _load_index(self):
        if self.index_file.exists():
            with open(self.index_file) as f:
                self.index = json.load(f)
        else:
            self.index = {"documents": {}, "last_updated": None}

    def _save_index(self):
        self.index["last_updated"] = datetime.now().isoformat()
        with open(self.index_file, "w") as f:
            json.dump(self.index, f, indent=2)

    def _generate_hash(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()[:16]

    def add_document(self, filename: str, content: bytes) -> dict:
        doc_hash = self._generate_hash(content)
        doc_id = f"{doc_hash}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        upload_path = self.uploads_dir / f"{doc_id}.pdf"
        with open(upload_path, "wb") as f:
            f.write(content)

        doc_info = {
            "id": doc_id,
            "filename": filename,
            "hash": doc_hash,
            "upload_path": str(upload_path),
            "parsed_path": None,
            "index_path": None,
            "page_count": 0,
            "status": "uploaded",
            "uploaded_at": datetime.now().isoformat(),
            "parsed_at": None,
        }

        self.index["documents"][doc_id] = doc_info
        self._save_index()

        return doc_info

    def update_document(self, doc_id: str, updates: dict):
        if doc_id in self.index["documents"]:
            self.index["documents"][doc_id].update(updates)
            self._save_index()

    def get_document(self, doc_id: str) -> dict:
        return self.index["documents"].get(doc_id)

    def list_documents(self) -> list:
        return list(self.index["documents"].values())

    def get_parsed_path(self, doc_id: str) -> Path:
        return self.parsed_dir / doc_id

    def delete_document(self, doc_id: str) -> bool:
        if doc_id in self.index["documents"]:
            doc = self.index["documents"][doc_id]

            if os.path.exists(doc.get("upload_path", "")):
                os.remove(doc["upload_path"])

            parsed_path = self.get_parsed_path(doc_id)
            if parsed_path.exists():
                shutil.rmtree(parsed_path)

            del self.index["documents"][doc_id]
            self._save_index()
            return True
        return False


DOCUMENT_STORE = DocumentStore()
