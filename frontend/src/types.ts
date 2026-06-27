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
  source_type: "case" | "statute" | "secondary";
  summary: string;
  relevance: number;
  quote: string;
  verified: boolean;
  url: string;
}

export interface AuthoritiesResponse {
  authorities: LegalAuthority[];
}
