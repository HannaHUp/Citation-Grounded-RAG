import type { WorkflowId } from "./types";

export type RunnableProfileId = "complaint_claims" | "contract_risk";

export interface WorkflowTask {
  id: RunnableProfileId;
  title: string;
  description: string;
  profileId: RunnableProfileId;
}

export interface EnabledWorkflow {
  id: WorkflowId;
  title: string;
  description: string;
  tags: string[];
  defaultProfileId: RunnableProfileId;
  requiresPerspective: boolean;
  tasks: WorkflowTask[];
  enabled: true;
}

export interface DisabledWorkflow {
  id: string;
  title: string;
  description: string;
  tags: string[];
  disabledReason: string;
  enabled: false;
}

export type WorkflowCatalogItem = EnabledWorkflow | DisabledWorkflow;

export const ENABLED_WORKFLOWS: EnabledWorkflow[] = [
  {
    id: "complaint",
    title: "Analyze a Complaint",
    description: "Extract claims, parties, facts, and litigation risks from a complaint.",
    tags: ["Litigation", "Document Analysis"],
    defaultProfileId: "complaint_claims",
    requiresPerspective: true,
    enabled: true,
    tasks: [
      {
        id: "complaint_claims",
        title: "Claims Analysis",
        description: "Extract legal claims, factual allegations, relief sought, and support in the pleading.",
        profileId: "complaint_claims",
      },
    ],
  },
  {
    id: "contract",
    title: "Analyze a Contract",
    description: "Review obligations, risk allocation, unusual terms, and client-hostile language.",
    tags: ["Transactional", "Document Analysis"],
    defaultProfileId: "contract_risk",
    requiresPerspective: false,
    enabled: true,
    tasks: [
      {
        id: "contract_risk",
        title: "Risk Review",
        description: "Surface legal exposure, obligations, ambiguous terms, and unfavorable provisions.",
        profileId: "contract_risk",
      },
    ],
  },
];

export const DISABLED_WORKFLOWS: DisabledWorkflow[] = [
  {
    id: "research_question",
    title: "Ask a Research Question",
    description: "Find answers in case law, legislation, and secondary sources.",
    tags: ["Research"],
    disabledReason: "Unavailable in this build",
    enabled: false,
  },
  {
    id: "document_tables",
    title: "Document Review with Tables",
    description: "Produce table reports summarizing documents and collections.",
    tags: ["Document Analysis"],
    disabledReason: "Unavailable in this build",
    enabled: false,
  },
  {
    id: "build_argument",
    title: "Build an Argument",
    description: "Draft argument structure from grounded claims and authorities.",
    tags: ["Research", "Litigation"],
    disabledReason: "Unavailable in this build",
    enabled: false,
  },
  {
    id: "compare_jurisdictions",
    title: "Compare Jurisdictions",
    description: "Compare legal rules across jurisdictions.",
    tags: ["Research"],
    disabledReason: "Unavailable in this build",
    enabled: false,
  },
];

export const WORKFLOWS: WorkflowCatalogItem[] = [
  ...ENABLED_WORKFLOWS,
  ...DISABLED_WORKFLOWS,
];

export const RUNNABLE_TASKS: WorkflowTask[] = ENABLED_WORKFLOWS.flatMap(
  (workflow) => workflow.tasks,
);

export function getWorkflow(id: WorkflowId): EnabledWorkflow {
  return ENABLED_WORKFLOWS.find((workflow) => workflow.id === id)!;
}

export function getTaskByProfileId(profileId: RunnableProfileId): WorkflowTask {
  return RUNNABLE_TASKS.find((task) => task.profileId === profileId)!;
}
