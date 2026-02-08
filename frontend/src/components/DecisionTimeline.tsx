import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { DecisionVersion } from "@/data/decisions";
import { cn } from "@/lib/utils";

interface DecisionTimelineProps {
  versions: DecisionVersion[];
  latestVersion: string;
  decisionTitle?: string;
}


export function DecisionTimeline({
  versions,
  latestVersion,
  decisionTitle,
}: DecisionTimelineProps) {
  const [selectedVersionId, setSelectedVersionId] = useState<string>(latestVersion);
  const latestIndex = versions.findIndex((v) => v.version_id === latestVersion);
  const selectedVersion = versions.find((v) => v.version_id === selectedVersionId);

  // Reset selection when versions change (e.g., different decision selected)
  useEffect(() => {
    setSelectedVersionId(latestVersion);
  }, [latestVersion]);

  const formatFullDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const formatTime = (dateStr: string) => {
    return new Date(dateStr).toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
    });
  };


  return (
    <div className="space-y-6">
      {/* Timeline */}
      <div className="relative">
        {/* Timeline line - fades toward older versions */}
        <div className="absolute left-0 right-0 top-6 h-0.5">
          <div className="h-full w-full bg-gradient-to-r from-border/40 via-timeline-line/60 to-timeline-line" />
        </div>

        {/* Version nodes */}
        <div className="relative flex gap-6 overflow-x-auto pb-4">
          {versions.map((version, index) => {
            const isLatest = version.version_id === latestVersion;
            const isSelected = version.version_id === selectedVersionId;
            const isHistorical = index < latestIndex;
            const formattedDate = new Date(version.created_at).toLocaleDateString(
              "en-US",
              {
                month: "short",
                day: "numeric",
              }
            );
            const formattedTime = new Date(version.created_at).toLocaleTimeString(
              "en-US",
              {
                hour: "numeric",
                minute: "2-digit",
              }
            );

            return (
              <button
                key={version.version_id}
                type="button"
                onClick={() => setSelectedVersionId(version.version_id)}
                className={cn(
                  "flex flex-col items-center text-left transition-opacity focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded-lg",
                  isHistorical && !isSelected && "opacity-60",
                  isSelected && "opacity-100"
                )}
                style={{ minWidth: isLatest ? "260px" : "220px" }}
              >
                {/* Node */}
                <div
                  className={cn(
                    "relative z-10 flex items-center justify-center rounded-full border-[3px] bg-card text-sm font-semibold transition-all",
                    isSelected
                      ? "h-14 w-14 border-timeline-node-latest text-timeline-node-latest shadow-md"
                      : isLatest
                        ? "h-12 w-12 border-timeline-node-latest/50 text-timeline-node-latest/70"
                        : "h-10 w-10 border-border text-muted-foreground"
                  )}
                >
                  {version.version_id.toUpperCase()}
                </div>

                {/* Card */}
                <Card
                  className={cn(
                    "mt-4 w-full transition-all",
                    isSelected
                      ? "border-timeline-node-latest/40 bg-card shadow-sm ring-2 ring-timeline-node-latest/20"
                      : isLatest
                        ? "border-timeline-node-latest/20 bg-card/90"
                        : "border-border/60 bg-card/80"
                  )}
                >
                  <CardContent className="p-4">
                    {/* Latest badge */}
                    {isLatest && (
                      <Badge
                        variant="secondary"
                        className="mb-2 bg-accent/80 text-accent-foreground text-xs"
                      >
                        Current Truth
                      </Badge>
                    )}

                    {/* Content */}
                    <p
                      className={cn(
                        "text-sm leading-relaxed",
                        isSelected
                          ? "font-medium text-foreground"
                          : "text-muted-foreground"
                      )}
                    >
                      {version.content}
                    </p>

                    {/* Timestamp */}
                    <p
                      className={cn(
                        "mt-2 text-xs",
                        isSelected ? "text-muted-foreground" : "text-muted-foreground/70"
                      )}
                    >
                      {formattedDate} at {formattedTime}
                    </p>
                  </CardContent>
                </Card>
              </button>
            );
          })}
        </div>
      </div>


      {/* Version Summary Panel */}
      {selectedVersion && (
        <div className="rounded-lg border border-border bg-card p-6">
          {/* Header */}
          <div className="flex items-start justify-between gap-4 mb-6 pb-4 border-b border-border">
            <div>
              <div className="flex items-center gap-3 mb-1">
                <h3 className="text-lg font-semibold text-foreground">
                  Version {selectedVersion.version_id.toUpperCase()}
                </h3>
                {selectedVersion.version_id === latestVersion && (
                  <Badge variant="secondary" className="bg-accent/80 text-accent-foreground text-xs">
                    Current
                  </Badge>
                )}
              </div>
              <p className="text-sm text-muted-foreground">
                {formatFullDate(selectedVersion.created_at)} at {formatTime(selectedVersion.created_at)}
              </p>
            </div>
          </div>

          {/* Summary Sections */}
          <div className="space-y-6">
            {/* Decision Statement */}
            <div>
              <h4 className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-2">
                Decision
              </h4>
              <p className="text-sm text-foreground leading-relaxed">
                {selectedVersion.content}
              </p>
            </div>

            {/* What Changed */}
            <div>
              <h4 className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-2">
                What Changed
              </h4>
              <p className="text-sm text-foreground leading-relaxed">
                {selectedVersion.what_changed}
              </p>
            </div>

            {/* Why It Changed */}
            <div>
              <h4 className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-2">
                Why It Changed
              </h4>
              <p className="text-sm text-foreground leading-relaxed">
                {selectedVersion.why_changed}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
