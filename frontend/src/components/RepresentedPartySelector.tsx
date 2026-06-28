import type { ExtractedParty } from "../types";

interface Props {
  parties: ExtractedParty[];
  selectedPartyIds: string[];
  onToggle: (partyId: string) => void;
}

export default function RepresentedPartySelector({ parties, selectedPartyIds, onToggle }: Props) {
  return (
    <section className="workspace-section">
      <div className="workspace-section__heading">
        <h2>What party do you represent?</h2>
      </div>
      {parties.length === 0 ? (
        <p className="limited-mode">
          Party extraction for arbitrary uploads requires LLM mode. Use the demo complaint to see fixture-backed parties.
        </p>
      ) : (
        <div className="party-chip-grid">
          {parties.map((party) => {
            const selected = selectedPartyIds.includes(party.id);
            return (
              <label key={party.id} className={`party-chip${selected ? " party-chip--selected" : ""}`}>
                <input
                  type="checkbox"
                  checked={selected}
                  onChange={() => onToggle(party.id)}
                />
                <span>{party.name}</span>
                <small>{party.role} · {party.type}</small>
              </label>
            );
          })}
        </div>
      )}
    </section>
  );
}
