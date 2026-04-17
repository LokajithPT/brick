import os
import httpx
from dotenv import load_dotenv
import time

load_dotenv()


class LlamaParser:
    def __init__(self):
        self.api_key = os.getenv("LLAMAPARSE_API_KEY")
        self.base_url = "https://cloud.llamaindex.ai/api"
        if not self.api_key:
            raise ValueError("LLAMAPARSE_API_KEY not set")

    async def parse_file(self, file_path: str, namespace: str = "default") -> dict:
        import uuid

        job_id = str(uuid.uuid4())
        file_size = os.path.getsize(file_path)

        if file_size > 30 * 1024 * 1024:
            return {
                "job_id": job_id,
                "status": "error",
                "error": "File too large. Need to split.",
            }

        with open(file_path, "rb") as f:
            file_content = f.read()

        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                f"{self.base_url}/parsing/upload",
                headers={"Authorization": f"Bearer {self.api_key}"},
                data={"namespace": namespace},
                files={
                    "file": (
                        os.path.basename(file_path),
                        file_content,
                        "application/pdf",
                    )
                },
            )

        if response.status_code == 200:
            result = response.json()
            return {
                "job_id": result.get("job_id", job_id),
                "status": "processing",
                "document_id": result.get("document_id"),
            }
        else:
            return {"job_id": job_id, "status": "error", "error": response.text}

    async def parse_file_multipart(
        self, file_path: str, namespace: str = "default"
    ) -> dict:
        import uuid

        job_id = str(uuid.uuid4())

        with open(file_path, "rb") as f:
            file_content = f.read()

        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                f"{self.base_url}/parsing/upload",
                headers={"Authorization": f"Bearer {self.api_key}"},
                data={"namespace": namespace},
                files={
                    "file": (
                        os.path.basename(file_path),
                        file_content,
                        "application/pdf",
                    )
                },
            )

        if response.status_code == 200:
            result = response.json()
            return {
                "job_id": result.get("job_id", job_id),
                "status": "processing",
                "document_id": result.get("document_id"),
            }
        else:
            return {"job_id": job_id, "status": "error", "error": response.text}

    async def get_job_status(self, job_id: str) -> dict:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(
                f"{self.base_url}/parsing/job/{job_id}",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            if response.status_code == 200:
                return response.json()
            return {"status": "unknown", "raw": response.text}

    async def get_parsed_content(self, job_id: str) -> dict:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.get(
                f"{self.base_url}/parsing/job/{job_id}/content/markdown",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            if response.status_code == 200:
                return response.json()
            return {"markdown": "", "error": response.text}

    async def extract_images(self, markdown: str) -> list[dict]:
        return []
