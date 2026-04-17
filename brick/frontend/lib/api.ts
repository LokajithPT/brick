const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
const DOCS_API = `${API_BASE}/docs`;
const PROJECTS_API = `${API_BASE}/projects`;

export interface Source {
  page: number;
  namespace: string;
  text: string;
}

export interface ImageResult {
  page: number;
  namespace: string;
  url: string;
}

export interface QueryResult {
  answer: string;
  sources: Source[];
  images: ImageResult[];
  question: string;
}

export interface Project {
  id: string;
  name: string;
  created_at: string;
  documents: string[];
  status: string;
}

export interface Document {
  id: string;
  filename: string;
  status: string;
  project_id?: string;
  page_count?: number;
  progress?: {
    current_page: number;
    total_pages: number;
    percentage: number;
    status: string;
  };
}

export async function queryDocuments(question: string, projectId?: string): Promise<QueryResult> {
  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      project_id: projectId,
      top_k: 5
    }),
  });
  if (!res.ok) throw new Error("Query failed");
  return res.json();
}

export async function getDocuments(projectId?: string) {
  if (projectId) {
    const res = await fetch(`${PROJECTS_API}/${projectId}/documents`);
    if (!res.ok) throw new Error("Failed to fetch project documents");
    return res.json();
  }
  const res = await fetch(`${DOCS_API}`);
  if (!res.ok) throw new Error("Failed to fetch documents");
  return res.json();
}

export async function getPage(namespace: string, pageNum: number) {
  const res = await fetch(`${DOCS_API}/${namespace}/page/${pageNum}`);
  if (!res.ok) throw new Error("Failed to fetch page");
  return res.json();
}

export async function uploadDocument(file: File, projectId?: string) {
  const formData = new FormData();
  formData.append("file", file);
  if (projectId) formData.append("project_id", projectId);

  const res = await fetch(`${DOCS_API}/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Upload failed");
  return res.json();
}

export async function parseDocument(docId: string) {
  const res = await fetch(`${DOCS_API}/${docId}/parse`, { method: "POST" });
  if (!res.ok) throw new Error("Parse failed");
  return res.json();
}

export async function getDocumentStatus(docId: string) {
  const res = await fetch(`${DOCS_API}/${docId}/status`);
  if (!res.ok) throw new Error("Status failed");
  return res.json();
}

export async function getDocumentIndex(docId: string) {
  const res = await fetch(`${DOCS_API}/${docId}/index`);
  if (!res.ok) throw new Error("Index failed");
  return res.json();
}

export async function getProjects() {
  const res = await fetch(`${PROJECTS_API}`);
  if (!res.ok) throw new Error("Failed to fetch projects");
  return res.json();
}

export async function createProject(name: string) {
  const res = await fetch(`${PROJECTS_API}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  if (!res.ok) throw new Error("Failed to create project");
  return res.json();
}

export async function deleteProject(projectId: string) {
  const res = await fetch(`${PROJECTS_API}/${projectId}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete project");
  return res.json();
}

export function getImageUrl(imagePath: string): string {
  if (imagePath.startsWith("http")) return imagePath;
  return `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}${imagePath}`;
}
