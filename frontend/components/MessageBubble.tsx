import React from "react";
import { Message } from "../types";
import LoadingDots from "./LoadingDots";

interface Props {
  message: Message;
  showTrace: boolean;
}

const MessageBubble: React.FC<Props> = ({ message, showTrace }) => {
  const baseClasses =
    "rounded-xl p-3 max-w-s min-h-12 whitespace-pre-wrap text-sm md:text-base transform animate-fade-in animate-bubble-grow";
  const bubbleClasses =
    message.sender === "user"
      ? "bg-gray-300 text-gray-900"
      : "text-gray-900";

  return (
    <div className={`flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}>
      <div className={`${baseClasses} ${bubbleClasses}`}>
        {message.loading ? (
          <LoadingDots />
        ) : message.words ? (
          message.words.map((w, i) => (
            <span
              key={i}
              className="inline-block"
              style={{ animation: "fadeIn 0.2s ease forwards" }}
            >
              {w}&nbsp;
            </span>
          ))
        ) : (
          message.text
        )}
        {showTrace && message.trace && (
          <pre className="mt-2 text-[10px] leading-tight text-gray-600 bg-gray-100 p-1 rounded overflow-x-auto max-h-40">
            {JSON.stringify(message.trace, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;
