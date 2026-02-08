import { apiGet } from "@/lib/api/client";
import type { Project } from "@/contexts/ProjectContext";

export async function fetchProjects(): Promise<Project[]> {
  return apiGet<Project[]>("/projects");
}
