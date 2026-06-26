// mirrors backend VerifiedFinding shape exactly (D-12, D-13)
export interface VerifiedFinding {
  finding: string;
  severity: "high" | "medium" | "low";
  source_chunk_id: string;
  quote: string;
  verified: boolean;
  abs_start: number | null;
  abs_end: number | null;
}

export interface UploadResponse {
  doc_id: string;
  full_text: string;
}

export interface AnalyzeResponse {
  findings: VerifiedFinding[];
}
