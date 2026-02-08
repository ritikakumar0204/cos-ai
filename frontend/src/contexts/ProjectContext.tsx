import { createContext, useContext, useEffect, useMemo, useState, ReactNode } from "react";

import { fetchProjects } from "@/lib/api/projects";

export interface Project {
  project_id: string;
  project_name: string;
}

const fallbackProjects: Project[] = [
  { project_id: "proj-1", project_name: "Analytics Platform" },
  { project_id: "proj-2", project_name: "Customer Portal" },
  { project_id: "proj-3", project_name: "Internal Tools" },
];

interface ProjectContextValue {
  selectedProject: Project;
  setSelectedProject: (project: Project) => void;
  projects: Project[];
}

const ProjectContext = createContext<ProjectContextValue | undefined>(undefined);

export function ProjectProvider({ children }: { children: ReactNode }) {
  const [projects, setProjects] = useState<Project[]>(fallbackProjects);
  const [selectedProject, setSelectedProject] = useState<Project>(fallbackProjects[0]);

  useEffect(() => {
    let active = true;

    fetchProjects()
      .then((remoteProjects) => {
        if (!active || remoteProjects.length === 0) {
          return;
        }

        setProjects(remoteProjects);
        setSelectedProject((current) => {
          const matched = remoteProjects.find(
            (project) => project.project_id === current.project_id
          );
          return matched ?? remoteProjects[0];
        });
      })
      .catch(() => {
        // Keep fallback projects when backend is unavailable.
      });

    return () => {
      active = false;
    };
  }, []);

  const value = useMemo(
    () => ({ selectedProject, setSelectedProject, projects }),
    [selectedProject, projects]
  );

  return <ProjectContext.Provider value={value}>{children}</ProjectContext.Provider>;
}

export function useProject() {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error("useProject must be used within a ProjectProvider");
  }
  return context;
}
