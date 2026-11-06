import { useState } from "react";

import Chat from "./components/Chat";

import "./App.css";

function App() {
  const [isOpen, setIsOpen] = useState(false);
  const [hasOpened, setHasOpened] = useState(false);

  function toggleOpen() {
    setIsOpen((open) => !open);
    setHasOpened(true);
  }

  // While the chat panel is open, the launcher button is hidden
  // entirely (not just swapped to an X) so the panel can expand
  // down into the space the launcher used to occupy. Closing /
  // minimizing now happens from the buttons inside the panel's
  // own header instead.
  return (
    <>
      {isOpen ? (
        <Chat onClose={() => setIsOpen(false)} />
      ) : (
        <button
          type="button"
          className="chat-launcher"
          onClick={toggleOpen}
          aria-label="Open AI Assistant"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <rect x="5" y="9" width="14" height="11" rx="3" />
            <path d="M12 9V5" />
            <circle cx="12" cy="4" r="1" fill="currentColor" stroke="none" />
            <path d="M3 13v3" />
            <path d="M21 13v3" />
            <circle cx="9.5" cy="14.5" r="1.1" fill="currentColor" stroke="none" />
            <circle cx="14.5" cy="14.5" r="1.1" fill="currentColor" stroke="none" />
            <path d="M9.5 18h5" />
          </svg>
          {!hasOpened && <span className="chat-launcher-dot" aria-hidden="true" />}
        </button>
      )}
    </>
  );
}

export default App;