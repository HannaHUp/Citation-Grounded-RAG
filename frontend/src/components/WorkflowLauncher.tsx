import type { WorkflowId } from "../types";
import type { WorkflowCatalogItem } from "../workflows";

interface Props {
  workflows: WorkflowCatalogItem[];
  onSelectWorkflow: (workflowId: WorkflowId) => void;
}

export default function WorkflowLauncher({ workflows, onSelectWorkflow }: Props) {
  return (
    <main className="workflow-launcher" aria-labelledby="workflow-launcher-title">
      <section className="workflow-launcher__hero">
        <div className="workflow-launcher__mark" aria-hidden="true">⌄</div>
        <h1 id="workflow-launcher-title">What would you like to do?</h1>
        <div className="workflow-command">
          <textarea
            aria-label="Ask a question or describe what you would like to do"
            placeholder="Ask any question or say what you would like to do..."
          />
          <div className="workflow-command__bar">
            <button type="button" className="workflow-command__icon" aria-label="Add document">+</button>
            <span>United States (Federal)</span>
            <button type="button" className="workflow-command__send" aria-label="Start">→</button>
          </div>
        </div>
      </section>

      <section className="workflow-launcher__workflows" aria-labelledby="workflow-list-title">
        <div className="workflow-launcher__toolbar">
          <h2 id="workflow-list-title">Workflows</h2>
          <div className="workflow-launcher__filters">
            <select aria-label="Workflow filter" defaultValue="featured">
              <option value="featured">Featured</option>
            </select>
            <input type="search" aria-label="Find workflows" placeholder="Find" />
          </div>
        </div>

        <div className="workflow-launcher__grid">
          {workflows.map((workflow) => (
            <button
              key={workflow.id}
              type="button"
              className={`workflow-launcher-card${workflow.enabled ? "" : " workflow-launcher-card--disabled"}`}
              disabled={!workflow.enabled}
              onClick={() => {
                if (workflow.enabled) onSelectWorkflow(workflow.id);
              }}
            >
              <span className="workflow-launcher-card__pin" aria-hidden="true">◆</span>
              <span className="workflow-launcher-card__title">{workflow.title}</span>
              <span className="workflow-launcher-card__description">{workflow.description}</span>
              <span className="workflow-launcher-card__tags">
                {workflow.tags.map((tag) => (
                  <span className="workflow-tag" key={tag}>{tag}</span>
                ))}
              </span>
              {!workflow.enabled && (
                <span className="workflow-card__status">{workflow.disabledReason}</span>
              )}
            </button>
          ))}
        </div>
      </section>
    </main>
  );
}
