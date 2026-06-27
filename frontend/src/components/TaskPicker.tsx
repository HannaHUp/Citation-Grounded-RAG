import type { Perspective } from "../types";
import {
  ENABLED_WORKFLOWS,
  getTaskByProfileId,
  type EnabledWorkflow,
  type RunnableProfileId,
  type WorkflowTask,
} from "../workflows";

const PERSPECTIVES: Array<{ id: Perspective; label: string }> = [
  { id: "plaintiff", label: "Plaintiff" },
  { id: "defendant", label: "Defendant" },
  { id: "neutral", label: "Neutral" },
];

interface Props {
  workflow: EnabledWorkflow;
  detectedDocType: "contract" | "complaint" | null;
  selectedProfileId: RunnableProfileId;
  perspective: Perspective;
  analyzing: boolean;
  analyzeError: string | null;
  onSelectProfile: (profileId: RunnableProfileId) => void;
  onSelectPerspective: (perspective: Perspective) => void;
  onRunTask: () => void;
  onBack: () => void;
}

export default function TaskPicker({
  workflow,
  detectedDocType,
  selectedProfileId,
  perspective,
  analyzing,
  analyzeError,
  onSelectProfile,
  onSelectPerspective,
  onRunTask,
  onBack,
}: Props) {
  const visibleTasks = withSelectedOverride(workflow.tasks, selectedProfileId);
  const selectedTask = getTaskByProfileId(selectedProfileId);

  return (
    <section className="workflow-screen task-picker" aria-labelledby="task-picker-title">
      <div className="workflow-screen__inner">
        <button type="button" className="btn-secondary workflow-back" onClick={onBack}>
          Back to upload
        </button>
        <div className="document-status">
          <span>
            Detected document type:{" "}
            <strong>{detectedDocType === "complaint" ? "Complaint" : detectedDocType === "contract" ? "Contract" : "Unknown"}</strong>
          </span>
          <span>
            Selected analysis profile: <strong>{selectedTask.title}</strong>
          </span>
        </div>

        <h1 id="task-picker-title">Here are some things I can help you do</h1>
        <p className="workflow-step-copy">
          Pick a runnable analysis task for this document.
        </p>

        <div className="profile-override">
          <div>
            <span className="profile-override__label">Manual profile override</span>
            <p>Use this if automatic detection chose the wrong document family.</p>
          </div>
          <div className="profile-override__buttons" role="group" aria-label="Analysis profile override">
            {ENABLED_WORKFLOWS.map((item) => {
              const task = item.tasks[0];
              return (
                <button
                  key={task.profileId}
                  type="button"
                  className={`doc-type-btn${selectedProfileId === task.profileId ? " doc-type-btn--active" : ""}`}
                  aria-pressed={selectedProfileId === task.profileId}
                  onClick={() => onSelectProfile(task.profileId)}
                >
                  {item.id === "contract" ? "Contract" : "Complaint"}
                </button>
              );
            })}
          </div>
        </div>

        {workflow.requiresPerspective && (
          <div className="perspective-control">
            <span className="profile-override__label">Who do you represent?</span>
            <div className="perspective-control__buttons" role="group" aria-label="Complaint perspective">
              {PERSPECTIVES.map((option) => (
                <button
                  key={option.id}
                  type="button"
                  className={`perspective-btn${perspective === option.id ? " perspective-btn--active" : ""}`}
                  aria-pressed={perspective === option.id}
                  onClick={() => onSelectPerspective(option.id)}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="task-grid">
          {visibleTasks.map((task) => (
            <button
              key={task.id}
              type="button"
              className={`task-card${selectedProfileId === task.profileId ? " task-card--active" : ""}`}
              aria-pressed={selectedProfileId === task.profileId}
              onClick={() => onSelectProfile(task.profileId)}
            >
              <span className="task-card__title">{task.title}</span>
              <span className="task-card__description">{task.description}</span>
            </button>
          ))}
        </div>

        {analyzeError && <p className="error-msg">{analyzeError}</p>}

        <div className="task-picker__actions">
          <button type="button" className="btn-primary" onClick={onRunTask} disabled={analyzing}>
            {analyzing ? "Analyzing..." : `Run ${selectedTask.title}`}
          </button>
        </div>
      </div>
    </section>
  );
}

function withSelectedOverride(
  workflowTasks: WorkflowTask[],
  selectedProfileId: RunnableProfileId,
): WorkflowTask[] {
  const selectedTask = getTaskByProfileId(selectedProfileId);
  if (workflowTasks.some((task) => task.profileId === selectedProfileId)) {
    return workflowTasks;
  }
  return [...workflowTasks, selectedTask];
}
