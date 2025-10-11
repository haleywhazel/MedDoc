"use client";
import React, { useRef } from "react";

interface Props {
  value: string;
  onValueChange: (v: string) => void;
  onSend: () => void;
  loading: boolean;
  maxRows?: number;
}

const ChatInput: React.FC<Props> = ({
  value,
  onValueChange,
  onSend,
  loading,
  maxRows = 4,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const lineHeight = 24;

  const autoResize = () => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    const maxHeight = lineHeight * maxRows;
    const newHeight = Math.min(ta.scrollHeight, maxHeight);
    ta.style.height = `${newHeight}px`;
    ta.style.overflowY = newHeight >= maxHeight ? "auto" : "hidden";
  };

  React.useEffect(() => {
    if (!value && textareaRef.current) {
      const ta = textareaRef.current;
      ta.style.height = `100%`;
      ta.style.overflowY = "hidden";
    }
  }, [value]);

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSend();
      }}
      className="relative"
    >
      <div className="flex gap-3 items-end p-4 bg-white rounded-2xl border-2 border-slate-200 shadow-lg hover:border-blue-300 focus-within:border-blue-400 focus-within:shadow-xl transition-all duration-200">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => {
            onValueChange(e.target.value);
            autoResize();
          }}
          rows={1}
          placeholder="Ask anything about your HR documents..."
          className="flex-1 rounded p-2 resize-none focus:outline-none custom-scrollbar text-slate-800 placeholder:text-slate-400 bg-transparent"
          style={{ maxHeight: `${maxRows * 24}px` }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              onSend();
            }
          }}
        />
        <button
          type="submit"
          disabled={loading || !value.trim()}
          className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-6 py-2.5 rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-md hover:shadow-lg flex items-center gap-2 whitespace-nowrap"
        >
          {loading ? (
            <>
              <svg
                className="animate-spin h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Thinking...
            </>
          ) : (
            <>
              <span>Ask</span>
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M14 5l7 7m0 0l-7 7m7-7H3"
                />
              </svg>
            </>
          )}
        </button>
      </div>
      <p className="text-xs text-slate-500 mt-2 px-1">
        Press{" "}
        <kbd className="px-1.5 py-0.5 bg-slate-100 border border-slate-300 rounded text-slate-700 font-mono">
          Enter
        </kbd>{" "}
        to send,{" "}
        <kbd className="px-1.5 py-0.5 bg-slate-100 border border-slate-300 rounded text-slate-700 font-mono">
          Shift + Enter
        </kbd>{" "}
        for new line
      </p>
    </form>
  );
};

export default ChatInput;
