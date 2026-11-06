export default function TypingIndicator() {
  return (
    <div className="message-row message-row-assistant">
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

      <div className="typing-card" aria-label="Assistant is typing">
        <span />
        <span />
        <span />
      </div>
    </div>
  );
}
