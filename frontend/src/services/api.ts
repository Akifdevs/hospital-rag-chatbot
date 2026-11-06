import type {
  ChatHistoryTurn,
  ChatRequest,
  ChatResponse,
  VersionSnapshot,
} from "../types/chat";

import { ACTIVE_VERSION } from "../config";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

/**
 * Resolve the documentation version to query at request time.
 *
 * Priority:
 *   1. window.__RAG_WIDGET_VERSION__ — set by widget-entry.tsx when
 *      the embedding site adds a `version` attribute to the script tag:
 *        <script src="...widget.js" version="2"></script>
 *   2. ACTIVE_VERSION from config.ts — the hardcoded default used by
 *      the standalone build and any embed without a version attribute.
 *
 * This is intentionally a function (not a top-level const) to avoid the
 * ES-module evaluation ordering issue where widget-entry.tsx sets the
 * global AFTER api.ts's own top-level code has already run.
 */
function resolveVersion(): string | number {
  const widgetVersion = (window as any).__RAG_WIDGET_VERSION__;
  if (widgetVersion !== undefined && widgetVersion !== null && widgetVersion !== "") {
    return widgetVersion;
  }
  return ACTIVE_VERSION;
}

/** Fetch ready global document-set versions. */
export async function fetchVersions(): Promise<VersionSnapshot[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/versions`);
  if (!response.ok) {
    throw new Error(`Failed to fetch versions: HTTP ${response.status}`);
  }
  const data = await response.json();
  return data.versions;
}


export const DEFAULT_ROLE_STORAGE_KEY = "role";

/**
 * Read the user role from window.localStorage at request time.
 * If data-role-key was provided on the widget script tag, use that key;
 * otherwise use DEFAULT_ROLE_STORAGE_KEY ("role").
 * Wrapped in try/catch; returns null if missing or unreadable.
 */
function resolveUserRole(): string | null {
  try {
    const customKey = (window as any).__RAG_ROLE_KEY__;
    const key =
      typeof customKey === "string" && customKey.trim()
        ? customKey.trim()
        : DEFAULT_ROLE_STORAGE_KEY;
    const role = window.localStorage.getItem(key);
    if (role && typeof role === "string" && role.trim()) {
      return role.trim();
    }
  } catch {
    // Missing, disabled, or unreadable localStorage (e.g. strict iframe)
  }
  return null;
}

/**
 * Send a chat message.
 *
 * The version is resolved at call time via resolveVersion():
 *  - If the embedding site set a `version` attribute on the widget
 *    script tag, that version is used.
 *  - Otherwise falls back to ACTIVE_VERSION from config.ts.
 *
 * See config.ts for instructions on bumping ACTIVE_VERSION after a
 * new version has been reviewed and confirmed.
 */
export async function sendMessage(
  query: string,
  history: ChatHistoryTurn[] = []
): Promise<ChatResponse> {
  // The role is read from localStorage at request time and sent in the
  // JSON payload (visible in the browser under Network > Payload).
  const role = resolveUserRole();

  const request: ChatRequest = {
    query,
    version: resolveVersion(),
    url: window.location.href,
    history,
    role: role ?? null,
  };

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (role) {
    headers["X-User-Role"] = role;
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/chat`, {
    method: "POST",
    headers,
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    if (response.status >= 400 && response.status < 500) {
      throw new Error(`Unable to send your message. Please refresh and try again. (Error ${response.status})`);
    }
    throw new Error(`API request failed: HTTP ${response.status}`);
  }

  return response.json();
}