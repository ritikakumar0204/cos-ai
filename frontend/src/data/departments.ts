export type DepartmentId = "product" | "infrastructure" | "engineering" | "finance" | "operations";

export interface Department {
  id: DepartmentId;
  name: string;
  shortName: string;
  colorClass: string;
  bgClass: string;
  borderClass: string;
}

export const departments: Record<DepartmentId, Department> = {
  product: {
    id: "product",
    name: "Product",
    shortName: "PRD",
    colorClass: "text-violet-600 dark:text-violet-400",
    bgClass: "bg-violet-50 dark:bg-violet-950/30",
    borderClass: "border-violet-200 dark:border-violet-800",
  },
  infrastructure: {
    id: "infrastructure",
    name: "Infrastructure",
    shortName: "INF",
    colorClass: "text-sky-600 dark:text-sky-400",
    bgClass: "bg-sky-50 dark:bg-sky-950/30",
    borderClass: "border-sky-200 dark:border-sky-800",
  },
  engineering: {
    id: "engineering",
    name: "Engineering",
    shortName: "ENG",
    colorClass: "text-emerald-600 dark:text-emerald-400",
    bgClass: "bg-emerald-50 dark:bg-emerald-950/30",
    borderClass: "border-emerald-200 dark:border-emerald-800",
  },
  finance: {
    id: "finance",
    name: "Finance",
    shortName: "FIN",
    colorClass: "text-amber-600 dark:text-amber-400",
    bgClass: "bg-amber-50 dark:bg-amber-950/30",
    borderClass: "border-amber-200 dark:border-amber-800",
  },
  operations: {
    id: "operations",
    name: "Operations",
    shortName: "OPS",
    colorClass: "text-rose-600 dark:text-rose-400",
    bgClass: "bg-rose-50 dark:bg-rose-950/30",
    borderClass: "border-rose-200 dark:border-rose-800",
  },
};

export const departmentList = Object.values(departments);

export function getDepartment(id: DepartmentId): Department {
  return departments[id];
}

export function getDepartmentByName(name: string): Department | undefined {
  const normalizedName = name.toLowerCase().replace(/\s+/g, "");
  return departmentList.find(
    (d) => d.id === normalizedName || d.name.toLowerCase() === name.toLowerCase()
  );
}
