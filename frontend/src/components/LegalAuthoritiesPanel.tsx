import { useState } from "react";
import type { LegalAuthority } from "../types";
import VerifiedBadge from "./VerifiedBadge";

type AuthorityTab = LegalAuthority["source_type"];

const TABS: Array<{ id: AuthorityTab; label: string }> = [
  { id: "case", label: "Cases" },
  { id: "statute", label: "Stat. & Reg." },
  { id: "secondary", label: "Secondary" },
];

interface Props {
  authorities: LegalAuthority[];
}

export default function LegalAuthoritiesPanel({ authorities }: Props) {
  const [activeTab, setActiveTab] = useState<AuthorityTab>("case");
  const visible = authorities.filter((authority) => authority.source_type === activeTab);

  if (authorities.length === 0) {
    return <p className="findings-empty">No authorities returned. Ingest the local corpus or try another finding.</p>;
  }

  return (
    <div className="authorities">
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

      <div className="authority-list">
        {visible.length === 0 && (
          <p className="findings-empty">No {sourceLabel(activeTab).toLowerCase()} authorities matched this lookup.</p>
        )}
        {visible.map((authority) => (
          <article className="authority-card" key={authority.authority_id}>
            <div className="authority-card__topline">
              <span className={`authority-source authority-source--${authority.source_type}`}>
                {sourceLabel(authority.source_type)}
              </span>
              <span className="authority-relevance">{authority.relevance}% relevant</span>
            </div>
            <h2 className="authority-card__title">{authority.title}</h2>
            <VerifiedBadge verified={authority.verified} compact />
            <p className="authority-card__summary">{authority.summary}</p>
            <blockquote className="authority-card__quote">"{authority.quote}"</blockquote>
            <a className="authority-card__link" href={authority.url} target="_blank" rel="noreferrer">
              Source
            </a>
          </article>
        ))}
      </div>
    </div>
  );
}

function sourceLabel(sourceType: LegalAuthority["source_type"]): string {
  if (sourceType === "case") return "Case";
  if (sourceType === "statute") return "Stat. & Reg.";
  return "Secondary";
}
