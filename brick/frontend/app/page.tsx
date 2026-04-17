"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { queryDocuments, getImageUrl } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: any[];
  images?: any[];
}

interface Chat {
  id: string;
  messages: Message[];
  title: string;
}

function renderMarkdown(text: string) {
  const lines = text.split('\n');
  
  return lines.map((line, i) => {
    const trimmed = line.trim();
    
    if (!trimmed) {
      return <br key={i} />;
    }
    
    if (trimmed.startsWith('**') && trimmed.endsWith('**') && !trimmed.slice(2, -2).includes('**')) {
      return (
        <h3 key={i} className="text-lg font-bold text-gray-800 mt-4 mb-2">
          {trimmed.replace(/\*\*/g, '')}
        </h3>
      );
    }
    
    if (trimmed.startsWith('- ')) {
      return (
        <li key={i} className="ml-4 text-gray-700 list-disc">
          {renderInlineBold(trimmed.replace(/^- /, ''))}
        </li>
      );
    }
    
    if (/^\d+\./.test(trimmed)) {
      return (
        <li key={i} className="ml-4 text-gray-700 list-decimal">
          {renderInlineBold(trimmed.replace(/^\d+\.\s*/, ''))}
        </li>
      );
    }
    
    return (
      <p key={i} className="text-gray-700 leading-relaxed mb-2">
        {renderInlineBold(trimmed)}
      </p>
    );
  });
}

function renderInlineBold(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, j) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={j} className="font-semibold text-gray-900">{part.replace(/\*\*/g, '')}</strong>;
    }
    return part;
  });
}

