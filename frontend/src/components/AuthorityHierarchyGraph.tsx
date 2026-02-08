import { CheckCircle2, AlertCircle, Clock } from "lucide-react";
import type { DepartmentStakeholder, AuthorityRole } from "@/data/mockAlignment";
import { authorityLabels } from "@/data/mockAlignment";
import type { StakeholderStatus } from "@/data/mockDecisionEvolution";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

interface AuthorityHierarchyGraphProps {
  stakeholders: DepartmentStakeholder[];
}

const authorityOrder: AuthorityRole[] = ["lead", "manager", "senior_ic", "ic"];

const stakeholderStatusConfig: Record<StakeholderStatus, { label: string; className: string; bgClassName: string }> = {
  aligned: {
    label: "Aligned",
    className: "text-emerald-400",
    bgClassName: "border-emerald-500/30 bg-slate-800/80",
  },
  out_of_sync: {
    label: "Out of Sync",
    className: "text-orange-400",
    bgClassName: "border-orange-500/30 bg-slate-800/80",
  },
  awaiting_update: {
    label: "Awaiting",
    className: "text-blue-300",
    bgClassName: "border-blue-500/30 bg-slate-800/80",
  },
};

const roleLabels: Record<string, string> = {
  owner: "Owner",
  contributor: "Contributor",
  informed: "Informed",
  affected: "Affected",
  observer: "Observer",
};

function generateAuthorityInsight(stakeholders: DepartmentStakeholder[]): string {
  // Group by authority level
  const grouped = authorityOrder.reduce((acc, authority) => {
    acc[authority] = stakeholders.filter(s => s.authority === authority);
    return acc;
  }, {} as Record<AuthorityRole, DepartmentStakeholder[]>);

  const activeLevels = authorityOrder.filter(level => grouped[level].length > 0);
  
  // Analyze drift patterns
  const outOfSync = stakeholders.filter(s => s.status === "out_of_sync");
  const awaiting = stakeholders.filter(s => s.status === "awaiting_update");
  const aligned = stakeholders.filter(s => s.status === "aligned");
  
  // Check if all aligned
  if (outOfSync.length === 0 && awaiting.length === 0) {
    return "All stakeholders across the authority chain are aligned with the current decision. No action is required at this time.";
  }

  // Find highest authority level with drift
  const highestDriftLevel = activeLevels.find(level => 
    grouped[level].some(s => s.status === "out_of_sync" || s.status === "awaiting_update")
  );

  // Find if lower levels are aligned while higher levels have drift
  const driftAtTop = highestDriftLevel === activeLevels[0];
  const alignedBelow = activeLevels.slice(1).some(level =>
    grouped[level].some(s => s.status === "aligned")
  );

  // Generate contextual insight
  if (driftAtTop && alignedBelow) {
    const topPerson = grouped[highestDriftLevel!].find(s => s.status === "out_of_sync" || s.status === "awaiting_update");
    const topAuthority = authorityLabels[highestDriftLevel!];
    
    if (topPerson?.status === "out_of_sync") {
      return `The ${topAuthority} is still referencing an earlier version of this decision, while downstream contributors are aligned with the latest update. This indicates a top-level awareness gap that may affect strategic direction.`;
    } else {
      return `The ${topAuthority} is awaiting confirmation on the latest update, while downstream team members have already aligned. Resolution requires acknowledgment from leadership to formalize the current state.`;
    }
  }

  // Drift only at lower levels
  if (!driftAtTop && outOfSync.length > 0) {
    const driftLevels = activeLevels.filter(level =>
      grouped[level].some(s => s.status === "out_of_sync")
    );
    const lowestDriftLevel = driftLevels[driftLevels.length - 1];
    const levelLabel = authorityLabels[lowestDriftLevel];
    
    return `Leadership is aligned with the current decision, but ${levelLabel}-level stakeholders remain out of sync. This may indicate a communication gap in cascading updates through the authority chain.`;
  }

  // All awaiting
  if (outOfSync.length === 0 && awaiting.length > 0) {
    return "Stakeholders at multiple levels are awaiting confirmation on the latest update. The decision has been communicated but formal acknowledgment is pending across the authority chain.";
  }

  // Mixed drift across levels
  const outOfSyncNames = outOfSync.map(s => s.name).join(" and ");
  return `${outOfSyncNames} ${outOfSync.length === 1 ? "is" : "are"} operating under a previous version of this decision. Ensuring alignment across authority levels will prevent execution inconsistencies.`;
}

