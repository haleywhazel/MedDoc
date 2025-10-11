"use client";

import type { PDFViewerProps } from "@/components/PDFViewer";
import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import ChatInput from "../components/ChatInput";
import MessageBubble from "../components/MessageBubble";
import { Message, Source } from "../types";

const PDFViewer = dynamic<PDFViewerProps>(
  () => import("@/components/PDFViewer"),
  { ssr: false },
);

export default function Home() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentPdf, setCurrentPdf] = useState<{
    file: string;
    page?: number | null;
  } | null>(null);

  useEffect(() => {
    const el = document.getElementById("chat-bottom");
    el?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    const trimmed = question.trim();
    if (!trimmed) return;

    let placeholderIndex: number | null = null;
    setMessages((prev) => {
      const updated = [
        ...prev,
        { sender: "user" as const, text: trimmed },
        { sender: "bot" as const, text: "…", loading: true },
      ];
      placeholderIndex = updated.length - 1;
      return updated;
    });
    setQuestion("");
    setLoading(true);

    try {
      const endpoint = "/api/chat";
      const url = `${process.env.NEXT_PUBLIC_BACKEND_URL}${endpoint}`;

      const messageHistory = messages.map((msg) => ({
        role: msg.sender === "user" ? "user" : "assistant",
        content: msg.text || msg.words?.join(" ") || "",
      }));

      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: trimmed,
          trace: false,
          history: messageHistory,
        }),
      });
      const data = await res.json();
      await new Promise((r) => setTimeout(r, 500));

      if (placeholderIndex !== null) {
        setMessages((prev) => {
          const updated = [...prev];
          updated[placeholderIndex!] = {
            sender: "bot" as const,
            words: [],
            sources: [],
          };
          return updated;
        });

        const words: string[] = (data.answer ?? "(no answer)").split(/\s+/);
        const sources = data.sources as Source[] | undefined;
        if (sources && sources.length > 0) {
          const s0 = sources[0];
          console.log("Opening PDF:", s0.file, "page", s0.page);
          setCurrentPdf({
            file: s0.file,
            page: s0.page != null ? Number(s0.page) : undefined,
          });
        }
        let i = 0;
        const step = 2;
        const interval = setInterval(() => {
          i += step;
          setMessages((prev) => {
            const updated = [...prev];
            const msg = updated[placeholderIndex!];
            if (msg && msg.words) {
              msg.words = words.slice(0, i);
              if (i >= words.length && sources) msg.sources = sources;
            }
            return updated;
          });
          if (i >= words.length) {
            clearInterval(interval);
            setMessages((prev) => {
              const updated = [...prev];
              const msgFinal = updated[placeholderIndex!];
              if (msgFinal && msgFinal.words) {
                msgFinal.text = words.join(" ");
                delete msgFinal.words;
                if (sources) msgFinal.sources = sources;
              }
              return updated;
            });
          }
        }, 50);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Enhanced Header */}
      <header className="px-6 py-4 flex justify-between items-center bg-white border-b border-slate-200 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-lg flex items-center justify-center shadow-md">
            <svg
              className="w-6 h-6 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
              />
            </svg>
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-800">
              HR Query Assistant
            </h1>
            <p className="text-xs text-slate-500">
              Intelligent document analysis
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {currentPdf && (
            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              <span className="text-xs font-medium text-blue-700">
                Document Active
              </span>
            </div>
          )}
        </div>
      </header>

      {/* Content area */}
      <main className="flex-1 flex overflow-hidden">
        {/* PDF viewer */}
        <div className="flex-1 hidden md:flex flex-col bg-white border-r border-slate-200">
          <div className="flex-1 overflow-hidden">
            <PDFViewer
              fileUrl={
                currentPdf
                  ? `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/pdf?file=${encodeURIComponent(currentPdf.file)}`
                  : null
              }
              page={currentPdf?.page}
            />
          </div>
        </div>

        {/* Chat column */}
        <div className="w-full md:w-[540px] flex flex-col bg-gradient-to-b from-slate-50 to-white">
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Messages area */}
            <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full text-center px-4">
                  <div className="w-20 h-20 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-2xl flex items-center justify-center mb-6 shadow-lg">
                    <svg
                      className="w-10 h-10 text-blue-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                      />
                    </svg>
                  </div>
                  <h2 className="text-2xl font-bold text-slate-800 mb-3">
                    Welcome to HR Query
                  </h2>
                  <p className="text-slate-600 max-w-md mb-6">
                    Ask questions about your HR documents and get instant
                    answers with source references.
                  </p>
                  <div className="grid grid-cols-1 gap-3 w-full max-w-md">
                    {[
                      "What is our vacation policy?",
                      "Tell me about benefits enrollment",
                      "What are the remote work guidelines?",
                    ].map((suggestion, idx) => (
                      <button
                        key={idx}
                        onClick={() => setQuestion(suggestion)}
                        className="px-4 py-3 bg-white border border-slate-200 rounded-xl text-sm text-slate-700 hover:border-blue-300 hover:bg-blue-50 transition-all duration-200 text-left shadow-sm hover:shadow"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {messages.map((m, idx) => (
                <MessageBubble
                  key={idx}
                  message={m}
                  onSourceClick={(file, pg) => {
                    setCurrentPdf({
                      file,
                      page: pg != null ? Number(pg) : undefined,
                    });
                  }}
                />
              ))}
              <div id="chat-bottom" />
            </div>

            {/* Input area */}
            <div className="p-6 bg-white border-t border-slate-200">
              <ChatInput
                value={question}
                onValueChange={setQuestion}
                onSend={send}
                loading={loading}
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
