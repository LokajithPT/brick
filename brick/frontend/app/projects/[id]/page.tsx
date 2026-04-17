"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  getProjects,
  uploadDocument,
  parseDocument,
  getDocumentStatus,
  getDocumentIndex,
  queryDocuments,
  type Project,
  type Document,
} from "@/lib/api";

function renderMarkdown(text: string) {
  const lines = text.split('\n');
  return lines.map((line, i) => {
    const trimmed = line.trim();
    if (!trimmed) return <br key={i} />;
    if (trimmed.startsWith('**') && trimmed.endsWith('**') && !trimmed.slice(2, -2).includes('**')) {
      return <h3 key={i} className="text-lg font-bold text-white mt-4 mb-2">{trimmed.replace(/\*\*/g, '')}</h3>;
    }
    if (trimmed.startsWith('- ')) {
      return <li key={i} className="ml-4 text-white list-disc">{trimmed.replace(/^- /, '')}</li>;
    }
    if (/^\d+\./.test(trimmed)) {
      return <li key={i} className="ml-4 text-white list-decimal">{trimmed.replace(/^\d+\.\s*/, '')}</li>;
    }
    return <p key={i} className="text-white leading-relaxed mb-2">{trimmed}</p>;
  });
}

export default function ProjectPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const [project, setProject] = useState<Project | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"docs" | "chat">("docs");

  const [uploading, setUploading] = useState(false);
  const [parsingDocs, setParsingDocs] = useState<Record<string, number>>({});

  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState<Array<{role: string; content: string}>>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadProject();
  }, [projectId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  const loadProject = async () => {
    try {
      const data = await getProjects();
      const found = data.projects.find((p: Project) => p.id === projectId);
      if (found) {
        setProject(found);
        const docData = await fetch(`/api/projects/${projectId}/documents`).then(r => r.json());
        setDocuments(docData.documents || []);
      } else {
        router.push("/projects");
      }
    } catch (err) {
      console.error("Failed to load project");
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files?.length) return;

    setUploading(true);
    for (const file of Array.from(files)) {
      try {
        const result = await uploadDocument(file, projectId);
        setDocuments(prev => [...prev, result.document]);

        setParsingDocs(prev => ({ ...prev, [result.document.id]: 0 }));

        parseDocument(result.document.id);

        const pollStatus = async () => {
          const status = await getDocumentStatus(result.document.id);
          setParsingDocs(prev => ({ ...prev, [result.document.id]: status.progress?.percentage || 0 }));

          if (status.status === "parsed" || status.status === "error") {
            setDocuments(prev => prev.map(d =>
              d.id === result.document.id ? { ...d, ...status } : d
            ));
            setTimeout(() => {
              setParsingDocs(prev => {
                const next = { ...prev };
                delete next[result.document.id];
                return next;
              });
            }, 1000);
          } else {
            setTimeout(pollStatus, 1000);
          }
        };
        setTimeout(pollStatus, 500);
      } catch (err) {
        console.error("Upload failed:", err);
      }
    }
    setUploading(false);
    e.target.value = "";
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || chatLoading) return;

    const userMsg = { role: "user", content: chatInput };
    setChatMessages(prev => [...prev, userMsg]);
    const question = chatInput;
    setChatInput("");
    setChatLoading(true);

    try {
      const result = await queryDocuments(question, projectId);
      setChatMessages(prev => [...prev, { role: "assistant", content: result.answer }]);
    } catch (err) {
      setChatMessages(prev => [...prev, { role: "assistant", content: "Failed to get answer" }]);
    } finally {
      setChatLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent" />
      </div>
    );
  }

  if (!project) return null;

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="max-w-6xl mx-auto p-6">
        <div className="flex items-center gap-4 mb-6">
          <Link href="/projects" className="p-2 hover:bg-gray-800 rounded-lg">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </Link>
          <h1 className="text-2xl font-bold flex-1">{project.name}</h1>
          <div className="flex gap-2 bg-gray-800 rounded-lg p-1">
            <button
              onClick={() => setTab("docs")}
              className={`px-4 py-2 rounded-lg text-sm ${tab === "docs" ? "bg-blue-600" : "hover:bg-gray-700"}`}
            >
              Documents
            </button>
            <button
              onClick={() => setTab("chat")}
              className={`px-4 py-2 rounded-lg text-sm ${tab === "chat" ? "bg-blue-600" : "hover:bg-gray-700"}`}
            >
              Chat
            </button>
          </div>
        </div>

        {tab === "docs" ? (
          <div>
            <div className="mb-6">
              <label className="block w-full p-8 border-2 border-dashed border-gray-700 rounded-lg text-center cursor-pointer hover:border-blue-500 transition">
                <input
                  type="file"
                  accept=".pdf"
                  multiple
                  onChange={handleUpload}
                  className="hidden"
                  disabled={uploading}
                />
                <svg className="w-12 h-12 mx-auto mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <span className="text-gray-400">
                  {uploading ? "Uploading..." : "Drop PDFs here or click to upload"}
                </span>
              </label>
            </div>

            {documents.length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                <p>No documents uploaded yet.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {documents.map(doc => (
                  <div key={doc.id} className="bg-gray-800 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <h3 className="font-medium">{doc.filename}</h3>
                        <p className="text-sm text-gray-400">
                          {doc.status === "parsed"
                            ? `${doc.page_count} pages`
                            : parsingDocs[doc.id] !== undefined && parsingDocs[doc.id] < 100
                            ? `Parsing... ${parsingDocs[doc.id]}%`
                            : doc.status === "error"
                            ? "Error"
                            : "Ready to parse"}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        {parsingDocs[doc.id] !== undefined && parsingDocs[doc.id] < 100 && (
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-gray-400">{parsingDocs[doc.id]}%</span>
                            <div className="w-32 bg-gray-700 rounded-full h-2">
                              <div
                                className="bg-blue-500 h-2 rounded-full transition-all"
                                style={{ width: `${parsingDocs[doc.id]}%` }}
                              />
                            </div>
                          </div>
                        )}
                        {doc.status === "parsed" && (
                          <Link
                            href={`/docs?doc=${doc.id}`}
                            className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm"
                          >
                            Browse
                          </Link>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col h-[calc(100vh-180px)]">
            <div className="flex-1 overflow-y-auto space-y-4 mb-4">
              {chatMessages.length === 0 ? (
                <div className="text-center py-12 text-gray-400">
                  <p>Ask questions about your project documents.</p>
                  <p className="text-sm mt-2">Example: "What kitchen appliances are specified?"</p>
                </div>
              ) : (
                chatMessages.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                    <div className={`max-w-xl px-4 py-3 rounded-2xl ${msg.role === "user" ? "bg-blue-600 text-white" : "bg-gray-800"}`}>
                      {msg.role === "assistant" ? (
                        <div className="text-white">{renderMarkdown(msg.content)}</div>
                      ) : (
                        <span>{msg.content}</span>
                      )}
                    </div>
                  </div>
                ))
              )}
              {chatLoading && (
                <div className="flex justify-start">
                  <div className="bg-gray-800 rounded-2xl px-4 py-3">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{animationDelay: '0ms'}} />
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{animationDelay: '150ms'}} />
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{animationDelay: '300ms'}} />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <form onSubmit={sendMessage} className="flex gap-3">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Ask about your project..."
                className="flex-1 p-4 bg-gray-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={chatLoading}
              />
              <button
                type="submit"
                disabled={chatLoading || !chatInput.trim()}
                className="px-6 py-4 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-xl"
              >
                Send
              </button>
            </form>
          </div>
        )}
      </div>

      {selectedImage && (
        <div className="fixed inset-0 bg-black/90 flex items-center justify-center z-50 p-8" onClick={() => setSelectedImage(null)}>
          <img src={selectedImage} alt="Page" className="max-w-full max-h-full object-contain" />
        </div>
      )}
    </div>
  );
}
