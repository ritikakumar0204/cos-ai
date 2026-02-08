import { useState } from "react";
import { CheckCircle2, AlertCircle, Clock, ChevronDown, ArrowLeft } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { AlignmentData, DepartmentAlignmentStatus, DepartmentAlignment } from "@/data/alignment";
import { authorityLabels } from "@/data/alignment";
import { getDepartment } from "@/data/departments";
import { AuthorityHierarchyGraph } from "@/components/AuthorityHierarchyGraph";
import { AIBriefingPanel, type SuggestedCommunication } from "@/components/AIBriefingPanel";
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";
import { saveCosVoiceMessage } from "@/data/team";
import { toast } from "sonner";

interface AlignmentStatusProps {
  data: AlignmentData;
  projectId: string;
}

const statusConfig: Record<DepartmentAlignmentStatus, { 
  label: string; 
  icon: typeof CheckCircle2;
  cardClass: string;
  iconClass: string;
  badgeClass: string;
}> = {
  aligned: {
    label: "Aligned",
    icon: CheckCircle2,
    cardClass: "border-blue-500/30 bg-[#0d1225] hover:border-blue-500/50",
    iconClass: "text-emerald-400",
    badgeClass: "bg-emerald-500/20 text-emerald-400",
  },
  drifting: {
    label: "Drifting",
    icon: AlertCircle,
    cardClass: "border-blue-500/30 bg-[#0d1225] hover:border-blue-500/50",
    iconClass: "text-orange-400",
    badgeClass: "bg-orange-500/20 text-orange-400",
  },
  awaiting_update: {
    label: "Awaiting Update",
    icon: Clock,
    cardClass: "border-blue-500/30 bg-[#0d1225] hover:border-blue-500/50",
    iconClass: "text-blue-300",
    badgeClass: "bg-blue-500/20 text-blue-300",
  },
};

export function AlignmentStatus({ data, projectId }: AlignmentStatusProps) {
  const [expandedDepartment, setExpandedDepartment] = useState<string | null>(null);

  // Sort departments: drifting first, then awaiting, then aligned
  const sortedDepartments = [...data.departments].sort((a, b) => {
    const order: Record<DepartmentAlignmentStatus, number> = {
      drifting: 0,
      awaiting_update: 1,
      aligned: 2,
    };
    return order[a.status] - order[b.status];
  });

  const driftingCount = data.departments.filter(d => d.status === "drifting").length;
  const awaitingCount = data.departments.filter(d => d.status === "awaiting_update").length;
  const alignedCount = data.departments.filter(d => d.status === "aligned").length;

  const handleDepartmentClick = (deptId: string) => {
    setExpandedDepartment(expandedDepartment === deptId ? null : deptId);
  };

  // If a department is expanded, show the detail view
  if (expandedDepartment) {
    const deptAlignment = data.departments.find(d => d.department_id === expandedDepartment);
    if (deptAlignment) {
      return (
        <DepartmentDetailView 
          deptAlignment={deptAlignment} 
          projectId={projectId}
          onBack={() => setExpandedDepartment(null)} 
        />
      );
    }
  }

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="flex items-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          <span className="text-white font-medium">{alignedCount}</span>
          <span className="text-blue-300/70">Aligned</span>
        </div>
        {driftingCount > 0 && (
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-orange-400" />
            <span className="text-white font-medium">{driftingCount}</span>
            <span className="text-blue-300/70">Drifting</span>
          </div>
        )}
        {awaitingCount > 0 && (
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-blue-300" />
            <span className="text-white font-medium">{awaitingCount}</span>
            <span className="text-blue-300/70">Awaiting</span>
          </div>
        )}
      </div>

      {/* Department Cards */}
      <div className="space-y-3">
        {sortedDepartments.map((deptAlignment) => {
          const dept = getDepartment(deptAlignment.department_id);
          const config = statusConfig[deptAlignment.status];
          const StatusIcon = config.icon;
          const stakeholderCount = deptAlignment.stakeholders.length;

          return (
            <button
              key={deptAlignment.department_id}
              type="button"
              onClick={() => handleDepartmentClick(deptAlignment.department_id)}
              className="w-full text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded-lg"
            >
              <Card
                className={cn("transition-all cursor-pointer", config.cardClass)}
              >
                <CardContent className="flex items-start gap-4 p-4">
                  {/* Department Color Indicator */}
                  <div
                    className={cn(
                      "mt-0.5 flex h-10 w-10 items-center justify-center rounded-lg",
                      dept.bgClass
                    )}
                  >
                    <span className={cn("text-sm font-semibold", dept.colorClass)}>
                      {dept.shortName}
                    </span>
                  </div>

                  {/* Department Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3">
                      <h3 className="font-medium text-blue-100">
                        {dept.name}
                      </h3>
                      <span
                        className={cn(
                          "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium",
                          config.badgeClass
                        )}
                      >
                        <StatusIcon className="h-3 w-3" />
                        {config.label}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      {deptAlignment.context && (
                        <p className="text-sm text-blue-300/70">
                          {deptAlignment.context}
                        </p>
                      )}
                      {!deptAlignment.context && (
                        <p className="text-sm text-blue-300/70">
                          {stakeholderCount} stakeholder{stakeholderCount !== 1 ? "s" : ""}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Expand Indicator */}
                  <div className="flex items-center text-blue-300/50">
                    <ChevronDown className="h-4 w-4" />
                  </div>
                </CardContent>
              </Card>
            </button>
          );
        })}
      </div>

      {/* Context Summary */}
      <div className="rounded-lg border border-blue-500/20 bg-[#0d1225]/80 p-4 backdrop-blur-sm">
        <h4 className="text-xs font-medium uppercase tracking-wider text-blue-300/50 mb-2">
          Summary
        </h4>
        <p className="text-sm leading-relaxed text-blue-100">
          {data.summary}
        </p>
      </div>
    </div>
  );
}

