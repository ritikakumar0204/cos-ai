import type { DepartmentId } from "./departments";

export type StakeholderRole = "owner" | "contributor" | "informed" | "affected" | "observer";
export type StakeholderStatus = "aligned" | "out_of_sync" | "awaiting_update";

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

export type DecisionStatus = "active" | "drifting" | "superseded";

export interface Decision {
  decision_id: string;
  title: string;
  description: string;
  status: DecisionStatus;
  versions: DecisionVersion[];
  latest_version: string;
  insight?: string;
}

export interface ProjectDecisions {
  project_id: string;
  project_name: string;
  decisions: Decision[];
}

export const mockDecisionEvolutionData: ProjectDecisions[] = [
  {
    project_id: "proj-1",
    project_name: "Analytics Platform",
    decisions: [
      {
        decision_id: "dec-1",
        title: "Analytics Database Selection",
        description: "Primary database technology for storing and querying analytics data at scale.",
        status: "drifting",
        insight: "Product is still referencing an earlier version of this decision.",
        versions: [
          {
            version_id: "v1",
            content: "Use Postgres for analytics MVP",
            created_at: "2024-02-10T10:00:00Z",
            what_changed: "Initial decision established Postgres as the primary analytics database for the MVP phase.",
            why_changed: "Team needed a reliable, well-understood database to move quickly during initial development. Postgres offered familiarity and sufficient capability for early-stage analytics workloads.",
            stakeholders: [
              { id: "s1", name: "Maya Chen", department: "product", role: "owner", status: "out_of_sync" },
              { id: "s2", name: "Jordan Lee", department: "engineering", role: "contributor", status: "aligned" },
            ],
          },
          {
            version_id: "v2",
            content: "Switch to BigQuery for scale needs",
            created_at: "2024-02-11T15:30:00Z",
            what_changed: "Migrated from Postgres to BigQuery as the primary analytics database.",
            why_changed: "User growth projections exceeded Postgres capabilities. Infrastructure review identified BigQuery as better suited for the anticipated query volumes and data scale.",
            stakeholders: [
              { id: "s3", name: "Alex Rivera", department: "infrastructure", role: "owner", status: "aligned" },
              { id: "s4", name: "Sam Patel", department: "engineering", role: "informed", status: "aligned" },
            ],
          },
          {
            version_id: "v3",
            content: "Use BigQuery with Postgres as fallback for cost control",
            created_at: "2024-02-13T09:15:00Z",
            what_changed: "Adopted a hybrid approach: BigQuery for primary analytics with Postgres retained as a cost-effective fallback for smaller queries.",
            why_changed: "Finance raised concerns about projected BigQuery costs at scale. Retaining Postgres for lower-priority queries provides cost flexibility without sacrificing performance for critical workloads.",
            stakeholders: [
              { id: "s3", name: "Alex Rivera", department: "infrastructure", role: "owner", status: "aligned" },
              { id: "s5", name: "Taylor Kim", department: "finance", role: "contributor", status: "aligned" },
              { id: "s6", name: "Casey Morgan", department: "operations", role: "observer", status: "awaiting_update" },
            ],
          },
        ],
        latest_version: "v3",
      },
      {
        decision_id: "dec-2",
        title: "Mobile vs Desktop Priority",
        description: "Strategic platform priority for Q1 development and resource allocation.",
        status: "active",
        insight: "Engineering and Product have aligned on this direction.",
        versions: [
          {
            version_id: "v1",
            content: "Desktop-first approach for Q1",
            created_at: "2024-02-08T14:00:00Z",
            what_changed: "Established desktop as the primary development focus for Q1.",
            why_changed: "Initial user research indicated the majority of early adopters would access the platform via desktop browsers. This allowed the team to optimize for the primary use case first.",
            stakeholders: [
              { id: "s1", name: "Maya Chen", department: "product", role: "owner", status: "aligned" },
              { id: "s7", name: "Drew Santos", department: "engineering", role: "informed", status: "aligned" },
            ],
          },
          {
            version_id: "v2",
            content: "Prioritize mobile experience over desktop",
            created_at: "2024-02-12T11:00:00Z",
            what_changed: "Shifted primary development focus from desktop to mobile.",
            why_changed: "Updated analytics showed 68% of active users accessing via mobile devices. Customer feedback highlighted friction in the mobile experience as a key barrier to engagement.",
            stakeholders: [
              { id: "s1", name: "Maya Chen", department: "product", role: "owner", status: "aligned" },
              { id: "s2", name: "Jordan Lee", department: "engineering", role: "contributor", status: "aligned" },
              { id: "s8", name: "Riley Park", department: "operations", role: "affected", status: "aligned" },
            ],
          },
        ],
        latest_version: "v2",
      },
    ],
  },
  {
    project_id: "proj-2",
    project_name: "Customer Portal",
    decisions: [
      {
        decision_id: "dec-3",
        title: "Authentication Approach",
        description: "User authentication strategy for the customer portal application.",
        status: "active",
        insight: "All departments are aligned on using the existing auth service.",
        versions: [
          {
            version_id: "v1",
            content: "Use existing auth service",
            created_at: "2024-02-08T10:00:00Z",
            what_changed: "Adopted the company's existing authentication service for the customer portal.",
            why_changed: "Building a new auth system would delay launch by 6-8 weeks. The existing service meets security requirements and provides SSO capabilities needed for enterprise customers.",
            stakeholders: [
              { id: "s2", name: "Jordan Lee", department: "engineering", role: "owner", status: "aligned" },
              { id: "s3", name: "Alex Rivera", department: "infrastructure", role: "contributor", status: "aligned" },
              { id: "s9", name: "Morgan West", department: "operations", role: "observer", status: "aligned" },
            ],
          },
        ],
        latest_version: "v1",
      },
      {
        decision_id: "dec-4",
        title: "Design System Adoption",
        description: "Component library and design standards for customer-facing interfaces.",
        status: "drifting",
        insight: "Operations has not yet acknowledged the new design system requirements.",
        versions: [
          {
            version_id: "v1",
            content: "Use legacy component library",
            created_at: "2024-02-09T09:00:00Z",
            what_changed: "Continued use of the existing legacy component library for customer portal development.",
            why_changed: "Engineering bandwidth was limited, and the legacy library was already integrated. This avoided migration overhead during the initial build phase.",
            stakeholders: [
              { id: "s2", name: "Jordan Lee", department: "engineering", role: "owner", status: "aligned" },
              { id: "s8", name: "Riley Park", department: "operations", role: "informed", status: "out_of_sync" },
            ],
          },
          {
            version_id: "v2",
            content: "Adopt new design system for all customer-facing pages",
            created_at: "2024-02-13T16:00:00Z",
            what_changed: "Transitioned from legacy components to the new unified design system across all customer-facing pages.",
            why_changed: "Brand consistency audit revealed significant visual inconsistencies. The new design system provides accessibility improvements and reduces long-term maintenance burden.",
            stakeholders: [
              { id: "s1", name: "Maya Chen", department: "product", role: "owner", status: "aligned" },
              { id: "s2", name: "Jordan Lee", department: "engineering", role: "contributor", status: "aligned" },
              { id: "s8", name: "Riley Park", department: "operations", role: "affected", status: "awaiting_update" },
            ],
          },
        ],
        latest_version: "v2",
      },
    ],
  },
  {
    project_id: "proj-3",
    project_name: "Internal Tools",
    decisions: [
      {
        decision_id: "dec-5",
        title: "Monorepo Migration",
        description: "Consolidation of internal scripts and tooling into a unified repository.",
        status: "active",
        insight: "All departments are aligned on the migration approach.",
        versions: [
          {
            version_id: "v1",
            content: "Migrate scripts to monorepo",
            created_at: "2024-02-09T11:00:00Z",
            what_changed: "Consolidated all internal scripts and tooling into a single monorepo structure.",
            why_changed: "Scattered repositories made dependency management difficult and slowed cross-team collaboration. A monorepo simplifies versioning and enables shared tooling.",
            stakeholders: [
              { id: "s2", name: "Jordan Lee", department: "engineering", role: "owner", status: "aligned" },
              { id: "s3", name: "Alex Rivera", department: "infrastructure", role: "contributor", status: "aligned" },
              { id: "s10", name: "Jamie Quinn", department: "finance", role: "observer", status: "aligned" },
            ],
          },
        ],
        latest_version: "v1",
      },
      {
        decision_id: "dec-6",
        title: "CI Pipeline Standardization",
        description: "Unified continuous integration approach across all engineering teams.",
        status: "drifting",
        insight: "Operations is still using the deprecated deploy scripts.",
        versions: [
          {
            version_id: "v1",
            content: "Each team manages own CI pipelines",
            created_at: "2024-02-10T08:00:00Z",
            what_changed: "Maintained decentralized CI ownership with each team managing their own pipelines.",
            why_changed: "Teams had different deployment requirements and timelines. Allowing autonomy reduced coordination overhead during rapid iteration phases.",
            stakeholders: [
              { id: "s2", name: "Jordan Lee", department: "engineering", role: "owner", status: "aligned" },
              { id: "s8", name: "Riley Park", department: "operations", role: "contributor", status: "out_of_sync" },
            ],
          },
          {
            version_id: "v2",
            content: "Standardize CI pipelines across teams",
            created_at: "2024-02-15T14:30:00Z",
            what_changed: "Adopted a unified CI pipeline configuration shared across all engineering teams.",
            why_changed: "Inconsistent pipelines caused deployment failures and debugging complexity. Standardization reduces maintenance burden and improves reliability across projects.",
            stakeholders: [
              { id: "s3", name: "Alex Rivera", department: "infrastructure", role: "owner", status: "aligned" },
              { id: "s2", name: "Jordan Lee", department: "engineering", role: "contributor", status: "aligned" },
              { id: "s8", name: "Riley Park", department: "operations", role: "affected", status: "awaiting_update" },
            ],
          },
        ],
        latest_version: "v2",
      },
    ],
  },
];

export function getDecisionsByProject(projectId: string): ProjectDecisions | undefined {
  return mockDecisionEvolutionData.find((p) => p.project_id === projectId);
}
