import { GitBranch, ChevronRight } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { DepartmentBadge } from "@/components/DepartmentBadge";
import { DecisionStatusBadge } from "@/components/DecisionStatusBadge";
import type { Decision } from "@/data/decisions";
import type { DepartmentId } from "@/data/departments";

interface DecisionListProps {
  decisions: Decision[];
  onSelect: (decision: Decision) => void;
}

export function DecisionList({ decisions, onSelect }: DecisionListProps) {
  return (
    <div className="space-y-4">
      {decisions.map((decision) => {
        const versionCount = decision.versions.length;

        // Get all unique departments across all versions
        const allDepartments = [
          ...new Set(
            decision.versions.flatMap((v) =>
              v.stakeholders.map((s) => s.department)
            )
          ),
        ] as DepartmentId[];

        return (
          <Card
            key={decision.decision_id}
            className="cursor-pointer transition-all hover:border-border hover:shadow-sm"
            onClick={() => onSelect(decision)}
          >
            <CardContent className="p-5">
              <div className="flex items-start justify-between gap-4">
                {/* Left content */}
                <div className="flex items-start gap-4 min-w-0 flex-1">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-secondary">
                    <GitBranch className="h-5 w-5 text-muted-foreground" />
                  </div>
                  
                  <div className="space-y-2 min-w-0 flex-1">
                    {/* Title + Status */}
                    <div className="flex items-center gap-3 flex-wrap">
                      <h3 className="font-medium text-foreground">
                        {decision.title}
                      </h3>
                      <DecisionStatusBadge status={decision.status} />
                    </div>
                    
                    {/* Description */}
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {decision.description}
                    </p>
                    
                    {/* Metadata */}
                    <div className="flex items-center gap-3 text-xs text-muted-foreground pt-1">
                      <span className="font-mono">{decision.decision_id}</span>
                      <span className="text-border">•</span>
                      <span>
                        {versionCount} version{versionCount !== 1 ? "s" : ""}
                      </span>
                    </div>
                    
                    {/* Departments involved */}
                    <div className="flex flex-wrap gap-1.5 pt-2">
                      {allDepartments.map((deptId) => (
                        <DepartmentBadge
                          key={deptId}
                          department={deptId}
                          variant="muted"
                          size="sm"
                        />
                      ))}
                    </div>
                  </div>
                </div>
                
                {/* Chevron */}
                <ChevronRight className="h-5 w-5 shrink-0 text-muted-foreground mt-2" />
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
