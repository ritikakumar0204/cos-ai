import { getDepartmentByName, type DepartmentId } from "@/data/departments";
import { cn } from "@/lib/utils";

interface DepartmentBadgeProps {
  department: string;
  variant?: "default" | "muted" | "minimal";
  size?: "sm" | "md";
  className?: string;
}

export function DepartmentBadge({
  department,
  variant = "default",
  size = "sm",
  className,
}: DepartmentBadgeProps) {
  const dept = getDepartmentByName(department);

  if (!dept) {
    return (
      <span
        className={cn(
          "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium",
          "border-border bg-muted text-muted-foreground",
          className
        )}
      >
        {department}
      </span>
    );
  }

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border font-medium",
        size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-sm",
        variant === "default" && [dept.bgClass, dept.borderClass, dept.colorClass],
        variant === "muted" && [
          "bg-muted/50",
          "border-border/60",
          dept.colorClass,
        ],
        variant === "minimal" && [
          "border-transparent bg-transparent",
          dept.colorClass,
        ],
        className
      )}
    >
      {dept.name}
    </span>
  );
}

interface DepartmentDotsProps {
  departments: string[];
  className?: string;
}

export function DepartmentDots({ departments, className }: DepartmentDotsProps) {
  const uniqueDepts = [...new Set(departments)];

  return (
    <div className={cn("flex items-center gap-1", className)}>
      {uniqueDepts.map((deptName) => {
        const dept = getDepartmentByName(deptName);
        if (!dept) return null;
        return (
          <span
            key={dept.id}
            className={cn(
              "h-2 w-2 rounded-full",
              dept.bgClass,
              "ring-1",
              dept.borderClass
            )}
            title={dept.name}
          />
        );
      })}
    </div>
  );
}
