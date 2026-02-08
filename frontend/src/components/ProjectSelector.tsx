import { FolderOpen } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useProject } from "@/contexts/ProjectContext";

export function ProjectSelector() {
  const { selectedProject, setSelectedProject, projects } = useProject();

  return (
    <Select
      value={selectedProject.project_id}
      onValueChange={(value) => {
        const project = projects.find((p) => p.project_id === value);
        if (project) setSelectedProject(project);
      }}
    >
      <SelectTrigger className="w-[220px] border-blue-500/30 bg-[#0d1225]/80 text-blue-100 hover:border-blue-500/50">
        <div className="flex items-center gap-2">
          <FolderOpen className="h-4 w-4 text-cyan-400" />
          <SelectValue placeholder="Select project" />
        </div>
      </SelectTrigger>
      <SelectContent>
        {projects.map((project) => (
          <SelectItem key={project.project_id} value={project.project_id}>
            {project.project_name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
