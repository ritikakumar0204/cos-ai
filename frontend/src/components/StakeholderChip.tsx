import { cn } from "@/lib/utils";
import { getDepartment, type DepartmentId } from "@/data/departments";
import type { StakeholderRole, StakeholderStatus } from "@/data/mockDecisionEvolution";

interface StakeholderChipProps {
  name: string;
  department: DepartmentId;
  role: StakeholderRole;
  status: StakeholderStatus;
  isLatestVersion?: boolean;
}

const roleLabels: Record<StakeholderRole, string> = {
  owner: "Owner",
  contributor: "Contributor",
  informed: "Informed",
  affected: "Affected",
  observer: "Observer",
};

const statusConfig: Record<StakeholderStatus, { label: string; className: string }> = {
  aligned: {
    label: "Aligned",
    className: "border-aligned/30 bg-aligned/5",
  },
  out_of_sync: {
    label: "Out of Sync",
    className: "border-drift/30 bg-drift/5",
  },
  awaiting_update: {
    label: "Awaiting",
    className: "border-muted-foreground/30 bg-muted/50",
  },
};

export function StakeholderChip({
  name,
  department,
  role,
  status,
  isLatestVersion = false,
}: StakeholderChipProps) {
  const dept = getDepartment(department);
  const statusInfo = statusConfig[status];
  const isObserver = role === "observer";

  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 rounded-full border px-2.5 py-1 text-xs transition-all",
        statusInfo.className,
        isObserver && "opacity-60"
      )}
    >
      {/* Department indicator */}
      <span
        className={cn(
          "inline-block h-2 w-2 rounded-full",
          dept.bgClass,
          dept.colorClass.replace("text-", "bg-").replace("dark:text-", "dark:bg-")
        )}
        style={{
          backgroundColor: "currentColor",
        }}
      >
        <span className={cn("sr-only", dept.colorClass)}>{dept.shortName}</span>
      </span>

      {/* Name */}
      <span className={cn(
        "font-medium",
        isLatestVersion ? "text-foreground" : "text-muted-foreground"
      )}>
        {name}
      </span>

      {/* Role */}
      <span className="text-muted-foreground/70">
        {roleLabels[role]}
      </span>

      {/* Status indicator for non-aligned */}
      {status !== "aligned" && (
        <span
          className={cn(
            "rounded px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide",
            status === "out_of_sync" && "bg-drift/10 text-drift",
            status === "awaiting_update" && "bg-muted text-muted-foreground"
          )}
        >
          {statusInfo.label}
        </span>
      )}
    </div>
  );
}
