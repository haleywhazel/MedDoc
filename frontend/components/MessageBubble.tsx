import React from "react";
import { Message } from "../types";
import LoadingDots from "./LoadingDots";

interface Props {
  message: Message;
  onSourceClick?: (file: string, page?: number | null) => void;
}

const MessageBubble: React.FC<Props> = ({ message, onSourceClick }) => {
  const isUser = message.sender === "user";

  return (
    <div
      className={`flex ${isUser ? "justify-end" : "justify-start"} animate-fade-in`}
    >
      <div
        className={`flex gap-3 max-w-[85%] ${isUser ? "flex-row-reverse" : "flex-row"}`}
      >
        {/* Avatar */}
        <div
          className={`flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center shadow-md ${
            isUser
              ? "bg-gradient-to-br from-slate-600 to-slate-700"
              : "bg-gradient-to-br from-blue-600 to-indigo-600"
          }`}
        >
          {isUser ? (
            <svg
              className="w-5 h-5 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
          ) : (
            <svg
              className="w-5 h-5 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
              />
            </svg>
          )}
        </div>

        {/* Message content */}
        <div className="flex flex-col gap-2">
          <div
            className={`rounded-2xl px-4 py-3 shadow-md ${
              isUser
                ? "bg-gradient-to-br from-slate-700 to-slate-800 text-white rounded-tr-sm"
                : "bg-white text-slate-800 border border-slate-200 rounded-tl-sm"
            }`}
          >
            {message.loading ? (
              <LoadingDots />
            ) : message.words ? (
              <div className="whitespace-pre-wrap text-sm leading-relaxed">
                {message.words.map((w, i) => (
                  <span
                    key={i}
                    className={`inline-block ${i === message.words!.length - 1 ? "animate-fade-in" : ""}`}
                  >
                    {w}&nbsp;
                  </span>
                ))}
              </div>
            ) : (
              <div className="whitespace-pre-wrap text-sm leading-relaxed">
                {message.text}
              </div>
            )}

            {message.trace && (
              <pre className="mt-3 text-xs leading-tight text-slate-600 bg-slate-50 p-3 rounded-lg whitespace-pre-wrap break-words border border-slate-200">
                {JSON.stringify(message.trace, null, 2)}
              </pre>
            )}
          </div>

          {/* Sources */}
          {message.sources && message.sources.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-1">
              {message.sources.map((s, i) => (
                <button
                  key={i}
                  type="button"
                  className="group flex items-center gap-2 px-3 py-1.5 bg-blue-50 hover:bg-blue-100 border border-blue-200 hover:border-blue-300 rounded-lg text-xs font-medium text-blue-700 transition-all duration-200 shadow-sm hover:shadow"
                  onClick={(e) => {
                    e.stopPropagation();
                    onSourceClick?.(s.file, s.page);
                  }}
                >
                  <svg
                    className="w-3.5 h-3.5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                  <span className="truncate max-w-[150px]">{s.file}</span>
                  {s.page != null && (
                    <span className="px-1.5 py-0.5 bg-blue-200 rounded text-blue-800 font-semibold">
                      p.{s.page}
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
