import { apiGet, apiPost } from "@/lib/api/client";

export interface StakeholderRecord {
  stakeholder_id: string;
  name: string;
  department: string;
  role: string;
}

export interface StakeholderReportsResponse {
  project_id: string;
  manager: StakeholderRecord;
  reports: StakeholderRecord[];
}

export interface AcceptLatestDecisionResponse {
  project_id: string;
  accepted_by: StakeholderRecord;
  include_downstream: boolean;
  notified_stakeholders: StakeholderRecord[];
  latest_versions: Record<string, string>;
  acknowledged_by_decision: Record<string, string[]>;
  alignment_status: "aligned" | "drift_detected";
  out_of_sync_departments: string[];
  message: string;
}

export interface CosVoiceMessageResponse {
  project_id: string;
  stakeholder_id: string;
  source: string;
  message: string;
  timestamp: string | null;
}

export async function fetchStakeholderReports(
  projectId: string,
  stakeholderId: string
): Promise<StakeholderReportsResponse> {
  return apiGet<StakeholderReportsResponse>(`/projects/${projectId}/stakeholders/${stakeholderId}/reports`);
}

export async function acceptLatestDecisions(
  projectId: string,
  stakeholderId: string,
  includeDownstream = true
): Promise<AcceptLatestDecisionResponse> {
  return apiPost<AcceptLatestDecisionResponse>(
    `/projects/${projectId}/stakeholders/${stakeholderId}/accept-latest`,
    { include_downstream: includeDownstream }
  );
}

export async function saveCosVoiceMessage(
  projectId: string,
  stakeholderId: string,
  stakeholderName: string,
  transcript: string
): Promise<void> {
  await apiPost(
    `/projects/${projectId}/cos-voice-messages`,
    {
      target_stakeholder_id: stakeholderId,
      target_stakeholder_name: stakeholderName,
      transcript,
    }
  );
}

export async function fetchCosVoiceMessage(
  projectId: string,
  stakeholderId: string
): Promise<CosVoiceMessageResponse> {
  return apiGet<CosVoiceMessageResponse>(
    `/projects/${projectId}/stakeholders/${stakeholderId}/cos-voice-message`
  );
}
