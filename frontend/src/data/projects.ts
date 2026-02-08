export type Project = {
  project_id: string;
  project_name: string;
};

export const mockProjects: Project[] = [
  { project_id: "proj-1", project_name: "Analytics Platform" },
  { project_id: "proj-2", project_name: "Customer Portal" },
  { project_id: "proj-3", project_name: "Internal Tools" },
];

export function getProjects(): Project[] {
  return mockProjects;
}
