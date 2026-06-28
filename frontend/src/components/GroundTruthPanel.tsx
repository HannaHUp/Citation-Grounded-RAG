import { useMemo, useState } from "react";
import type { LegalAuthority } from "../types";

type AuthorityTab = "all" | "case" | "statute" | "admin" | "secondary";

const TABS: Array<{ id: AuthorityTab; label: string }> = [
  { id: "all", label: "All" },
  { id: "case", label: "Cases" },
  { id: "statute", label: "Stat. & Reg." },
  { id: "admin", label: "Admin. Decisions" },
  { id: "secondary", label: "Secondary" },
];

interface Props {
  authorities: LegalAuthority[];
  loading: boolean;
  error: string | null;
}

export default function GroundTruthPanel({ authorities, loading, error }: Props) {
  const [activeTab, setActiveTab] = useState<AuthorityTab>("all");
  const [query, setQuery] = useState("");
  const [closed, setClosed] = useState(false);

  const visible = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return authorities
      .filter((authority) => activeTab === "all" || authority.source_type === activeTab)
      .filter((authority) => {
        if (!normalized) return true;
        return [authority.title, authority.summary, authority.quote]
          .join(" ")
          .toLowerCase()
          .includes(normalized);
      })
      .sort((left, right) => right.relevance - left.relevance);
  }, [activeTab, authorities, query]);

  if (closed) {
    return (
      <aside className="ground-truth ground-truth--closed">
        <button className="btn-secondary" type="button" onClick={() => setClosed(false)}>Legal Authorities</button>
      </aside>
    );
  }

  return (
    <aside className="ground-truth">
      <div className="ground-truth__top">
        <h2>Legal Authorities</h2>
        <button className="icon-btn" type="button" aria-label="Close legal authorities" onClick={() => setClosed(true)}>×</button>
      </div>
      <div className="ground-truth__controls">
        <div className="authority-tabs" role="tablist" aria-label="Legal authority source types">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={activeTab === tab.id}
              className={`authority-tab${activeTab === tab.id ? " authority-tab--active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <input
          className="authority-search"
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search results"
        />
        <div className="ground-truth__meta">
          <span>{visible.length} results</span>
          <select aria-label="Sort authorities" value="relevance" onChange={() => undefined}>
            <option value="relevance">Most Relevant</option>
          </select>
          <button className="btn-secondary" type="button">Modify List</button>
        </div>
      </div>
      <div className="authority-list">
        {loading && <p className="findings-empty">Finding legal authorities...</p>}
        {error && <p className="error-msg">{error}</p>}
        {!loading && !error && visible.length === 0 && (
          <p className="findings-empty">No authorities matched this view.</p>
        )}
        {!loading && !error && visible.map((authority) => (
          <article className="authority-card" key={authority.authority_id}>
            <div className="authority-card__topline">
              <span className={`authority-source authority-source--${authority.source_type}`}>
                {sourceLabel(authority.source_type)}
              </span>
              <span className="authority-relevance">{authority.relevance}% relevant</span>
            </div>
            <h3 className="authority-card__title">{authority.title}</h3>
            <div className="authority-card__meta">
              <span>{authority.metadata?.court ?? authority.metadata?.jurisdiction ?? "External source"}</span>
              {authority.metadata?.treatment && <span>{authority.metadata.treatment}</span>}
            </div>
            <p className="authority-card__summary">{authority.summary}</p>
            <blockquote className="authority-card__quote">{authority.quote}</blockquote>
            <a className="authority-card__link" href={authority.url} target="_blank" rel="noreferrer">Source</a>
          </article>
        ))}
      </div>
    </aside>
  );
}

function sourceLabel(sourceType: LegalAuthority["source_type"]): string {
  if (sourceType === "case") return "Case";
  if (sourceType === "statute") return "Stat. & Reg.";
  if (sourceType === "admin") return "Admin. Decision";
  if (sourceType === "similar_case") return "Similar Matter";
  return "Secondary";
}
