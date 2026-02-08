import { useEffect, useMemo, useRef, useState } from "react";
import { ArrowLeft, GitBranch, MessageSquare, User, Play, Pause } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";
import { useProject } from "@/contexts/ProjectContext";
import { fetchAlignment, type DepartmentAlignment, type DepartmentStakeholder } from "@/data/alignment";
import { fetchDecisions, type Decision } from "@/data/decisions";
import {
  acceptLatestDecisions,
  fetchCosVoiceMessage,
  fetchStakeholderReports,
  type StakeholderRecord,
} from "@/data/team";
import { DepartmentBadge } from "@/components/DepartmentBadge";
import { DecisionList } from "@/components/DecisionList";
import { DecisionTimeline } from "@/components/DecisionTimeline";
import { AIBriefingPanel, type SuggestedCommunication } from "@/components/AIBriefingPanel";
import { toast } from "sonner";
import { synthesizeSpeech } from "@/data/tts";

interface TeamProjectSnapshot {
  projectId: string;
  projectName: string;
  department: DepartmentAlignment["department_id"];
  stakeholder: DepartmentStakeholder;
  aiSummary: string;
  decisions: Decision[];
}

function toTitleCaseRole(role: string): string {
  return role
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function buildAiSummary(
  teamMemberName: string,
  projectName: string,
  department: string,
  stakeholder: DepartmentStakeholder,
  alignmentSummary: string,
  relatedDecisions: Decision[]
): string {
  const statusMessage =
    stakeholder.status === "out_of_sync"
      ? `${teamMemberName} appears out of sync with latest approved decisions.`
      : stakeholder.status === "awaiting_update"
      ? `${teamMemberName} has pending acknowledgements on recent decision updates.`
      : `${teamMemberName} is aligned with the current decision baseline.`;

  const decisionMessage =
    relatedDecisions.length > 0
      ? `You are currently connected to ${relatedDecisions.length} tracked decision${
          relatedDecisions.length === 1 ? "" : "s"
        } in ${projectName}.`
      : `No tracked decision links have been detected yet for ${teamMemberName} in ${projectName}.`;

  return `${statusMessage} Department: ${department}. ${decisionMessage} AI summary: ${alignmentSummary}`;
}

function buildSuggestedCommunications(
  profile: TeamProjectSnapshot | undefined,
  reports: StakeholderRecord[]
): SuggestedCommunication[] {
  if (!profile) {
    return [];
  }

  const firstName = profile.stakeholder.name.split(" ")[0];
  return [
    {
      channel: "voice",
      recipient: profile.stakeholder.name,
      preview: `${firstName}, here is your quick voice brief on recent decision updates and downstream impact.`,
    },
    {
      channel: "email",
      recipient: `${profile.stakeholder.name} + Product Leads`,
      preview: `Decision context for ${profile.projectName}: scope changes, reasoning, and expected team-level actions.`,
    },
    {
      channel: "slack",
      recipient: reports.length > 0 ? reports.map((r) => r.name).join(", ") : "Team channel",
      preview: "Please confirm acknowledgment of the latest approved decision and execution impact.",
    },
    {
      channel: "calendar",
      recipient: `${profile.projectName} coordination group`,
      preview: "Open meeting context, attendance, and affected stakeholders before next sync.",
    },
  ];
}

export default function TeamPortal() {
  const navigate = useNavigate();
  const { teamMemberName, logout } = useAuth();
  const { projects } = useProject();

  const [loading, setLoading] = useState<boolean>(false);
  const [profiles, setProfiles] = useState<TeamProjectSnapshot[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [selectedDecision, setSelectedDecision] = useState<Decision | null>(null);
  const [reportsByProfile, setReportsByProfile] = useState<Record<string, StakeholderRecord[]>>({});
  const [notifiedByProfile, setNotifiedByProfile] = useState<Record<string, string[]>>({});
  const [cosMessagesByProfile, setCosMessagesByProfile] = useState<Record<string, string>>({});
  const [isPlayingCosMessage, setIsPlayingCosMessage] = useState<boolean>(false);
  const [isLoadingCosAudio, setIsLoadingCosAudio] = useState<boolean>(false);
  const cosAudioRef = useRef<HTMLAudioElement | null>(null);

  const normalizedMemberName = teamMemberName.trim().toLowerCase();

  const loadProfileForProject = async (
    projectId: string,
    projectName: string
  ): Promise<TeamProjectSnapshot | null> => {
    try {
      const [alignment, decisions] = await Promise.all([
        fetchAlignment(projectId),
        fetchDecisions(projectId),
      ]);

      const department = alignment.departments.find((dept) =>
        dept.stakeholders.some(
          (person) => person.name.trim().toLowerCase() === normalizedMemberName
        )
      );
      if (!department) {
        return null;
      }

      const stakeholder = department.stakeholders.find(
        (person) => person.name.trim().toLowerCase() === normalizedMemberName
      );
      if (!stakeholder) {
        return null;
      }

      const relatedDecisions = decisions.decisions.filter((decision) =>
        decision.versions.some((version) =>
          version.stakeholders.some(
            (person) => person.name.trim().toLowerCase() === normalizedMemberName
          )
        )
      );

      return {
        projectId,
        projectName,
        department: department.department_id,
        stakeholder,
        aiSummary: buildAiSummary(
          stakeholder.name,
          projectName,
          department.department_id,
          stakeholder,
          alignment.summary,
          relatedDecisions
        ),
        decisions: relatedDecisions,
      };
    } catch (error) {
      console.error(`Error loading team profile for project ${projectId}:`, error);
      return null;
    }
  };

  useEffect(() => {
    let active = true;
    setLoading(true);
    setSelectedDecision(null);

    Promise.all(
      projects.map((project) => loadProfileForProject(project.project_id, project.project_name))
    )
      .then((matches) => {
        if (!active) {
          return;
        }
        const filtered = matches.filter((match): match is TeamProjectSnapshot => match !== null);
        setProfiles(filtered);
        if (filtered.length > 0) {
          setSelectedProjectId(filtered[0].projectId);
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [projects, normalizedMemberName]);

  const activeProfile = useMemo(
    () => profiles.find((profile) => profile.projectId === selectedProjectId) ?? profiles[0],
    [profiles, selectedProjectId]
  );

  const profileKey = activeProfile ? `${activeProfile.projectId}:${activeProfile.stakeholder.id}` : "";
  const decisionsForView = activeProfile?.decisions ?? [];
  const directReports = profileKey ? reportsByProfile[profileKey] ?? [] : [];
  const notifiedIds = profileKey ? notifiedByProfile[profileKey] ?? [] : [];
  const decisionAccepted =
    directReports.length > 0 &&
    directReports.every((report) => notifiedIds.includes(report.stakeholder_id));
  const suggestedCommunications = useMemo(
    () => buildSuggestedCommunications(activeProfile, directReports),
    [activeProfile, directReports]
  );
  const cosMessage = profileKey ? cosMessagesByProfile[profileKey] ?? "" : "";
  const aiSummaryWithContext =
    activeProfile?.aiSummary && cosMessage
      ? `${activeProfile.aiSummary} COS context: ${cosMessage}`
      : (activeProfile?.aiSummary ?? "");

  useEffect(() => {
    if (!activeProfile) {
      return;
    }

    let active = true;
    fetchStakeholderReports(activeProfile.projectId, activeProfile.stakeholder.id)
      .then((response) => {
        if (!active) {
          return;
        }
        const key = `${activeProfile.projectId}:${activeProfile.stakeholder.id}`;
        setReportsByProfile((current) => ({ ...current, [key]: response.reports }));
      })
      .catch((error) => {
        console.error("Error loading downstream reports:", error);
      });

    return () => {
      active = false;
    };
  }, [activeProfile?.projectId, activeProfile?.stakeholder.id]);

  useEffect(() => {
    if (!activeProfile) {
      return;
    }

    let active = true;
    fetchCosVoiceMessage(activeProfile.projectId, activeProfile.stakeholder.id)
      .then((response) => {
        if (!active) {
          return;
        }
        const key = `${activeProfile.projectId}:${activeProfile.stakeholder.id}`;
        setCosMessagesByProfile((current) => ({ ...current, [key]: response.message ?? "" }));
      })
      .catch((error) => {
        console.error("Error loading COS voice message:", error);
      });

    return () => {
      active = false;
    };
  }, [activeProfile?.projectId, activeProfile?.stakeholder.id]);

  useEffect(() => {
    return () => {
      if (cosAudioRef.current) {
        cosAudioRef.current.pause();
        cosAudioRef.current = null;
      }
    };
  }, []);

  return (
    <div className="min-h-screen bg-[#0a0e1a] p-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-blue-100">Team Workspace</h1>
            <p className="mt-1 text-blue-300/70">
              Team member view for <span className="font-medium text-cyan-300">{teamMemberName}</span>
            </p>
          </div>
          <Button
            onClick={() => {
              logout();
              navigate("/");
            }}
            variant="ghost"
            className="text-blue-300/70 hover:text-cyan-300 hover:bg-blue-500/10"
          >
            Log Out
          </Button>
        </div>

        {loading ? (
          <div className="rounded-xl border border-blue-500/30 bg-[#0d1225] p-8 text-center text-blue-300/70">
            Loading team member details...
          </div>
        ) : profiles.length === 0 ? (
          <div className="rounded-xl border border-blue-500/30 bg-[#0d1225] p-8 text-center">
            <p className="text-blue-300/80">No team profile found for {teamMemberName}.</p>
            <p className="mt-2 text-sm text-blue-300/60">
              Try a known stakeholder name like Maya Chen, Jordan Lee, or Alex Rivera.
            </p>
          </div>
        ) : (
          <>
            <div className="space-y-4">
              <div className="rounded-xl border border-blue-500/30 bg-[#0d1225] p-6">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 shadow-lg shadow-blue-500/30">
                    <User className="h-5 w-5 text-white" />
                  </div>
                  <h2 className="text-lg font-semibold text-blue-100">Member Details</h2>
                </div>
                {profiles.length > 1 && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {profiles.map((profile) => (
                      <button
                        key={profile.projectId}
                        type="button"
                        className={`rounded-md border px-3 py-1 text-xs transition ${
                          activeProfile?.projectId === profile.projectId
                            ? "border-cyan-400 bg-cyan-500/10 text-cyan-300"
                            : "border-blue-500/30 bg-blue-500/5 text-blue-300/70 hover:bg-blue-500/10"
                        }`}
                        onClick={() => {
                          setSelectedProjectId(profile.projectId);
                          setSelectedDecision(null);
                        }}
                      >
                        {profile.projectName}
                      </button>
                    ))}
                  </div>
                )}

                {activeProfile && (
                  <div className="mt-4 space-y-2 text-sm text-blue-200/90">
                    <p>
                      <span className="text-blue-300/60">Name:</span> {activeProfile.stakeholder.name}
                    </p>
                    <p>
                      <span className="text-blue-300/60">Project:</span> {activeProfile.projectName}
                    </p>
                    <p className="flex items-center gap-2">
                      <span className="text-blue-300/60">Department:</span>
                      <DepartmentBadge department={activeProfile.department} variant="muted" size="sm" />
                    </p>
                    <p>
                      <span className="text-blue-300/60">Role:</span>{" "}
                      {toTitleCaseRole(activeProfile.stakeholder.role)}
                    </p>
                    <p>
                      <span className="text-blue-300/60">Status:</span>{" "}
                      {toTitleCaseRole(activeProfile.stakeholder.status)}
                    </p>
                  </div>
                )}
              </div>

              <div className="rounded-xl border border-blue-500/30 bg-[#0d1225] p-6">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 shadow-lg shadow-blue-500/30">
                    <MessageSquare className="h-5 w-5 text-white" />
                  </div>
                  <h2 className="text-lg font-semibold text-blue-100">New AI Communication</h2>
                </div>
                <div className="mt-4 space-y-4">
                  <AIBriefingPanel
                    summary={aiSummaryWithContext}
                    suggestedCommunications={suggestedCommunications}
                    className="border-slate-300 bg-slate-100 text-slate-900 [&_.text-foreground]:text-slate-900 [&_.text-muted-foreground]:text-slate-700 [&_.bg-card]:bg-slate-100 [&_.bg-muted\\/30]:bg-slate-200 [&_.bg-muted\\/20]:bg-slate-200 [&_.border-border]:border-slate-300 [&_.border-border\\/60]:border-slate-300 [&_.bg-primary\\/10]:bg-cyan-100 [&_.text-primary]:text-cyan-800"
                  />

                  {activeProfile?.stakeholder.name.toLowerCase() === "maya chen" && cosMessage && (
                    <div className="rounded-lg border border-cyan-500/30 bg-cyan-500/10 p-4">
                      <p className="text-xs font-medium uppercase tracking-wider text-cyan-300/80">
                        Message From COS
                      </p>
                      <p className="mt-1 text-sm text-blue-100">{cosMessage}</p>
                      <Button
                        className="mt-3 bg-cyan-600 text-white hover:bg-cyan-500"
                        onClick={async () => {
                          if (isLoadingCosAudio) {
                            return;
                          }

                          if (isPlayingCosMessage && cosAudioRef.current) {
                            cosAudioRef.current.pause();
                            setIsPlayingCosMessage(false);
                            return;
                          }

                          try {
                            setIsLoadingCosAudio(true);

                            if (cosAudioRef.current) {
                              await cosAudioRef.current.play();
                              setIsPlayingCosMessage(true);
                              return;
                            }

                            const audioBlob = await synthesizeSpeech(cosMessage);
                            const nextUrl = URL.createObjectURL(audioBlob);
                            const audio = new Audio(nextUrl);
                            audio.onended = () => setIsPlayingCosMessage(false);
                            audio.onpause = () => setIsPlayingCosMessage(false);
                            cosAudioRef.current = audio;
                            await audio.play();
                            setIsPlayingCosMessage(true);
                          } catch (error) {
                            console.error("Error playing COS message:", error);
                            toast.error("Failed to play COS message.");
                            setIsPlayingCosMessage(false);
                          } finally {
                            setIsLoadingCosAudio(false);
                          }
                        }}
                      >
                        {isLoadingCosAudio ? (
                          "Preparing audio..."
                        ) : isPlayingCosMessage ? (
                          <>
                            <Pause className="mr-2 h-4 w-4" />
                            Pause COS Message
                          </>
                        ) : (
                          <>
                            <Play className="mr-2 h-4 w-4" />
                            Play COS Message
                          </>
                        )}
                      </Button>
                    </div>
                  )}

                  <div className="flex flex-wrap gap-2">
                    <Button
                      onClick={async () => {
                        if (!activeProfile) {
                          return;
                        }
                        try {
                          const response = await acceptLatestDecisions(
                            activeProfile.projectId,
                            activeProfile.stakeholder.id,
                            true
                          );
                          setNotifiedByProfile((current) => ({
                            ...current,
                            [profileKey]: response.notified_stakeholders.map(
                              (stakeholder) => stakeholder.stakeholder_id
                            ),
                          }));

                          const refreshed = await loadProfileForProject(
                            activeProfile.projectId,
                            activeProfile.projectName
                          );
                          if (refreshed) {
                            setProfiles((current) =>
                              current.map((item) =>
                                item.projectId === refreshed.projectId ? refreshed : item
                              )
                            );
                          }

                          toast.success(response.message);
                        } catch (error) {
                          console.error("Error accepting latest decisions:", error);
                          toast.error("Failed to accept latest decisions.");
                        }
                      }}
                      disabled={!activeProfile || decisionAccepted}
                      className="bg-emerald-600 hover:bg-emerald-500 text-white"
                    >
                      {decisionAccepted ? "Decision Accepted" : "Accept Decision"}
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={() => {
                        toast.success("Conflict resolution meeting requested.");
                      }}
                      className="bg-blue-900/40 text-blue-100 hover:bg-blue-900/60"
                    >
                      Schedule Meeting to Resolve Conflict
                    </Button>
                  </div>

                  {directReports.length > 0 && (
                    <div className="rounded-lg border border-blue-500/20 bg-[#0d1225]/80 p-4">
                      <h3 className="text-xs font-medium uppercase tracking-wider text-blue-300/60">
                        Downstream Team Notifications
                      </h3>
                      <div className="mt-3 space-y-2">
                        {directReports.map((report) => (
                          <div
                            key={report.stakeholder_id}
                            className="flex items-center justify-between rounded-md border border-blue-500/20 bg-[#0a0e1a] px-3 py-2"
                          >
                            <div>
                              <p className="text-sm text-blue-100">{report.name}</p>
                              <p className="text-xs text-blue-300/60">{report.department}</p>
                            </div>
                            <span
                              className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                                notifiedIds.includes(report.stakeholder_id)
                                  ? "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"
                                  : "bg-amber-500/15 text-amber-300 border border-amber-500/30"
                              }`}
                            >
                              {notifiedIds.includes(report.stakeholder_id) ? "Notified" : "Pending"}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {selectedDecision ? (
              <div className="space-y-6">
                <div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedDecision(null)}
                    className="mb-2 -ml-2 text-blue-300/70 hover:text-cyan-300 hover:bg-blue-500/10"
                  >
                    <ArrowLeft className="mr-1 h-4 w-4" />
                    All Relevant Decisions
                  </Button>
                  <h2 className="text-2xl font-semibold tracking-tight text-blue-100">
                    {selectedDecision.title}
                  </h2>
                  <p className="mt-1 text-sm text-blue-300/70">
                    Decision evolution for {teamMemberName} in {activeProfile?.projectName}.
                  </p>
                </div>

                <div className="rounded-xl border border-blue-500/30 bg-[#0d1225] p-6 backdrop-blur-sm">
                  <DecisionTimeline
                    versions={selectedDecision.versions}
                    latestVersion={selectedDecision.latest_version}
                    decisionTitle={selectedDecision.title}
                  />
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 shadow-lg shadow-blue-500/30">
                    <GitBranch className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <h2 className="text-xl font-semibold text-blue-100">Decision Evolution</h2>
                    <p className="text-sm text-blue-300/70">
                      Decisions connected to {teamMemberName} in {activeProfile?.projectName}
                    </p>
                  </div>
                </div>

                {decisionsForView.length > 0 ? (
                  <DecisionList decisions={decisionsForView} onSelect={setSelectedDecision} />
                ) : (
                  <div className="rounded-xl border border-blue-500/30 bg-[#0d1225] p-8 text-center text-sm text-blue-300/70">
                    No decision history linked to this team member yet.
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
