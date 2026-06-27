import type { WorkflowId } from "../types";
import type { WorkflowCatalogItem } from "../workflows";

interface Props {
  workflows: WorkflowCatalogItem[];
  onSelectWorkflow: (workflowId: WorkflowId) => void;
}

export default function WorkflowPicker({ workflows, onSelectWorkflow }: Props) {
  return (
    <section className="workflow-screen workflow-picker" aria-labelledby="workflow-picker-title">
      <div className="workflow-screen__inner">
        <h1 id="workflow-picker-title">What would you like to do?</h1>
        <div className="workflow-section-heading">
          <h2>Workflows</h2>
        </div>
        <div className="workflow-grid">
          {workflows.map((workflow) => (
            <button
              key={workflow.id}
              type="button"
              className={`workflow-card${workflow.enabled ? "" : " workflow-card--disabled"}`}
              disabled={!workflow.enabled}
              onClick={() => {
                if (workflow.enabled) onSelectWorkflow(workflow.id);
              }}
            >
              <span className="workflow-card__title">{workflow.title}</span>
              <span className="workflow-card__description">{workflow.description}</span>
              <span className="workflow-card__tags">
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
      </div>
    </section>
  );
}