interface DepartmentDetailViewProps {
  deptAlignment: DepartmentAlignment;
  projectId: string;
  onBack: () => void;
}

function generateBriefingSummary(deptAlignment: DepartmentAlignment): string {
  const dept = getDepartment(deptAlignment.department_id);
  const outOfSync = deptAlignment.stakeholders.filter(s => s.status === "out_of_sync");
  const awaiting = deptAlignment.stakeholders.filter(s => s.status === "awaiting_update");
  
  if (deptAlignment.status === "aligned") {
    return `${dept.name} is fully aligned with the current decision. All stakeholders are operating with the same understanding, and no communication gaps have been detected.`;
  }
  
  if (outOfSync.length > 0) {
    const names = outOfSync.map(s => s.name).join(" and ");
    const authorities = outOfSync.map(s => authorityLabels[s.authority]).join(" and ");
    return `${names} (${authorities}) in ${dept.name} ${outOfSync.length === 1 ? "is" : "are"} referencing an earlier version of this decision. A targeted update would bring ${dept.name} into alignment and prevent execution inconsistencies.`;
  }
  
  if (awaiting.length > 0) {
    const names = awaiting.map(s => s.name).join(" and ");
    return `${names} in ${dept.name} ${awaiting.length === 1 ? "has" : "have"} not yet acknowledged the latest update. A brief confirmation message would close the loop and formalize alignment.`;
  }
  
  return `${dept.name} requires attention to ensure alignment with the current decision.`;
}

function generateSuggestedCommunications(deptAlignment: DepartmentAlignment): SuggestedCommunication[] {
  const dept = getDepartment(deptAlignment.department_id);
  const outOfSync = deptAlignment.stakeholders.filter(s => s.status === "out_of_sync");
  const awaiting = deptAlignment.stakeholders.filter(s => s.status === "awaiting_update");
  
  const communications: SuggestedCommunication[] = [];
  
  // For out of sync stakeholders - suggest email with context
  outOfSync.forEach(stakeholder => {
    const authority = authorityLabels[stakeholder.authority];
    communications.push({
      channel: "email",
      recipient: stakeholder.name,
      preview: `Quick sync on the latest decision update — the current approach has evolved since we last discussed. Here's what changed and why it matters for ${dept.name}...`,
    });
  });
  
  // For awaiting stakeholders - suggest Slack for quick acknowledgment
  awaiting.forEach(stakeholder => {
    communications.push({
      channel: "slack",
      recipient: stakeholder.name,
      preview: `Hey ${stakeholder.name.split(" ")[0]}, just confirming you've seen the latest update on this decision. Let me know if you have any questions.`,
    });
  });
  
  return communications;
}

function DepartmentDetailView({ deptAlignment, projectId, onBack }: DepartmentDetailViewProps) {
  const { role } = useAuth();
  const dept = getDepartment(deptAlignment.department_id);
  const config = statusConfig[deptAlignment.status];
  const StatusIcon = config.icon;
  const [recordedContext, setRecordedContext] = useState<string>("");
  
  const briefingSummary = generateBriefingSummary(deptAlignment);
  const summaryWithContext = recordedContext
    ? `${briefingSummary} COS recorded context: ${recordedContext}`
    : briefingSummary;
  const suggestedCommunications = generateSuggestedCommunications(deptAlignment);
  const targetStakeholder =
    deptAlignment.stakeholders.find((stakeholder) => stakeholder.status === "out_of_sync")
    ?? deptAlignment.stakeholders.find((stakeholder) => stakeholder.status === "awaiting_update")
    ?? deptAlignment.stakeholders[0];

  return (
    <div className="space-y-6">
      {/* Back Button + Header */}
      <div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onBack}
          className="mb-3 -ml-2 text-blue-300/70 hover:text-cyan-300 hover:bg-blue-500/10"
        >
          <ArrowLeft className="mr-1 h-4 w-4" />
          All Departments
        </Button>
        
        <div className="flex items-center gap-4">
          <div
            className={cn(
              "flex h-12 w-12 items-center justify-center rounded-lg",
              dept.bgClass
            )}
          >
            <span className={cn("text-base font-semibold", dept.colorClass)}>
              {dept.shortName}
            </span>
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-semibold text-white">
                {dept.name}
              </h2>
              <span
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium",
                  config.badgeClass
                )}
              >
                <StatusIcon className="h-3 w-3" />
                {config.label}
              </span>
            </div>
            {deptAlignment.context && (
              <p className="mt-1 text-sm text-blue-300/70">
                {deptAlignment.context}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* AI Briefing Panel - only show for non-aligned departments */}
      {deptAlignment.status !== "aligned" && (
        <AIBriefingPanel
          summary={summaryWithContext}
          suggestedCommunications={suggestedCommunications}
          onRecordedMessage={
            role === "admin" && targetStakeholder
              ? async (message) => {
                  await saveCosVoiceMessage(
                    projectId,
                    targetStakeholder.id,
                    targetStakeholder.name,
                    message
                  );
                  setRecordedContext(message);
                  toast.success(`Saved COS voice message for ${targetStakeholder.name}.`);
                }
              : undefined
          }
        />
      )}

      {/* Authority Hierarchy Graph */}
      <div className="rounded-lg border border-blue-500/30 bg-[#0d1225] p-6 backdrop-blur-sm">
        <h3 className="text-xs font-medium uppercase tracking-wider text-blue-300/50 mb-4">
          Authority Structure
        </h3>
        <AuthorityHierarchyGraph stakeholders={deptAlignment.stakeholders} />
      </div>
    </div>
  );
}
