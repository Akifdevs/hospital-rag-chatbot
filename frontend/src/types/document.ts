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
