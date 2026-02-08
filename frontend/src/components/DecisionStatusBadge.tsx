import { cn } from "@/lib/utils";
import type { DecisionStatus } from "@/data/decisions";

interface DecisionStatusBadgeProps {
  status: DecisionStatus;
}

const statusConfig: Record<DecisionStatus, { label: string; className: string }> = {
  active: {
    label: "Active",
    className: "bg-aligned/10 text-aligned border-aligned/20",
  },
  drifting: {
    label: "Drifting",
    className: "bg-drift/10 text-drift border-drift/20",
  },
  superseded: {
    label: "Superseded",
    className: "bg-muted text-muted-foreground border-border",
  },
};

export function DecisionStatusBadge({ status }: DecisionStatusBadgeProps) {
  const config = statusConfig[status];

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium",
        config.className
      )}
    >
      {config.label}
    </span>
  );
}
