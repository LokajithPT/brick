"use client";

import { useState, useEffect, useCallback } from "react";

interface Document {
  id: string;
  filename: string;
  status: string;
  page_count: number;
  uploaded_at: string;
}

interface Progress {
  current_page: number;
  total_pages: number;
  percentage: number;
  status: string;
}

interface Section {
  pages: { page: number; image: string; preview: string }[];
}

export default function DocsManager() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [sections, setSections] = useState<{ [key: string]: Section }>({});
  const [uploading, setUploading] = useState(false);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [parsingDocs, setParsingDocs] = useState<{ [key: string]: Progress }>({});

  useEffect(() => {
    fetchDocuments();
  }, []);

  useEffect(() => {
    const parsing = documents.filter(d => d.status === "parsing" || d.status === "uploaded");
    parsing.forEach(doc => {
      fetchProgress(doc.id);
    });
  }, [documents]);

  const fetchDocuments = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/docs/");
      const data = await res.json();
      setDocuments(data.documents || []);
    } catch (err) {
      console.error("Failed to fetch documents");
    }
  };

  const fetchProgress = useCallback(async (docId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/docs/${docId}/progress`);
      const data = await res.json();
      
      setParsingDocs(prev => ({
        ...prev,
        [docId]: data
      }));

      if (data.status === "parsed") {
        fetchDocuments();
      } else if (data.status === "parsing") {
        setTimeout(() => fetchProgress(docId), 500);
      }
    } catch (err) {
      console.error("Failed to fetch progress");
    }
  }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("http://localhost:8000/api/docs/upload", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (data.success) {
        await fetchDocuments();
        
        setParsingDocs(prev => ({
          ...prev,
          [data.document.id]: {
            current_page: 0,
            total_pages: 0,
            percentage: 0,
            status: "parsing"
          }
        }));

        await fetch(`http://localhost:8000/api/docs/${data.document.id}/parse`, {
          method: "POST",
        });
        
        fetchProgress(data.document.id);
      }
    } catch (err) {
      console.error("Upload failed:", err);
    } finally {
      setUploading(false);
    }
  };

  const loadDocIndex = async (doc: Document) => {
    setSelectedDoc(doc);
    if (doc.status !== "parsed") return;

    try {
      const res = await fetch(`http://localhost:8000/api/docs/${doc.id}/index`);
      const data = await res.json();
      setSections(data.sections || {});
    } catch (err) {
      console.error("Failed to load index");
    }
  };

  const getImageUrl = (docId: string, image: string) => {
    return `http://localhost:8000/images/${docId}/${image}`;
  };

  const deleteDocument = async (docId: string) => {
    if (!confirm("Delete this document?")) return;
    try {
      await fetch(`http://localhost:8000/api/docs/${docId}`, { method: "DELETE" });
      await fetchDocuments();
      if (selectedDoc?.id === docId) {
        setSelectedDoc(null);
        setSections({});
      }
      setParsingDocs(prev => {
        const newState = { ...prev };
        delete newState[docId];
        return newState;
      });
    } catch (err) {
      console.error("Delete failed:", err);
    }
  };

  const getProgress = (docId: string): Progress | null => {
    return parsingDocs[docId] || null;
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold">Document Library</h1>
            <p className="text-gray-400">Upload and manage your PDF documents</p>
          </div>
          
          <label className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg cursor-pointer flex items-center gap-2">
            <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {uploading ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              )}
            </svg>
            {uploading ? "Uploading..." : "Upload PDF"}
            <input
              type="file"
              accept=".pdf"
              onChange={handleUpload}
              className="hidden"
              disabled={uploading}
            />
          </label>
        </div>

        <div className="grid grid-cols-12 gap-6">
          {/* Document List */}
          <div className="col-span-3 bg-gray-800 rounded-lg p-4">
            <h2 className="text-lg font-semibold mb-4">Documents ({documents.length})</h2>
            <div className="space-y-3">
              {documents.map((doc) => {
                const progress = getProgress(doc.id);
                const isParsing = doc.status === "parsing" || doc.status === "uploaded" || (progress && progress.status === "parsing");
                
                return (
                  <div
                    key={doc.id}
                    onClick={() => loadDocIndex(doc)}
                    className={`p-3 rounded-lg cursor-pointer transition-all ${
                      selectedDoc?.id === doc.id 
                        ? "bg-gray-700 ring-2 ring-blue-500" 
                        : "bg-gray-700/50 hover:bg-gray-700"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{doc.filename}</p>
                        
                        {isParsing && progress ? (
                          <div className="mt-2">
                            <div className="flex items-center justify-between text-xs mb-1">
                              <span className="text-yellow-400">Parsing...</span>
                              <span className="text-gray-400">{progress.percentage}%</span>
                            </div>
                            <div className="h-2 bg-gray-600 rounded-full overflow-hidden">
                              <div 
                                className="h-full bg-yellow-500 transition-all duration-300"
                                style={{ width: `${progress.percentage}%` }}
                              />
                            </div>
                            <p className="text-xs text-gray-500 mt-1">
                              Page {progress.current_page} of {progress.total_pages}
                            </p>
                          </div>
                        ) : doc.status === "parsed" ? (
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs px-2 py-0.5 bg-green-600 rounded">{doc.page_count} pages</span>
                          </div>
                        ) : doc.status === "error" ? (
                          <span className="text-xs px-2 py-0.5 bg-red-600 rounded mt-1 inline-block">Error</span>
                        ) : (
                          <span className="text-xs px-2 py-0.5 bg-gray-600 rounded mt-1 inline-block">Uploaded</span>
                        )}
                      </div>
                      <button
                        onClick={(e) => { e.stopPropagation(); deleteDocument(doc.id); }}
                        className="text-gray-400 hover:text-red-400 p-1 ml-2"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  </div>
                );
              })}
              {documents.length === 0 && (
                <p className="text-gray-500 text-center py-8">No documents yet</p>
              )}
            </div>
          </div>

          {/* Document Content */}
          <div className="col-span-9">
            {selectedDoc ? (
              <div className="bg-gray-800 rounded-lg p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-2xl font-bold">{selectedDoc.filename}</h2>
                    <p className="text-gray-400">
                      {selectedDoc.page_count > 0 ? `${selectedDoc.page_count} pages` : 'Not parsed'} • Uploaded {new Date(selectedDoc.uploaded_at).toLocaleDateString()}
                    </p>
                  </div>
                  {selectedDoc.status === "uploaded" && (
                    <button
                      onClick={async () => {
                        await fetch(`http://localhost:8000/api/docs/${selectedDoc.id}/parse`, { method: "POST" });
                        fetchProgress(selectedDoc.id);
                      }}
                      className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg"
                    >
                      Parse Document
                    </button>
                  )}
                </div>

                {selectedDoc.status !== "parsed" ? (
                  <div className="flex flex-col items-center justify-center h-64">
                    {(selectedDoc.status === "parsing" || (getProgress(selectedDoc.id)?.status === "parsing")) ? (
                      <div className="text-center w-full max-w-md">
                        <div className="mb-4">
                          <svg className="w-16 h-16 mx-auto text-blue-500 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                        </div>
                        <h3 className="text-xl font-semibold mb-2">Parsing Document</h3>
                        {getProgress(selectedDoc.id) && (
                          <>
                            <div className="mb-2">
                              <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
                                <div 
                                  className="h-full bg-blue-500 transition-all duration-500"
                                  style={{ width: `${getProgress(selectedDoc.id)?.percentage || 0}%` }}
                                />
                              </div>
                            </div>
                            <p className="text-gray-400">
                              Processing page {getProgress(selectedDoc.id)?.current_page || 0} of {getProgress(selectedDoc.id)?.total_pages || 0}
                            </p>
                            <p className="text-sm text-gray-500 mt-1">
                              {getProgress(selectedDoc.id)?.percentage || 0}% complete
                            </p>
                          </>
                        )}
                      </div>
                    ) : (
                      <div className="text-center">
                        <svg className="w-16 h-16 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <p className="text-gray-400">Click &quot;Parse Document&quot; to extract content</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-6">
                    {Object.entries(sections).map(([section, data]) => (
                      <div key={section}>
                        <h3 className="text-xl font-semibold text-blue-400 mb-4">{section}</h3>
                        <div className="grid grid-cols-4 gap-4">
                          {data.pages.map((p) => (
                            <div
                              key={p.page}
                              onClick={() => setSelectedImage(getImageUrl(selectedDoc.id, p.image))}
                              className="cursor-pointer hover:ring-2 ring-blue-500 rounded-lg overflow-hidden bg-gray-700"
                            >
                              <div className="h-32 bg-gray-600 relative">
                                <img
                                  src={getImageUrl(selectedDoc.id, p.image)}
                                  alt={`Page ${p.page}`}
                                  className="w-full h-full object-cover"
                                  onError={(e) => (e.target as HTMLImageElement).style.display = 'none'}
                                />
                              </div>
                              <div className="p-2">
                                <span className="text-sm text-gray-300">Page {p.page}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-gray-800 rounded-lg p-12 flex items-center justify-center h-full">
                <div className="text-center text-gray-400">
                  <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <p>Select a document to view its contents</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {selectedImage && (
        <div
          className="fixed inset-0 bg-black/90 flex items-center justify-center z-50 p-8"
          onClick={() => setSelectedImage(null)}
        >
          <img
            src={selectedImage}
            alt="Page"
            className="max-w-full max-h-full object-contain"
          />
          <button
            className="absolute top-4 right-4 text-white text-3xl hover:text-gray-300"
            onClick={() => setSelectedImage(null)}
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
}
