import { apiGet } from "@/lib/api/client";
import type { DepartmentId } from "./departments";
import type { StakeholderRole, StakeholderStatus } from "./decisions";

export type DepartmentAlignmentStatus = "aligned" | "drifting" | "awaiting_update";
export type AuthorityRole = "lead" | "manager" | "senior_ic" | "ic";

export interface DepartmentStakeholder {
  id: string;
  name: string;
  role: StakeholderRole;
  authority: AuthorityRole;
  status: StakeholderStatus;
  lastVersionReferenced: string;
}

export interface DepartmentAlignment {
  department_id: DepartmentId;
  status: DepartmentAlignmentStatus;
  context?: string;
  stakeholders: DepartmentStakeholder[];
}

export interface AlignmentData {
  project_id: string;
  project_name: string;
  alignment_status: "aligned" | "drift_detected";
  out_of_sync_departments: string[];
  explanation: string;
  departments: DepartmentAlignment[];
  summary: string;
}

export const authorityLabels: Record<AuthorityRole, string> = {
  lead: "Lead",
  manager: "Manager",
  senior_ic: "Senior IC",
  ic: "IC",
};

export async function fetchAlignment(projectId: string): Promise<AlignmentData> {
  return apiGet<AlignmentData>(`/projects/${projectId}/alignment`);
}
