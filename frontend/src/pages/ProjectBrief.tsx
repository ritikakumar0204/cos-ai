import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useProject } from "@/contexts/ProjectContext";
import { useAuth } from "@/contexts/AuthContext";
import { fetchDecisions } from "@/data/decisions";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sparkles, ArrowRight, FolderOpen, AlertTriangle, Orbit, Radar } from "lucide-react";

export default function ProjectBrief() {
  const navigate = useNavigate();
  const { projects } = useProject();
  const { loginAsAdmin, loginAsTeamMember } = useAuth();
  const [driftingProjects, setDriftingProjects] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [teamMemberName, setTeamMemberName] = useState<string>("");
  const [showTeamLoginForm, setShowTeamLoginForm] = useState<boolean>(false);

  useEffect(() => {
    let active = true;
    setLoading(true);

    Promise.all(
      projects.map(async (project) => {
        try {
          const response = await fetchDecisions(project.project_id);
          return response.decisions.some((decision) => decision.status === "drifting");
        } catch (error) {
          console.error("Error loading decision stats:", error);
          return false;
        }
      })
    )
      .then((driftFlags) => {
        if (!active) {
          return;
        }
        setDriftingProjects(driftFlags.filter(Boolean).length);
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [projects]);

  const totalProjects = projects.length;

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#060912] px-6 py-12 sm:px-8">
      <div className="pointer-events-none absolute inset-0 hero-grid opacity-60" />
      <div className="pointer-events-none absolute -left-24 top-[-8rem] h-[24rem] w-[24rem] rounded-full bg-cyan-400/20 blur-[100px] animate-float-slow" />
      <div className="pointer-events-none absolute -right-16 bottom-[-10rem] h-[26rem] w-[26rem] rounded-full bg-orange-400/15 blur-[110px] animate-float-reverse" />
      <div className="pointer-events-none absolute left-1/2 top-[35%] h-[30rem] w-[30rem] -translate-x-1/2 rounded-full bg-blue-600/15 blur-[140px]" />

      <div className="relative mx-auto flex w-full max-w-6xl flex-col gap-12">
        <div className="animate-reveal-up">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-cyan-300/30 bg-cyan-300/10 px-4 py-2 text-xs uppercase tracking-[0.28em] text-cyan-200">
            <Radar className="h-3.5 w-3.5" />
            Strategic Intelligence Platform
          </div>

          <div className="flex flex-col items-start gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <div className="mb-4 flex items-center gap-4">
                <div className="relative">
                  <div className="absolute inset-0 rounded-xl bg-cyan-300/40 blur-lg" />
                  <div className="relative rounded-xl border border-cyan-200/40 bg-cyan-300/20 p-3 backdrop-blur-sm">
                    <Sparkles className="h-8 w-8 text-cyan-100" />
                  </div>
                </div>
                <h1
                  className="text-6xl font-black leading-none tracking-tight text-transparent sm:text-7xl md:text-8xl"
                  style={{
                    fontFamily: "'Space Grotesk', sans-serif",
                    backgroundImage: "linear-gradient(110deg, #bff8ff 0%, #5dc5ff 35%, #ffd08d 100%)",
                    WebkitBackgroundClip: "text",
                    backgroundClip: "text",
                  }}
                >
                  COS
                </h1>
              </div>
              <p
                className="max-w-2xl text-base text-blue-100/75 sm:text-lg"
                style={{ fontFamily: "'Manrope', sans-serif" }}
              >
                AI Chief of Staff that spots drift early, aligns teams fast, and keeps complex projects moving in one direction.
              </p>
            </div>

            <div className="hidden items-center gap-2 rounded-full border border-blue-300/25 bg-blue-400/10 px-4 py-2 text-sm text-blue-100/80 backdrop-blur-sm sm:inline-flex">
              <Orbit className="h-4 w-4 text-orange-200" />
              Live organization pulse
            </div>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="glass-panel animate-reveal-up [animation-delay:80ms]">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-cyan-300/20 p-3 text-cyan-100 shadow-lg shadow-cyan-500/20">
                <FolderOpen className="h-6 w-6" />
              </div>
              <div>
                <p className="text-sm uppercase tracking-[0.16em] text-cyan-100/60">Projects Tracked</p>
                <p className="text-4xl font-bold text-white">{totalProjects}</p>
              </div>
            </div>
          </div>

          <div className="glass-panel animate-reveal-up [animation-delay:150ms]">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-orange-300/20 p-3 text-orange-100 shadow-lg shadow-orange-500/20">
                <AlertTriangle className="h-6 w-6" />
              </div>
              <div>
                <p className="text-sm uppercase tracking-[0.16em] text-orange-100/70">Drift Alerts</p>
                <p className="text-4xl font-bold text-white">{loading ? "-" : driftingProjects}</p>
              </div>
            </div>
          </div>
        </div>

        {!showTeamLoginForm ? (
          <div className="grid gap-4 md:grid-cols-2">
            <div className="animate-reveal-up [animation-delay:220ms]">
              <Button
                size="lg"
                onClick={() => {
                  loginAsAdmin();
                  navigate("/meetings");
                }}
                className="group relative h-16 w-full overflow-hidden border-0 bg-gradient-to-r from-cyan-500 to-blue-500 text-base font-semibold text-white shadow-xl shadow-cyan-600/25 transition-transform duration-300 hover:scale-[1.015] hover:from-cyan-400 hover:to-blue-400"
              >
                <span className="absolute inset-0 bg-[linear-gradient(120deg,transparent_20%,rgba(255,255,255,0.28)_50%,transparent_80%)] opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
                <span className="relative flex items-center gap-2">
                  Admin Login
                  <ArrowRight className="h-4 w-4" />
                </span>
              </Button>
            </div>

            <div className="animate-reveal-up [animation-delay:280ms]">
              <Button
                size="lg"
                onClick={() => setShowTeamLoginForm(true)}
                className="group relative h-16 w-full overflow-hidden border border-blue-300/25 bg-blue-200/10 text-base font-semibold text-blue-100 backdrop-blur-md transition-all duration-300 hover:border-blue-200/40 hover:bg-blue-200/15 hover:shadow-xl hover:shadow-blue-800/40"
              >
                <span className="relative flex items-center gap-2">
                  Team Login
                  <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-0.5" />
                </span>
              </Button>
            </div>
          </div>
        ) : (
          <div className="glass-panel max-w-xl animate-reveal-up">
            <p className="mb-2 text-left text-xs uppercase tracking-[0.2em] text-cyan-100/60">
              Team Login
            </p>
            <div className="flex items-center gap-2">
              <Input
                value={teamMemberName}
                onChange={(event) => setTeamMemberName(event.target.value)}
                placeholder="Enter your name"
                className="border-cyan-300/30 bg-[#070d1e] text-blue-100 placeholder:text-blue-100/45 focus-visible:ring-cyan-300"
              />
              <Button
                type="button"
                onClick={() => {
                  const name = teamMemberName.trim();
                  if (!name) {
                    return;
                  }
                  loginAsTeamMember(name);
                  navigate("/team");
                }}
                className="bg-cyan-600 text-white hover:bg-cyan-500"
              >
                Enter
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
