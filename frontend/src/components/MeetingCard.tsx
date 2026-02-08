import { Calendar, MessageSquare, Users } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { DepartmentBadge } from "@/components/DepartmentBadge";
import type { Meeting } from "@/data/meetings";

interface MeetingCardProps {
  meeting: Meeting;
  onReview: (action: "approve" | "deny") => void;
  isSubmitting?: boolean;
}

export function MeetingCard({ meeting, onReview, isSubmitting = false }: MeetingCardProps) {
  const formattedDate = new Date(meeting.timestamp || meeting.date).toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
  });
  const isApproved = meeting.status === "approved";
  const isDenied = meeting.status === "denied";

  return (
    <Card className="transition-shadow hover:shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <h3 className="text-base font-semibold leading-tight">
            {meeting.title}
          </h3>
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Calendar className="h-3.5 w-3.5" />
            {formattedDate}
          </div>
        </div>

        <div className="flex items-center gap-2 pt-1">
          <Badge
            variant="secondary"
            className={
              isApproved
                ? "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"
                : isDenied
                ? "bg-rose-500/15 text-rose-300 border border-rose-500/30"
                : "bg-amber-500/15 text-amber-300 border border-amber-500/30"
            }
          >
            {meeting.status.toUpperCase()}
          </Badge>
          {isApproved && (
            <span className="text-xs text-emerald-300/80">Approval is locked</span>
          )}
        </div>
        
        {/* Departments Present */}
        {meeting.departments_present && meeting.departments_present.length > 0 && (
          <div className="flex items-center gap-2 pt-2">
            <Users className="h-3.5 w-3.5 text-muted-foreground" />
            <div className="flex flex-wrap gap-1">
              {meeting.departments_present.map((deptId) => (
                <DepartmentBadge
                  key={deptId}
                  department={deptId}
                  variant="muted"
                  size="sm"
                />
              ))}
            </div>
          </div>
        )}
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wider text-muted-foreground">
            <MessageSquare className="h-3.5 w-3.5" />
            Decisions Extracted
          </div>
          <ul className="space-y-2">
            {meeting.decisions_extracted.map((decision, index) => (
              <li
                key={index}
                className="rounded-md bg-secondary/50 px-3 py-2 text-sm text-secondary-foreground"
              >
                {decision}
              </li>
            ))}
          </ul>
        </div>

        <div className="mt-4 flex items-center gap-2">
          <Button
            type="button"
            size="sm"
            onClick={() => onReview("approve")}
            disabled={isSubmitting || isApproved}
            className="bg-emerald-600 hover:bg-emerald-500 text-white"
          >
            Approve
          </Button>
          <Button
            type="button"
            size="sm"
            variant="destructive"
            onClick={() => onReview("deny")}
            disabled={isSubmitting || isApproved}
          >
            Deny
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
