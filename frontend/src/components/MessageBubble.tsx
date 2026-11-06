import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import type { Message } from "../types/chat";

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`message-row ${isUser ? "message-row-user" : "message-row-assistant"}`}>
      {!isUser && (
        <div className="message-avatar message-avatar-assistant" aria-hidden="true">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <rect x="5" y="9" width="14" height="11" rx="3" />
            <path d="M12 9V5" />
            <circle cx="12" cy="4" r="1" fill="currentColor" stroke="none" />
            <path d="M3 13v3" />
            <path d="M21 13v3" />
            <circle cx="9.5" cy="14.5" r="1.1" fill="currentColor" stroke="none" />
            <circle cx="14.5" cy="14.5" r="1.1" fill="currentColor" stroke="none" />
            <path d="M9.5 18h5" />
          </svg>
        </div>
      )}

      {isUser ? (
        <div className="message-bubble-user">{message.content}</div>
      ) : (
        <div className="message-card">
          <span className="message-card-tag">AI Assistant</span>
          <div className="message-card-body message-markdown">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
          </div>
        </div>
      )}

      {isUser && (
        <div className="message-avatar message-avatar-user" aria-hidden="true">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 21a8 8 0 0 0-16 0" />
            <circle cx="12" cy="7" r="4" />
          </svg>
        </div>
      )}
    </div>
  );
}