import { useState } from "react";
import { uploadFile, analyze, getAuthorities } from "./api";
import type { LegalAuthority, VerifiedFinding } from "./types";
import DocViewer from "./components/DocViewer";
import FindingsPanel from "./components/FindingsPanel";
import UploadZone from "./components/UploadZone";

interface Highlight {
  start: number;
  end: number;
}

export default function App() {
  const [fullText, setFullText] = useState<string | null>(null);
  const [docId, setDocId] = useState<string | null>(null);
  const [detectedDocType, setDetectedDocType] = useState<"contract" | "complaint" | null>(null);
  const [selectedProfileId, setSelectedProfileId] = useState<string>("contract_risk");
  const [findings, setFindings] = useState<VerifiedFinding[]>([]);
  const [authorities, setAuthorities] = useState<LegalAuthority[]>([]);
  const [highlight, setHighlight] = useState<Highlight | null>(null);
  const [activeFinding, setActiveFinding] = useState<VerifiedFinding | null>(null);

  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);
  const [loadingAuthoritiesFor, setLoadingAuthoritiesFor] = useState<string | null>(null);

  async function handleUpload(file: File) {
    setUploading(true);
    setUploadError(null);
    setDetectedDocType(null);
    try {
      const res = await uploadFile(file);
      setDocId(res.doc_id);
      setFullText(res.full_text);
      setDetectedDocType(res.detected_doc_type);
      setSelectedProfileId(res.profile_id);
      setFindings([]);
      setAuthorities([]);
      setHighlight(null);
      setActiveFinding(null);
      setAnalyzeError(null);
    } catch (err) {
      setUploadError(parseUploadError(err));
    } finally {
      setUploading(false);
    }
  }

  async function handleAnalyze() {
    if (!docId) return;
    setAnalyzing(true);
    setAnalyzeError(null);
    setHighlight(null);
    setActiveFinding(null);
    try {
      if (selectedProfileId === "contract_antitrust") {
        const res = await getAuthorities(docId, selectedProfileId);
        setAuthorities(res.authorities);
        setFindings([]);
      } else {
        const res = await analyze(docId, selectedProfileId);
        setFindings(res.findings);
        setAuthorities([]);
      }
    } catch (err) {
      setAnalyzeError(parseAnalyzeError(err));
    } finally {
      setAnalyzing(false);
    }
  }

  function handleFindingClick(f: VerifiedFinding) {
    if (f.verified && f.abs_start != null && f.abs_end != null) {
      setHighlight({ start: f.abs_start, end: f.abs_end });
      setActiveFinding(f);
    }
  }

  async function handleAuthorityLookup(finding: VerifiedFinding) {
    if (!docId) return;
    setLoadingAuthoritiesFor(finding.source_chunk_id);
    setAnalyzeError(null);
    setActiveFinding(finding);
    try {
      const res = await getAuthorities(docId, selectedProfileId, finding);
      setAuthorities(res.authorities);
    } catch (err) {
      setAnalyzeError(parseAnalyzeError(err));
    } finally {
      setLoadingAuthoritiesFor(null);
    }
  }

  return (
    <div className="app">
      <header className="app-header">Citation-Grounded RAG</header>
      <main className="app-body">
        <section className="doc-pane">
          {fullText == null ? (
            <UploadZone
              onUpload={handleUpload}
              uploading={uploading}
              error={uploadError}
            />
          ) : (
            <DocViewer text={fullText} highlight={highlight} />
          )}
        </section>
        <section className="findings-pane">
          <FindingsPanel
            findings={findings}
            authorities={authorities}
            activeFinding={activeFinding}
            hasDocument={fullText != null}
            analyzing={analyzing}
            loadingAuthoritiesFor={loadingAuthoritiesFor}
            analyzeError={analyzeError}
            onAnalyze={handleAnalyze}
            onFindingClick={handleFindingClick}
            onAuthorityLookup={handleAuthorityLookup}
            detectedDocType={detectedDocType}
            selectedProfileId={selectedProfileId}
            onSelectProfile={setSelectedProfileId}
          />
        </section>
      </main>
    </div>
  );
}

function parseUploadError(err: unknown): string {
  const raw = err instanceof Error ? err.message : String(err);
  if (/413|too large/i.test(raw)) return "File too large. Maximum size is 20 MB.";
  if (/400|unsupported|type/i.test(raw)) return "Unsupported file type. Please upload a PDF or DOCX.";
  return "Upload failed. Check your connection and try again.";
}

function parseAnalyzeError(err: unknown): string {
  const raw = err instanceof Error ? err.message : String(err);
  if (/404|not found/i.test(raw)) return "Session expired. Please re-upload your document.";
  return "Analysis failed. Try again or upload a different document.";
}
