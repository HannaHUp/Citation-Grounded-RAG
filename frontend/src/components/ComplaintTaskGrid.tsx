import type { WorkflowTask } from "../types";

interface Props {
  tasks: WorkflowTask[];
  selectedTaskIds: string[];
  onToggle: (taskId: string) => void;
}

export default function ComplaintTaskGrid({ tasks, selectedTaskIds, onToggle }: Props) {
  return (
    <section className="workspace-section">
      <div className="workspace-section__heading">
        <h2>Here are some things I can help you do</h2>
      </div>
      <div className="complaint-task-grid">
        {tasks.map((task) => {
          const selected = selectedTaskIds.includes(task.id);
          return (
            <button
              key={task.id}
              type="button"
              className={[
                "complaint-task",
                selected ? "complaint-task--selected" : "",
                !task.enabled ? "complaint-task--disabled" : "",
              ].filter(Boolean).join(" ")}
              disabled={!task.enabled}
              onClick={() => onToggle(task.id)}
            >
              <span className="complaint-task__title">{task.title}</span>
              <span className="complaint-task__description">{task.description}</span>
              <span className={task.fixture_supported ? "status-pill status-pill--ready" : "status-pill"}>
                {task.fixture_supported ? "Fixture-backed" : "LLM mode"}
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
