import type { DepartmentId } from "./departments";
import { apiGet } from "@/lib/api/client";

export type StakeholderRole = "owner" | "contributor" | "informed" | "affected" | "observer";
export type StakeholderStatus = "aligned" | "out_of_sync" | "awaiting_update";
export type DecisionStatus = "active" | "drifting" | "superseded";

export interface Stakeholder {
  id: string;
  name: string;
  department: DepartmentId;
  role: StakeholderRole;
  status: StakeholderStatus;
}

export interface DecisionVersion {
  version_id: string;
  content: string;
  created_at: string;
  what_changed: string;
  why_changed: string;
  stakeholders: Stakeholder[];
}

export interface Decision {
  decision_id: string;
  title: string;
  description: string;
  status: DecisionStatus;
  versions: DecisionVersion[];
  latest_version: string;
  insight?: string;
}

export interface ProjectDecisionsResponse {
  project_id: string;
  decisions: Decision[];
}

export async function fetchDecisions(
  projectId: string
): Promise<ProjectDecisionsResponse> {
  return apiGet<ProjectDecisionsResponse>(`/projects/${projectId}/decisions`);
}
