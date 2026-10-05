import httpx
import json
import os
from config import (
    ANYTHINGLLM_BASE_URL,
    API_KEY,
    WORKSPACE_SLUG,
    LLM_API_BASE,
)

DOCUMENTS_DIR = os.path.expandvars(r"%APPDATA%\anythingllm-desktop\storage\documents\custom-documents")


class AnythingLLMClient:
    def __init__(self):
        self.base_url = ANYTHINGLLM_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }
        self.http = httpx.AsyncClient(base_url=self.base_url, headers=self.headers, timeout=30.0)
        self.llm_base = LLM_API_BASE

    async def get_workspaces(self) -> dict:
        response = await self.http.get("/api/workspaces")
        response.raise_for_status()
        return response.json()

    async def get_workspace(self, slug: str = WORKSPACE_SLUG) -> dict:
        response = await self.http.get(f"/api/workspace/{slug}")
        response.raise_for_status()
        return response.json()

    async def get_workspace_documents(self, slug: str = WORKSPACE_SLUG) -> list:
        workspace = await self.get_workspace(slug)
        documents = workspace.get("workspace", {}).get("documents", [])
        result = []
        for doc in documents:
            metadata_str = doc.get("metadata", "{}")
            if isinstance(metadata_str, str):
                metadata = json.loads(metadata_str)
            else:
                metadata = metadata_str

            doc_filename = doc.get("filename", "")
            title = metadata.get("title", "")
            page_content = self._read_document_content(doc_filename, metadata)
            result.append({
                "title": title,
                "content": page_content,
                "filename": doc_filename,
            })
        return result

    def _read_document_content(self, doc_filename: str, metadata: dict) -> str:
        if metadata.get("pageContent"):
            return metadata["pageContent"]

        json_path = os.path.join(DOCUMENTS_DIR, doc_filename)
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                content = data.get("pageContent", "")
                if content:
                    return content
            except Exception:
                pass

        return json.dumps(metadata, ensure_ascii=False)

    async def get_workspace_context(self, slug: str = WORKSPACE_SLUG) -> str:
        documents = await self.get_workspace_documents(slug)
        parts = []
        for doc in documents:
            parts.append(f"--- Document: {doc['title']} ---\n{doc['content']}")
        return "\n\n".join(parts)

    async def chat_with_workspace(self, question: str, slug: str = WORKSPACE_SLUG) -> str:
        context = await self.get_workspace_context(slug)
        full_prompt = (
            f"You are an AI assistant answering questions based on the following document context.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            f"Answer based only on the provided context. If the context does not contain the answer, "
            f"state that the information is not available in the provided documents."
        )
        return await self._call_llm(full_prompt)

    async def _call_llm(self, prompt: str) -> str:
        llm_headers = {"Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient(base_url=self.llm_base, timeout=5.0) as llm:
                response = await llm.post(
                    "/v1/chat/completions",
                    json={
                        "model": "qwen3-vl-4b-instruct",
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False,
                    },
                    headers=llm_headers,
                )
                if response.status_code != 200:
                    return f"LLM returned error {response.status_code}: {response.text[:200]}"
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0].get("message", {}).get("content", "")
                return str(data)
        except httpx.ConnectError:
            return (
                "Cannot connect to LLM at "
                f"{self.llm_base}/v1/chat/completions. "
                "Please ensure LM Studio or another compatible LLM server is running."
            )
        except Exception as e:
            return f"LLM call error: {str(e)}"

    async def close(self):
        await self.http.aclose()
