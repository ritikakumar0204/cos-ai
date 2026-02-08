import type { DepartmentId } from "./departments";
import type { StakeholderRole, StakeholderStatus } from "./mockDecisionEvolution";

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
  departments: DepartmentAlignment[];
  summary: string;
}

export const authorityLabels: Record<AuthorityRole, string> = {
  lead: "Lead",
  manager: "Manager",
  senior_ic: "Senior IC",
  ic: "IC",
};

export const mockAlignmentData: AlignmentData[] = [
  {
    project_id: "proj-1",
    project_name: "Analytics Platform",
    departments: [
      { 
        department_id: "product", 
        status: "drifting", 
        context: "Still referencing Postgres as the primary database.",
        stakeholders: [
          { id: "s1", name: "Maya Chen", role: "owner", authority: "lead", status: "out_of_sync", lastVersionReferenced: "V1" },
          { id: "s2", name: "Priya Sharma", role: "contributor", authority: "senior_ic", status: "aligned", lastVersionReferenced: "V3" },
        ],
      },
      { 
        department_id: "infrastructure", 
        status: "aligned",
        stakeholders: [
          { id: "s3", name: "Alex Rivera", role: "owner", authority: "manager", status: "aligned", lastVersionReferenced: "V3" },
          { id: "s4", name: "Marcus Webb", role: "contributor", authority: "senior_ic", status: "aligned", lastVersionReferenced: "V3" },
        ],
      },
      { 
        department_id: "engineering", 
        status: "aligned",
        stakeholders: [
          { id: "s5", name: "Jordan Lee", role: "contributor", authority: "lead", status: "aligned", lastVersionReferenced: "V3" },
          { id: "s6", name: "Sam Patel", role: "informed", authority: "ic", status: "aligned", lastVersionReferenced: "V3" },
        ],
      },
      { 
        department_id: "finance", 
        status: "aligned",
        stakeholders: [
          { id: "s7", name: "Taylor Kim", role: "contributor", authority: "manager", status: "aligned", lastVersionReferenced: "V3" },
        ],
      },
      { 
        department_id: "operations", 
        status: "awaiting_update", 
        context: "Has not acknowledged the hybrid database approach.",
        stakeholders: [
          { id: "s8", name: "Casey Morgan", role: "observer", authority: "senior_ic", status: "awaiting_update", lastVersionReferenced: "V2" },
          { id: "s9", name: "Riley Park", role: "informed", authority: "ic", status: "awaiting_update", lastVersionReferenced: "V2" },
        ],
      },
    ],
    summary: "Product is operating under the assumption that Postgres is the primary database, while Infrastructure and Finance have aligned on BigQuery with fallback. Operations is awaiting confirmation on the new approach.",
  },
  {
    project_id: "proj-2",
    project_name: "Customer Portal",
    departments: [
      { 
        department_id: "product", 
        status: "aligned",
        stakeholders: [
          { id: "s1", name: "Maya Chen", role: "owner", authority: "lead", status: "aligned", lastVersionReferenced: "V2" },
        ],
      },
      { 
        department_id: "infrastructure", 
        status: "aligned",
        stakeholders: [
          { id: "s3", name: "Alex Rivera", role: "contributor", authority: "manager", status: "aligned", lastVersionReferenced: "V2" },
        ],
      },
      { 
        department_id: "engineering", 
        status: "aligned",
        stakeholders: [
          { id: "s5", name: "Jordan Lee", role: "owner", authority: "lead", status: "aligned", lastVersionReferenced: "V2" },
          { id: "s6", name: "Drew Santos", role: "contributor", authority: "senior_ic", status: "aligned", lastVersionReferenced: "V2" },
        ],
      },
      { 
        department_id: "finance", 
        status: "aligned",
        stakeholders: [
          { id: "s7", name: "Taylor Kim", role: "observer", authority: "manager", status: "aligned", lastVersionReferenced: "V2" },
        ],
      },
      { 
        department_id: "operations", 
        status: "drifting", 
        context: "Has not acknowledged the new design system requirements.",
        stakeholders: [
          { id: "s8", name: "Riley Park", role: "affected", authority: "senior_ic", status: "out_of_sync", lastVersionReferenced: "V1" },
          { id: "s9", name: "Morgan West", role: "informed", authority: "ic", status: "awaiting_update", lastVersionReferenced: "V1" },
        ],
      },
    ],
    summary: "Operations has not yet acknowledged the new design system requirements for customer-facing pages. This may affect deployment timelines and support documentation.",
  },
  {
    project_id: "proj-3",
    project_name: "Internal Tools",
    departments: [
      { 
        department_id: "product", 
        status: "awaiting_update", 
        context: "Pending review of the monorepo migration impact.",
        stakeholders: [
          { id: "s1", name: "Maya Chen", role: "informed", authority: "lead", status: "awaiting_update", lastVersionReferenced: "V1" },
        ],
      },
      { 
        department_id: "infrastructure", 
        status: "aligned",
        stakeholders: [
          { id: "s3", name: "Alex Rivera", role: "owner", authority: "manager", status: "aligned", lastVersionReferenced: "V2" },
        ],
      },
      { 
        department_id: "engineering", 
        status: "aligned",
        stakeholders: [
          { id: "s5", name: "Jordan Lee", role: "owner", authority: "lead", status: "aligned", lastVersionReferenced: "V2" },
          { id: "s6", name: "Sam Patel", role: "contributor", authority: "ic", status: "aligned", lastVersionReferenced: "V2" },
        ],
      },
      { 
        department_id: "finance", 
        status: "aligned",
        stakeholders: [
          { id: "s10", name: "Jamie Quinn", role: "observer", authority: "senior_ic", status: "aligned", lastVersionReferenced: "V2" },
        ],
      },
      { 
        department_id: "operations", 
        status: "drifting", 
        context: "Still using deprecated deploy scripts.",
        stakeholders: [
          { id: "s8", name: "Riley Park", role: "contributor", authority: "manager", status: "out_of_sync", lastVersionReferenced: "V1" },
          { id: "s9", name: "Casey Morgan", role: "affected", authority: "ic", status: "out_of_sync", lastVersionReferenced: "V1" },
        ],
      },
    ],
    summary: "Operations is still using deprecated deploy scripts that are not compatible with the new standardized CI pipelines. Product is awaiting review of migration impact.",
  },
];

export function getAlignmentByProject(projectId: string): AlignmentData | undefined {
  return mockAlignmentData.find((p) => p.project_id === projectId);
}
