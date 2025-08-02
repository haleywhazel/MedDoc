"use client";

import { useState } from "react";

export default function Home() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const ask = async () => {
    if (!question.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const data = await res.json();
      setAnswer(data.answer);
    } catch (err) {
      console.error(err);
      setAnswer("Error contacting server");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex flex-col items-center mt-12 px-4">
      <h1 className="text-2xl font-bold mb-4">MedDoc HR Assistant</h1>
      <textarea
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask an HR question…"
        className="w-full max-w-2xl border rounded p-2"
        rows={4}
      />
      <button
        onClick={ask}
        className="mt-2 bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50"
        disabled={loading}
      >
        {loading ? "Thinking…" : "Ask"}
      </button>
      {answer && (
        <div className="mt-6 w-full max-w-2xl whitespace-pre-wrap border rounded p-4 bg-gray-50">
          {answer}
        </div>
      )}
    </main>
  );
}
