import type { DepartmentId } from "./departments";
import { apiGet, apiPost } from "@/lib/api/client";

export type MeetingStatus = "pending" | "approved" | "denied";

export interface Meeting {
  meeting_id: string;
  title: string;
  timestamp: string;
  date: string;
  summary: string;
  status: MeetingStatus;
  locked: boolean;
  decisions_extracted: string[];
  departments_present: DepartmentId[];
}

export interface ProjectMeetingsResponse {
  project_id: string;
  meetings: Meeting[];
}

export interface MeetingReviewResponse {
  project_id: string;
  meeting_id: string;
  status: MeetingStatus;
  locked: boolean;
  message: string;
}

export async function fetchMeetings(projectId: string): Promise<ProjectMeetingsResponse> {
  return apiGet<ProjectMeetingsResponse>(`/projects/${projectId}/meetings`);
}

export async function reviewMeeting(
  projectId: string,
  meetingId: string,
  action: "approve" | "deny"
): Promise<MeetingReviewResponse> {
  return apiPost<MeetingReviewResponse>(`/projects/${projectId}/meetings/${meetingId}/review`, {
    action,
  });
}
