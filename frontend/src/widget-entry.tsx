import { createRoot } from "react-dom/client";

import App from "./App";
import indexCss from "./index.css?inline";
import appCss from "./App.css?inline";

/**
 * Embeddable entry point. Built separately (see vite.widget.config.ts)
 * into a single dist/widget.js file that any external site can load
 * with:
 *
 *   <script src="https://your-ngrok-url/widget.js"></script>
 *
 * Optionally, the embedding site can pin a specific documentation
 * version by adding a `version` attribute to the script tag:
 *
 *   <script src="https://your-ngrok-url/widget.js" version="2"></script>
 *
 * No rebuild needed — changing the attribute and reloading the host
 * page is enough. If the attribute is absent or not a valid positive
 * integer, the widget falls back to ACTIVE_VERSION in config.ts.
 *
 * Two things this does differently from the standalone app
 * (src/main.tsx):
 *
 * 1. It derives the API base URL from the <script> tag's own src,
 *    so the widget always talks back to whichever server it was
 *    loaded from - no manual config needed on the host site.
 * 2. It renders inside a closed-off Shadow DOM so the widget's
 *    CSS (including the global resets in index.css) can never
 *    leak onto the host page, and the host page's CSS can never
 *    accidentally restyle the widget.
 */
(function initWidget() {
  const currentScript = document.currentScript as HTMLScriptElement | null;

  if (currentScript?.src) {
    try {
      // Cast to `any` since the Window type augmentation for
      // __RAG_API_BASE__ lives in services/api.ts; that file no
      // longer reads this value (see chat history for why), but
      // this line is kept harmless in case it's wired back up later.
      (window as any).__RAG_API_BASE__ = new URL(currentScript.src).origin;
    } catch {
      // Malformed script src - fall back to relative/localhost
      // resolution in services/api.ts.
    }
  }

  // Read optional `version` attribute from the script tag so the
  // embedding site can control which documentation version the widget
  // answers from without a rebuild:
  //   <script src="...widget.js" version="2"></script>
  if (currentScript) {
    const raw = currentScript.getAttribute("version");
    if (raw !== null) {
      const trimmed = raw.trim();
      if (/^\d+(\.\d+)?$/.test(trimmed)) {
        (window as any).__RAG_WIDGET_VERSION__ = trimmed;
      }
      // Invalid / non-positive value → leave __RAG_WIDGET_VERSION__
      // unset so api.ts falls back to ACTIVE_VERSION from config.ts.
    }

    const roleKey = currentScript.getAttribute("data-role-key");
    if (roleKey !== null && roleKey.trim()) {
      (window as any).__RAG_ROLE_KEY__ = roleKey.trim();
    }
  }

  const host = document.createElement("div");
  host.id = "rag-widget-host";
  document.body.appendChild(host);

  const shadowRoot = host.attachShadow({ mode: "open" });

  // :root doesn't apply inside a shadow tree - swap it for :host
  // so the design tokens (colors, fonts) still resolve.
  const style = document.createElement("style");
  style.textContent = `${indexCss.replace(/:root/g, ":host")}\n${appCss}`;
  shadowRoot.appendChild(style);

  const mountPoint = document.createElement("div");
  shadowRoot.appendChild(mountPoint);

  createRoot(mountPoint).render(<App />);
})();
