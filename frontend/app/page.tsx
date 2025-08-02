"use client";

import { useEffect, useState } from "react";
import ChatInput from "../components/ChatInput";
import MessageBubble from "../components/MessageBubble";
import { Message } from "../types";

export default function Home() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [debugMode, setDebugMode] = useState(true);
  const [showTrace, setShowTrace] = useState(false);

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
      const endpoint = debugMode ? "/api/chat/debug" : "/api/chat";
      const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}${endpoint}`, {
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
        let i = 0;
        const interval = setInterval(() => {
          i += 1;
          setMessages((prev) => {
            const updated = [...prev];
            const msg = updated[placeholderIndex!];
            if (msg && msg.words) {
              msg.words = words.slice(0, i);
              if (i >= words.length) msg.trace = showTrace ? data.trace : undefined;
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
                msgFinal.trace = showTrace ? data.trace : undefined;
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
              checked={debugMode}
              onChange={(e) => setDebugMode(e.target.checked)}
              className="accent-blue-600"
            />
            Debug
          </label>
          <label className="flex items-center gap-1 text-sm select-none">
            <input
              type="checkbox"
              checked={showTrace}
              onChange={(e) => setShowTrace(e.target.checked)}
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
              <MessageBubble key={idx} message={m} showTrace={showTrace} />
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
    </div>
  );
}
