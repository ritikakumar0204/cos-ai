import { useEffect, useState } from "react";
import { fetchDecisions, type Decision } from "@/data/decisions";
import { DecisionTimeline } from "@/components/DecisionTimeline";
import { DecisionList } from "@/components/DecisionList";
import { useProject } from "@/contexts/ProjectContext";
import { ArrowLeft, GitBranch } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function DecisionEvolution() {
  const { selectedProject } = useProject();
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [selectedDecision, setSelectedDecision] = useState<Decision | null>(null);

  useEffect(() => {
    let isMounted = true;

    setSelectedDecision(null);

    fetchDecisions(selectedProject.project_id)
      .then((data) => {
        if (isMounted) {
          setDecisions(data.decisions ?? []);
        }
      })
      .catch((error) => {
        console.error("Error loading decisions:", error);
        if (isMounted) {
          setDecisions([]);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [selectedProject.project_id]);

  // If a decision is selected, show its timeline
  if (selectedDecision) {
    return (
      <div className="space-y-6">
        {/* Back Button + Header */}
        <div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSelectedDecision(null)}
            className="mb-2 -ml-2 text-blue-300/70 hover:text-cyan-300 hover:bg-blue-500/10"
          >
            <ArrowLeft className="mr-1 h-4 w-4" />
            All Decisions
          </Button>
          <div className="flex items-center gap-2 text-xs text-blue-300/50 mb-1">
            <span>Project: {selectedProject.project_name}</span>
            <span className="text-blue-500/30">•</span>
            <span className="font-mono">{selectedDecision.decision_id}</span>
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-blue-100">
            {selectedDecision.title}
          </h1>
          <p className="mt-1 text-sm text-blue-300/70">
            This view tracks how this decision evolved over time, capturing what changed and the reasoning behind each update.
          </p>
        </div>

        {/* Insight Callout */}
        {selectedDecision.insight && (
          <div className="relative">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500/10 to-cyan-500/10 rounded-xl blur" />
            <div className="relative rounded-lg border border-blue-500/20 bg-[#0d1225]/80 px-4 py-3 backdrop-blur-sm">
              <p className="text-sm text-blue-300/80 leading-relaxed">
                {selectedDecision.insight}
              </p>
            </div>
          </div>
        )}

        {/* Timeline Visualization */}
        <div className="relative">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500/20 to-cyan-500/20 rounded-2xl blur" />
          <div className="relative rounded-xl border border-blue-500/30 bg-[#0d1225] p-6 backdrop-blur-sm">
            <DecisionTimeline
              versions={selectedDecision.versions}
              latestVersion={selectedDecision.latest_version}
              decisionTitle={selectedDecision.title}
            />
          </div>
        </div>
      </div>
    );
  }

  // Default: show list of decisions
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="relative">
        <div className="flex items-center gap-4 mb-2">
          <div className="relative">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 shadow-lg shadow-blue-500/30">
              <GitBranch className="h-5 w-5 text-white" />
            </div>
            <div className="absolute inset-0 blur-lg bg-cyan-400/30" />
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-blue-100">
            Decision Evolution
          </h1>
        </div>
        <p className="mt-1 text-blue-300/70">
          Track how decisions evolved over time, capturing what changed and the reasoning behind each update.
        </p>
      </div>

      {/* Decision List */}
      {decisions.length > 0 ? (
        <DecisionList
          decisions={decisions}
          onSelect={setSelectedDecision}
        />
      ) : (
        <div className="relative">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500/20 to-cyan-500/20 rounded-2xl blur" />
          <div className="relative rounded-xl border border-blue-500/30 bg-[#0d1225] p-8 text-center backdrop-blur-sm">
            <p className="text-sm text-blue-300/70">
              No decisions found for this project.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
