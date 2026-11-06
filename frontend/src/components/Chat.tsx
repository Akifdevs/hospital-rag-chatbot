import { useEffect, useRef, useState } from "react";

import ChatInput from "./ChatInput";
import MessageBubble from "./MessageBubble";
import TypingIndicator from "./TypingIndicator";

import { sendMessage as sendChatMessage } from "../services/api";

import type { ChatHistoryTurn, Message } from "../types/chat";

interface ChatProps {
  onClose: () => void;
}

// Matches the backend's ChatRequest.history max_length (see
// api.py). Only the most recent turns are sent - older turns
// stop being relevant for resolving a follow-up question, and
// keeping this short keeps the follow-up-rewriting LLM call
// fast and cheap.
const MAX_HISTORY_TURNS = 6;

// Mirrors the backend's greeting short-circuit (see api.py). Kept
// here so a bare "hi"/"hello" gets an instant reply without an API call.
const GREETING_WORDS =
  "hi+|hey+|hello+|hola|yo|sup|good\\s?morning|good\\s?afternoon|good\\s?evening|namaste|namaskar";
const GREETING_PATTERN = new RegExp(
  `^\\s*(?:${GREETING_WORDS})(?:\\s*[,!.\\s]\\s*(?:${GREETING_WORDS}))*[\\s!.?]*$`,
  "i"
);
const GREETING_REPLY =
  "Hey there! 👋 I'm your AI Assistant - ask me anything about the documentation and I'll help you find the answer.";

function isPureGreeting(question: string): boolean {
  return GREETING_PATTERN.test(question.trim());
}

/**
 * Pairs up the current message list into {question, answer}
 * turns to send as conversation history with the NEXT request.
 * Only complete user->assistant pairs are included (a trailing
 * unanswered user message, if any, is skipped).
 */
function buildHistoryTurns(messages: Message[]): ChatHistoryTurn[] {
  const turns: ChatHistoryTurn[] = [];
  let i = 0;

  while (i < messages.length - 1) {
    const current = messages[i];
    const next = messages[i + 1];

    if (current.role === "user" && next.role === "assistant") {
      turns.push({ question: current.content, answer: next.content });
      i += 2;
    } else {
      i += 1;
    }
  }

  return turns.slice(-MAX_HISTORY_TURNS);
}

// sessionStorage keys.
// sessionStorage persists across page reloads and across
// opening/closing this widget within the SAME browser tab,
// but is automatically cleared when the tab/browser is closed.
// That gives the exact behaviour we want: history survives while
// the user stays on the site, but disappears once they leave.
const MESSAGES_STORAGE_KEY = "rag_chat_messages";

function loadStoredMessages(): Message[] {
  try {
    const raw = sessionStorage.getItem(MESSAGES_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export default function Chat({ onClose }: ChatProps) {
  const [messages, setMessages] = useState<Message[]>(loadStoredMessages);
  const [isLoading, setIsLoading] = useState(false);

  // Persist messages to sessionStorage whenever they change.
  useEffect(() => {
    try {
      sessionStorage.setItem(MESSAGES_STORAGE_KEY, JSON.stringify(messages));
    } catch (e) {
      console.error("Failed to persist chat history:", e);
    }
  }, [messages]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto‑scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isLoading]);

  // Minimize just hides the panel - messages stay in sessionStorage
  // and reappear next time the widget is opened.
  function handleMinimize() {
    onClose();
  }

  // Close wipes the conversation: clear the in-memory messages AND
  // the persisted copy in sessionStorage, then hide the panel. Next
  // open starts from a blank slate.
  function handleCloseAndClear() {
    setMessages([]);
    try {
      sessionStorage.removeItem(MESSAGES_STORAGE_KEY);
    } catch (e) {
      console.error("Failed to clear chat history:", e);
    }
    onClose();
  }

  async function sendMessage(question: string) {
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: question,
    };

    // Greetings get an instant canned reply - no document needed,
    // no API call.
    if (isPureGreeting(question)) {
      const greetingReply: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: GREETING_REPLY,
      };
      setMessages((current) => [...current, userMessage, greetingReply]);
      return;
    }

    // Snapshot the history BEFORE adding the new user message,
    // so we send only prior turns, not the question being asked.
    const historyForRequest = buildHistoryTurns(messages);
    setMessages((current) => [...current, userMessage]);
    setIsLoading(true);
    try {
      const data = await sendChatMessage(
        question,
        historyForRequest
      );
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content:
          data.answer ||
          "Hmm, I couldn't find a clear answer to that. Could you try rephrasing your question, or ask about something else I can help with?",
      };
      setMessages((current) => [...current, assistantMessage]);
    } catch (error) {
      console.error("Chat request failed:", error);
      const errorMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "Sorry, I'm having trouble connecting right now. Please try again in a moment.",
      };
      setMessages((current) => [...current, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className="chat-widget" aria-label="AI Assistant">
      {/* HEADER */}
      <header className="chat-header">
        <div className="chat-header-info">
          <div className="chat-brand-mark" aria-hidden="true">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
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
          <div className="chat-header-text">
            <h2>AI Assistant</h2>
            <span className="chat-status">
              <span className="chat-status-dot" aria-hidden="true" />
              Online, ready to help
            </span>
          </div>
        </div>
        <div className="chat-header-actions">
          <button
            type="button"
            className="chat-header-btn chat-minimize"
            onClick={handleMinimize}
            aria-label="Minimize chat (keeps history)"
            title="Minimize"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M5 12h14" />
            </svg>
          </button>
          <button
            type="button"
            className="chat-header-btn chat-close"
            onClick={handleCloseAndClear}
            aria-label="Close chat and erase history"
            title="Close and erase history"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M18 6 6 18" />
              <path d="m6 6 12 12" />
            </svg>
          </button>
        </div>
      </header>

      {/* MESSAGES */}
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="chat-welcome">
            <div className="chat-welcome-mark" aria-hidden="true">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
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
            <h3>Hi, I'm your AI Assistant!</h3>
            <p>Ask me anything about the documentation and I'll help you find the answer.</p>
          </div>
        ) : (
          messages.map((message) => <MessageBubble key={message.id} message={message} />)
        )}
        {isLoading && <TypingIndicator />}
        <div ref={messagesEndRef} />
      </div>

      {/* INPUT */}
      <ChatInput
        onSend={sendMessage}
        disabled={isLoading}
        placeholder="Type your message..."
      />
    </section>
  );
}