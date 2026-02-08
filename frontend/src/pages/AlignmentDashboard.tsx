import { useEffect, useState } from "react";
import { fetchAlignment, type AlignmentData } from "@/data/alignment";
import { AlignmentStatus } from "@/components/AlignmentStatus";
import { useProject } from "@/contexts/ProjectContext";
import { Target } from "lucide-react";

export default function AlignmentDashboard() {
  const { selectedProject } = useProject();
  const [alignmentData, setAlignmentData] = useState<AlignmentData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    let active = true;
    setLoading(true);

    fetchAlignment(selectedProject.project_id)
      .then((response) => {
        if (!active) {
          return;
        }
        setAlignmentData(response);
      })
      .catch((error) => {
        console.error("Error loading alignment:", error);
        if (active) {
          setAlignmentData(null);
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [selectedProject.project_id]);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="relative">
        <div className="flex items-center gap-4 mb-2">
          <div className="relative">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 shadow-lg shadow-blue-500/30">
              <Target className="h-5 w-5 text-white" />
            </div>
            <div className="absolute inset-0 blur-lg bg-cyan-400/30" />
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-blue-100">
            Alignment Dashboard
          </h1>
        </div>
        <p className="mt-1 text-blue-300/70">
          Department alignment status for{" "}
          <span className="font-medium text-cyan-300">
            {selectedProject.project_name}
          </span>
          . Review which teams are synchronized with the current truth.
        </p>
      </div>

      {/* Alignment Status */}
      {alignmentData ? (
        <AlignmentStatus data={alignmentData} projectId={selectedProject.project_id} />
      ) : (
        <div className="relative">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500/20 to-cyan-500/20 rounded-2xl blur" />
          <div className="relative rounded-xl border border-blue-500/30 bg-[#0d1225] p-8 text-center backdrop-blur-sm">
            <p className="text-sm text-blue-300/70">
              {loading ? "Loading alignment data..." : "No alignment data found for this project."}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