export default function Home() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showIndex, setShowIndex] = useState(false);
  const [documentIndex, setDocumentIndex] = useState<any>(null);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const currentChat = chats.find(c => c.id === currentChatId);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chats, currentChatId]);

  const createNewChat = () => {
    const newChat: Chat = {
      id: Date.now().toString(),
      messages: [],
      title: "New Chat"
    };
    setChats(prev => [newChat, ...prev]);
    setCurrentChatId(newChat.id);
    setShowIndex(false);
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage: Message = { role: "user", content: input };
    
    setChats(prev => prev.map(chat => 
      chat.id === currentChatId 
        ? { ...chat, messages: [...chat.messages, userMessage] }
        : chat
    ));
    
    const question = input;
    setInput("");
    setLoading(true);

    try {
      const result = await queryDocuments(question);
      
      const assistantMessage: Message = {
        role: "assistant",
        content: result.answer,
        sources: result.sources || [],
        images: result.images || []
      };

      setChats(prev => prev.map(chat => {
        if (chat.id === currentChatId) {
          const newMessages = [...chat.messages, assistantMessage];
          const title = chat.messages.length === 0 
            ? question.slice(0, 30) + (question.length > 30 ? "..." : "")
            : chat.title;
          return { ...chat, messages: newMessages, title };
        }
        return chat;
      }));
    } catch (err) {
      const errorMessage: Message = {
        role: "assistant",
        content: "Sorry, I couldn't connect to the backend. Make sure it's running."
      };
      setChats(prev => prev.map(chat => 
        chat.id === currentChatId 
          ? { ...chat, messages: [...chat.messages, errorMessage] }
          : chat
      ));
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const loadIndex = async () => {
    setShowIndex(true);
    if (!documentIndex) {
      try {
        const res = await fetch("http://localhost:8000/api/index/working_design_book");
        const data = await res.json();
        setDocumentIndex(data);
      } catch (err) {
        console.error("Failed to load index");
      }
    }
  };

  if (!currentChatId && !showIndex) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="max-w-2xl w-full p-8">
          <h1 className="text-5xl font-bold text-white text-center mb-4">BRICK</h1>
          <p className="text-gray-400 text-center mb-8">Marlette Residence Document Assistant</p>
          
          <div className="space-y-4">
            <button
              onClick={createNewChat}
              className="w-full p-4 bg-gray-800 hover:bg-gray-700 text-left rounded-lg text-white transition"
            >
              <span className="text-gray-400 text-sm">New Chat</span>
            </button>
            <button
              onClick={loadIndex}
              className="w-full p-4 bg-gray-800 hover:bg-gray-700 text-left rounded-lg text-white transition"
            >
              <span className="text-gray-400 text-sm">Browse Documents</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (showIndex) {
    return (
      <div className="min-h-screen bg-gray-900">
        <div className="max-w-4xl mx-auto p-4">
          <div className="flex items-center gap-4 mb-6">
            <button
              onClick={() => { setShowIndex(false); if (!currentChatId) createNewChat(); }}
              className="p-2 hover:bg-gray-800 rounded-lg text-white"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <h1 className="text-xl font-bold text-white">Document Index</h1>
          </div>

          {documentIndex ? (
            <div className="space-y-6">
              {Object.entries(documentIndex.sections).map(([section, pages]: [string, any[]]) => (
                <div key={section} className="bg-gray-800 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-blue-400 mb-4">{section}</h3>
                  <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
                    {pages.map((p: any) => (
                      <div
                        key={p.page}
                        onClick={() => setSelectedImage(getImageUrl(p.image))}
                        className="cursor-pointer hover:ring-2 ring-blue-500 rounded-lg overflow-hidden"
                      >
                        <img
                          src={getImageUrl(p.image)}
                          alt={`Page ${p.page}`}
                          className="w-full h-24 object-cover"
                          onError={(e) => (e.target as HTMLImageElement).style.display = 'none'}
                        />
                        <div className="p-2 bg-gray-700 text-center">
                          <span className="text-sm text-gray-300">PG {p.page}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent"></div>
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

  return (
    <div className="min-h-screen bg-gray-900 flex">
      {/* Sidebar */}
      <div className="w-64 bg-gray-800 p-4 flex flex-col">
        <button
          onClick={createNewChat}
          className="w-full p-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg mb-4 flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Chat
        </button>
        
        <button
          onClick={loadIndex}
          className="w-full p-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg mb-4 flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Browse Docs
        </button>

        <Link
          href="/projects"
          className="w-full p-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg mb-4 flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
          Projects
        </Link>

        <div className="flex-1 overflow-y-auto space-y-2">
          {chats.map(chat => (
            <button
              key={chat.id}
              onClick={() => { setCurrentChatId(chat.id); setShowIndex(false); }}
              className={`w-full p-2 text-left rounded-lg text-sm truncate ${chat.id === currentChatId ? 'bg-gray-700 text-white' : 'text-gray-400 hover:bg-gray-700'}`}
            >
              {chat.title}
            </button>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-8">
          <div className="max-w-3xl mx-auto space-y-6">
            {currentChat?.messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-xl ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-100'} rounded-2xl px-4 py-3`}>
                  {msg.role === 'assistant' && msg.images && msg.images.length > 0 && (
                    <div className="mb-4">
                      <p className="text-sm text-gray-400 mb-2">Related Pages:</p>
                      <div className="flex gap-2 overflow-x-auto pb-2">
                        {msg.images.map((img: any, j: number) => (
                          <div
                            key={j}
                            onClick={() => setSelectedImage(getImageUrl(img.url))}
                            className="flex-shrink-0 cursor-pointer hover:ring-2 ring-blue-500 rounded-lg overflow-hidden"
                          >
                            <img
                              src={getImageUrl(img.url)}
                              alt={`Page ${img.page}`}
                              className="w-20 h-20 object-cover"
                            />
                            <div className="text-center text-xs p-1 bg-gray-700">PG {img.page}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  <div className="space-y-1">{renderMarkdown(msg.content)}</div>
                </div>
              </div>
            ))}
            {loading && (
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
        </div>

        {/* Input */}
        <div className="p-4 bg-gray-800">
          <form onSubmit={sendMessage} className="max-w-3xl mx-auto">
            <div className="flex gap-3">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about kitchen specs, bathroom fixtures, flooring..."
                className="flex-1 p-4 bg-gray-700 text-white rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="p-4 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-white"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          </form>
        </div>
      </div>

      {selectedImage && (
        <div className="fixed inset-0 bg-black/90 flex items-center justify-center z-50 p-8" onClick={() => setSelectedImage(null)}>
          <img src={selectedImage} alt="Page" className="max-w-full max-h-full object-contain" />
        </div>
      )}
    </div>
  );
}
