"use client";

import { FormEvent, useEffect, useRef, useState } from "react";

interface Message {
  sender: "user" | "bot";
  text?: string;
  words?: string[];
  loading?: boolean;
  trace?: Record<string, unknown>;
}

export default function Home() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [debugMode, setDebugMode] = useState(true);
  const [showTrace, setShowTrace] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const MAX_ROWS = 4;

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Adjust textarea height
  const autoResize = () => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    const lineHeight = 24; // approx 1.5rem with tailwind text-sm
    const maxHeight = lineHeight * MAX_ROWS;
    ta.style.height = `${Math.min(ta.scrollHeight, maxHeight)}px`;
  };

  const send = async (e?: FormEvent) => {
    e?.preventDefault();
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
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
    setLoading(true);

    try {
      const endpoint = debugMode ? "/api/chat/debug" : "/api/chat";
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}${endpoint}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: trimmed }),
        }
      );
      const data = await res.json();
      await new Promise((r) => setTimeout(r, 500)); // artificial delay

      // Replace loading bubble with animated bubble
      if (placeholderIndex !== null) {
        setMessages((prev) => {
          const updated = [...prev];
          if (updated[placeholderIndex!]) {
            updated[placeholderIndex!] = { sender: "bot", words: [] };
          }
          return updated;
        });

        const fullText: string = data.answer ?? "(no answer)";
        const words = fullText.split(/\s+/);
        const delay = 120; // 120ms per word

        let i = 0;
        const interval = setInterval(() => {
          i += 1;
          setMessages((prev) => {
            const updated = [...prev];
            const msg = updated[placeholderIndex!];
            if (msg && msg.sender === "bot" && msg.words) {
              msg.words = words.slice(0, i);
              if (i >= words.length) {
                msg.trace = showTrace ? data.trace : undefined;
              }
            }
            return updated;
          });
          if (i >= words.length) clearInterval(interval);
        }, delay);
      }
    } catch (err) {
      console.error(err);
      setMessages((prev) => {
        const updated = [...prev];
        if (placeholderIndex !== null && updated[placeholderIndex]) {
          updated[placeholderIndex] = { sender: "bot", text: "Error contacting server." };
        }
        return updated;
      });
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
          <label className="flex items-center gap-1 text-sm cursor-pointer select-none">
            <input
              type="checkbox"
              checked={debugMode}
              onChange={(e) => setDebugMode(e.target.checked)}
              className="accent-blue-600"
            />
            Debug
          </label>
          <label className="flex items-center gap-1 text-sm cursor-pointer select-none">
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
        <div className="flex flex-col w-full max-w-md flex-1 shadow bg-white">
          {/* Messages */}
          <div className="flex-1 min-h-0 overflow-y-auto p-4 space-y-4 flex flex-col justify-end bg-gray-50">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`rounded-lg p-3 max-w-s min-h-12 whitespace-pre-wrap text-sm md:text-base transform animate-fade-in animate-bubble-grow ${
                    msg.sender === "user" ? "bg-gray-300 text-gray-900" : "text-gray-900"
                  }`}
                >
                  {msg.loading ? (
                    <span className="loading-dots font-bold">
                      <span>.</span>
                      <span>.</span>
                      <span>.</span>
                    </span>
                  ) : msg.words ? (
                    msg.words.map((w, i) => (
                      <span key={i} className="inline-block" style={{ animation: "fadeIn 0.2s ease forwards" }}>
                        {w}&nbsp;
                      </span>
                    ))
                  ) : (
                    msg.text
                  )}
                  {showTrace && msg.trace && (
                    <pre className="mt-2 text-[10px] leading-tight text-gray-600 bg-gray-100 p-1 rounded overflow-x-auto max-h-40">
                      {JSON.stringify(msg.trace, null, 2)}
                    </pre>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form onSubmit={send} className="border-t p-3 bg-white flex gap-2 items-end">
            <textarea
              ref={textareaRef}
              value={question}
              onChange={(e) => {
                setQuestion(e.target.value);
                autoResize();
              }}
              rows={1}
              placeholder="Ask Ello anything…"
              className="flex-1 border rounded p-2 resize-none focus:outline-none transition-all"
              style={{ maxHeight: `${MAX_ROWS * 24}px` }}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send();
                }
              }}
            />
            <button
              type="submit"
              disabled={loading}
              className="bg-gray-700 text-white px-4 py-2 rounded disabled:opacity-50 h-fit"
            >
              {loading ? "…" : "Ask"}
            </button>
          </form>
        </div>
      </main>

      <style jsx global>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }
        @keyframes bubbleGrow {
          0% {
            transform: scale(0.8);
          }
          20% {
            transform: scale(0.8);
          }
          100% {
            transform: scale(1);
          }
        }
        .animate-bubble-grow {
          animation: bubbleGrow 0.15s ease-out forwards;
        }
        /* Loading dots */
        .loading-dots span {
          opacity: 0.4;
          animation: dotFade 0.5s linear infinite alternate;
          display: inline-block;
        }
        .loading-dots span:nth-child(2) {
          animation-delay: 0.1s;
        }
        .loading-dots span:nth-child(3) {
          animation-delay: 0.2s;
        }
        @keyframes dotFade {
          from {
            opacity: 0.4;
          }
          to {
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
}