export function AuthorityHierarchyGraph({ stakeholders }: AuthorityHierarchyGraphProps) {
  // Group stakeholders by authority level
  const grouped = authorityOrder.reduce((acc, authority) => {
    acc[authority] = stakeholders.filter(s => s.authority === authority);
    return acc;
  }, {} as Record<AuthorityRole, DepartmentStakeholder[]>);

  // Filter to only levels that have stakeholders
  const activeLevels = authorityOrder.filter(level => grouped[level].length > 0);

  if (activeLevels.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground text-sm">
        No stakeholders in this department.
      </div>
    );
  }

  const insight = generateAuthorityInsight(stakeholders);

  return (
    <TooltipProvider delayDuration={200}>
      <div className="space-y-6">
        {/* Insight Panel */}
        <div className="rounded-md border border-blue-500/20 bg-[#0d1225]/80 px-4 py-3 backdrop-blur-sm">
          <p className="text-sm text-blue-100 leading-relaxed">
            {insight}
          </p>
        </div>

        {/* Tree structure */}
        <div className="flex flex-col items-center gap-0 py-4">
          {activeLevels.map((level, levelIndex) => {
            const levelStakeholders = grouped[level];
            const isLastLevel = levelIndex === activeLevels.length - 1;
            const hasNextLevel = !isLastLevel;

            return (
              <div key={level} className="flex flex-col items-center w-full">
                {/* Level label */}
                <div className="text-xs font-medium uppercase tracking-wider text-blue-300/50 mb-3">
                  {authorityLabels[level]}
                </div>

                {/* Stakeholder nodes at this level */}
                <div className="flex flex-wrap justify-center gap-4">
                  {levelStakeholders.map((stakeholder) => (
                    <StakeholderNode key={stakeholder.id} stakeholder={stakeholder} />
                  ))}
                </div>

                {/* Connector line to next level */}
                {hasNextLevel && (
                  <div className="flex flex-col items-center my-2">
                    <div className="w-px h-6 bg-blue-500/30" />
                    <div className="w-3 h-3 border-l border-b border-blue-500/30 rotate-[-45deg] -mt-1.5" />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </TooltipProvider>
  );
}

interface StakeholderNodeProps {
  stakeholder: DepartmentStakeholder;
}

function StakeholderNode({ stakeholder }: StakeholderNodeProps) {
  const statusInfo = stakeholderStatusConfig[stakeholder.status];
  const isObserver = stakeholder.role === "observer";

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div
          className={cn(
            "flex items-center gap-3 rounded-lg border px-4 py-3 transition-all cursor-default",
            "hover:shadow-sm hover:border-blue-400/40",
            statusInfo.bgClassName,
            isObserver && "opacity-70"
          )}
        >
          {/* Avatar */}
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-500/20 text-sm font-medium text-blue-200 shrink-0">
            {stakeholder.name.split(" ").map(n => n[0]).join("")}
          </div>

          {/* Info */}
          <div className="min-w-0">
            <p className="font-medium text-white text-sm">
              {stakeholder.name}
            </p>
            <p className="text-xs text-blue-300/70">
              {roleLabels[stakeholder.role]}
            </p>
          </div>

          {/* Status indicator */}
          <div className="flex items-center gap-1.5 ml-2 shrink-0">
            {stakeholder.status === "aligned" ? (
              <CheckCircle2 className={cn("h-4 w-4", statusInfo.className)} />
            ) : stakeholder.status === "out_of_sync" ? (
              <AlertCircle className={cn("h-4 w-4", statusInfo.className)} />
            ) : (
              <Clock className={cn("h-4 w-4", statusInfo.className)} />
            )}
          </div>
        </div>
      </TooltipTrigger>
      <TooltipContent side="bottom" className="max-w-xs p-0">
        <div className="p-3 space-y-2">
          {/* Name */}
          <div className="font-medium text-foreground">
            {stakeholder.name}
          </div>
          
          {/* Details grid */}
          <div className="space-y-1.5 text-sm">
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Authority</span>
              <span className="text-foreground font-medium">
                {authorityLabels[stakeholder.authority]}
              </span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Status</span>
              <span className={cn("font-medium", statusInfo.className)}>
                {statusInfo.label}
              </span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Last Version</span>
              <span className="text-foreground font-medium">
                {stakeholder.lastVersionReferenced}
              </span>
            </div>
          </div>
        </div>
      </TooltipContent>
    </Tooltip>
  );
}
