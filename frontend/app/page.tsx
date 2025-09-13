"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import ChatInput from "../components/ChatInput";
import MessageBubble from "../components/MessageBubble";
import { Message, Source } from "../types";

const PDFViewer = dynamic(() => import("../components/PDFViewer"), { ssr: false });

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
          updated[placeholderIndex!] = { sender: "bot" as const, words: [] };
          return updated;
        });

        const words: string[] = (data.answer ?? "(no answer)").split(/\s+/);
        const sources = data.sources as Source[] | undefined;
        if (sources && sources.length > 0) {
          const s0 = sources[0];
          console.log("Opening PDF:", s0.file, "page", s0.page);
          setCurrentPdf({ file: s0.file, page: s0.page });
        }
        let i = 0;
        const interval = setInterval(() => {
          i += 1;
          setMessages((prev) => {
            const updated = [...prev];
            const msg = updated[placeholderIndex!];
            if (msg && msg.words) {
              msg.words = words.slice(0, i);
              if (i >= words.length) {
                if (sources) msg.sources = sources;
              }
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
    <div className="flex flex-col h-screen md:pl-[40%]">
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

      {/* Main chat area */}
      <main className="flex-1 flex flex-col items-center overflow-hidden bg-gray-100 py-2">
        <div className="flex flex-col w-full max-w-md flex-1 min-h-0 shadow bg-white">
          {/* Messages */}
          <div className="flex-1 min-h-0 overflow-y-scroll p-4 pr-1 space-y-4 flex-1 flex-col justify-end bg-white custom-scrollbar">
            {messages.map((m, idx) => (
              <MessageBubble key={idx} message={m} />
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
      </main>

      {/* PDF sidebar */}
      <div className="fixed left-0 top-0 bottom-0 w-[40%] max-w-lg z-10 hidden md:block">
        <PDFViewer
          fileUrl={currentPdf ? `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/pdf?file=${encodeURIComponent(currentPdf.file)}` : null}
          page={currentPdf?.page}
        />
      </div>
    </div>
  );
}
