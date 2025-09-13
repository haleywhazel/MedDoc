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
  const [currentPdf, setCurrentPdf] = useState<{ file: string; page?: number | null } | null>(null);
  const [prodMode, setProdMode] = useState(false);
  const [traceNext, setTraceNext] = useState(true);

  // Scroll to bottom when messages change
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
      const endpoint = traceNext ? "/api/chat/debug" : "/api/chat";
      const dummyParam = prodMode ? '' : 'use_dummy_response=1';
      const traceParam = traceNext ? '' : '';
      const qs = [dummyParam].filter(Boolean).join('&');
      const url = `${process.env.NEXT_PUBLIC_BACKEND_URL}${endpoint}${qs ? '?' + qs : ''}`;
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmed }),
      });
      const data = await res.json();
      await new Promise((r) => setTimeout(r, 500));

      if (placeholderIndex !== null) {
        setMessages((prev) => {
          const updated = [...prev];
          updated[placeholderIndex!] = { sender: "bot" as const, words: [], sources: [] }; // give links immediately
          return updated;
        });

        const words: string[] = (data.answer ?? "(no answer)").split(/\s+/);
        const sources = data.sources as Source[] | undefined;
        if (sources && sources.length > 0) {
          const s0 = sources[0];
          console.log("Opening PDF:", s0.file, "page", s0.page);
          setCurrentPdf({ file: s0.file, page: s0.page != null ? Number(s0.page) : undefined });
        }
        let i = 0;
        const interval = setInterval(() => {
          i += 1;
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
            // collapse to single text when animation done
            setMessages((prev) => {
              const updated = [...prev];
              const msgFinal = updated[placeholderIndex!];
              if (msgFinal && msgFinal.words) {
                msgFinal.text = words.join(" ");
                delete msgFinal.words;
                // no trace needed now
                if (sources) msgFinal.sources = sources;
              }
              return updated;
            });
          }
        }, 120);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <header className="px-4 py-2 flex justify-between items-center bg-white shadow">
        <h1 className="font-semibold">Ello</h1>
        <div className="flex gap-4 items-center">
          <label className="flex items-center gap-1 text-sm select-none">
            <input
              type="checkbox"
              checked={prodMode}
              onChange={(e) => {
                const checked = e.target.checked;
                setProdMode(checked);
                
              }}
              className="accent-blue-600"
            />
            Prod
          </label>
          <label className="flex items-center gap-1 text-sm select-none">
            <input
              type="checkbox"
              checked={traceNext}
              onChange={(e) => setTraceNext(e.target.checked)}
              className="accent-blue-600"
            />
            Trace
          </label>
        </div>
      </header>

      {/* Content area with PDF viewer (left) and chat (right) */}
      <main className="flex-1 flex overflow-hidden">
        {/* PDF viewer fills remaining space */}
        <div className="flex-1 hidden md:block border-r border-gray-300 bg-gray-50">
          <PDFViewer
            fileUrl={currentPdf ? `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/pdf?file=${encodeURIComponent(currentPdf.file)}` : null}
            page={currentPdf?.page}
          />
        </div>

        {/* Chat column fixed width */}
        <div className="w-full md:w-[400px] flex flex-col items-center overflow-hidden py-2">
          <div className="flex flex-col w-full flex-1 min-h-0 shadow bg-white">
            {/* Messages */}
            <div className="flex-1 min-h-0 overflow-y-scroll p-4 pr-1 space-y-4 flex-1 flex-col justify-end custom-scrollbar">
              {messages.map((m, idx) => (
                <MessageBubble
                  key={idx}
                  message={m}
                  onSourceClick={(file, pg) => {
                    setCurrentPdf({ file, page: pg != null ? Number(pg) : undefined });
                  }}
                />
              ))}
              <div id="chat-bottom" />
            </div>

            <ChatInput
              value={question}
              onValueChange={setQuestion}
              onSend={send}
              loading={loading}
            />
          </div>
        </div>
      </main>
    </div>
  );
}
