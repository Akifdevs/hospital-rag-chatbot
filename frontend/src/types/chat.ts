export type MessageRole =
  | "user"
  | "assistant";


export interface Message {
  id: string;
  role: MessageRole;
  content: string;
}


/**
 * One prior question/answer pair sent along with a new chat
 * request, so the backend can resolve follow-up questions
 * ("what about X?") into standalone queries. This mirrors the
 * backend's ChatHistoryTurn model.
 */
export interface ChatHistoryTurn {
  question: string;
  answer: string;
}


/**
 * Request sent to the FastAPI backend.
 */
export interface ChatRequest {
  query: string;
  version?: number | string;
  /** Full URL of the host page currently embedding the widget. */
  url: string;
  history: ChatHistoryTurn[];
  /** User role read by the widget from the browser's localStorage. */
  role?: string | null;
}

export interface VersionSnapshot {
  version_label: string;
  major_version: number;
  minor_version: number;
  status: string;
  document_count: number;
  version?: number | string;
}


/**
 * Response returned by:
 *
 * POST /api/v1/chat
 */
export interface ChatResponse {
  success: boolean;
  answer: string;
  error: string | null;
  request_id: string;
}

export interface DocumentSummary {
  id: number;
  document_number: string;
  name: string;
  description?: string;
}

export interface DocumentVersionResponse {
  id: number;
  version_number: number;
  file_name: string;
  status: string;
  is_latest: boolean;
  chunk_count: number;
}
