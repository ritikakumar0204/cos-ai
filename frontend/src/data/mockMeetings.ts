import type { DepartmentId } from "./departments";

export interface Meeting {
  meeting_id: string;
  title: string;
  date: string;
  decisions_extracted: string[];
  departments_present: DepartmentId[];
}

export interface ProjectMeetings {
  project_id: string;
  project_name: string;
  meetings: Meeting[];
}

export const mockMeetingsData: ProjectMeetings[] = [
  {
    project_id: "proj-1",
    project_name: "Analytics Platform",
    meetings: [
      {
        meeting_id: "m-1",
        title: "Analytics Planning",
        date: "2024-02-10",
        decisions_extracted: ["Use Postgres for analytics MVP"],
        departments_present: ["product", "engineering"],
      },
      {
        meeting_id: "m-2",
        title: "Infra Review",
        date: "2024-02-11",
        decisions_extracted: ["Switch to BigQuery for scale needs"],
        departments_present: ["infrastructure", "engineering"],
      },
      {
        meeting_id: "m-3",
        title: "Q1 Roadmap Sync",
        date: "2024-02-12",
        decisions_extracted: [
          "Prioritize mobile experience over desktop",
          "Delay API v2 launch to Q2",
        ],
        departments_present: ["product", "engineering", "operations"],
      },
      {
        meeting_id: "m-4",
        title: "Security Review",
        date: "2024-02-14",
        decisions_extracted: ["Implement SSO before public launch"],
        departments_present: ["infrastructure", "engineering", "operations"],
      },
    ],
  },
  {
    project_id: "proj-2",
    project_name: "Customer Portal",
    meetings: [
      {
        meeting_id: "m-5",
        title: "Portal Kickoff",
        date: "2024-02-08",
        decisions_extracted: [
          "Build portal with React + TypeScript",
          "Use existing auth service",
        ],
        departments_present: ["product", "engineering", "infrastructure"],
      },
      {
        meeting_id: "m-6",
        title: "UX Review",
        date: "2024-02-13",
        decisions_extracted: ["Adopt new design system for all customer-facing pages"],
        departments_present: ["product", "engineering"],
      },
    ],
  },
  {
    project_id: "proj-3",
    project_name: "Internal Tools",
    meetings: [
      {
        meeting_id: "m-7",
        title: "Tooling Standup",
        date: "2024-02-09",
        decisions_extracted: ["Migrate scripts to monorepo"],
        departments_present: ["engineering", "infrastructure"],
      },
      {
        meeting_id: "m-8",
        title: "DevOps Sync",
        date: "2024-02-15",
        decisions_extracted: [
          "Standardize CI pipelines across teams",
          "Deprecate legacy deploy scripts",
        ],
        departments_present: ["infrastructure", "engineering", "operations"],
      },
    ],
  },
];

export function getMeetingsByProject(projectId: string): ProjectMeetings | undefined {
  return mockMeetingsData.find((p) => p.project_id === projectId);
}
