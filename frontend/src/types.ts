// mirrors backend VerifiedFinding shape exactly (D-12, D-13)
export interface VerifiedFinding {
  finding: string;
  severity: "high" | "medium" | "low";
  source_chunk_id: string;
  quote: string;
  verified: boolean;
  abs_start: number | null;
  abs_end: number | null;
  source_page: number | null;
}

export type Perspective = "plaintiff" | "defendant" | "neutral";

export type WorkflowId = "complaint" | "contract";

export type WorkflowStep = "workflow" | "upload" | "tasks" | "output";

export interface UploadResponse {
  doc_id: string;
  full_text: string;
  detected_doc_type: "contract" | "complaint";
  profile_id: string;
}

export interface AnalyzeResponse {
  findings: VerifiedFinding[];
}

export interface LegalAuthority {
  authority_id: string;
  title: string;
  source_type: "case" | "statute" | "secondary" | "admin" | "similar_case";
  summary: string;
  relevance: number;
  quote: string;
  verified: boolean;
  url: string;
  metadata?: Record<string, string>;
}

export interface AuthoritiesResponse {
  authorities: LegalAuthority[];
}

export interface WorkflowTask {
  id: string;
  title: string;
  description: string;
  category: string;
  enabled: boolean;
  fixture_supported: boolean;
}

export interface ExtractedParty {
  id: string;
  name: string;
  role: string;
  type: string;
  selected_by_default: boolean;
}

export interface ComplaintWorkflowResponse {
  doc_id: string;
  document_name: string;
  full_text: string;
  workflow_id: string;
  detected_doc_type: string;
  detected_summary: string;
  fixture_available: boolean;
  tasks: WorkflowTask[];
  parties: ExtractedParty[];
}

export interface ReportCitation {
  id: string;
  label: string;
  source_doc_name: string;
  page: number;
  quote: string;
  abs_start: number | null;
  abs_end: number | null;
}

export interface ReportBlock {
  type: "paragraph" | "ordered_list" | "bulleted_list" | "callout" | "table_ref";
  text?: string | null;
  items?: string[];
  citation_ids?: string[];
  table_id?: string | null;
}

export interface ReportSection {
  id: string;
  heading: string;
  blocks: ReportBlock[];
}

export interface ReportTable {
  id: string;
  title: string;
  columns: string[];
  rows: Record<string, string | string[]>[];
}

export interface AnalysisReport {
  id: string;
  title: string;
  subtitle: string;
  sections: ReportSection[];
  tables: ReportTable[];
  citations: ReportCitation[];
  primary_task_ids: string[];
  represented_party_ids: string[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  report: AnalysisReport | null;
  citations: ReportCitation[];
  created_at: string;
}

export interface ChatThread {
  thread_id: string;
  doc_id: string;
  selected_task_ids: string[];
  represented_party_ids: string[];
  messages: ChatMessage[];
}
