import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { Calendar, GitBranch, Target, Sparkles } from "lucide-react";
import { ProjectSelector } from "@/components/ProjectSelector";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";

const navItems = [
  { to: "/meetings", label: "Meetings", icon: Calendar },
  { to: "/evolution", label: "Decision Evolution", icon: GitBranch },
  { to: "/alignment", label: "Alignment Dashboard", icon: Target },
];

export function Layout() {
  const navigate = useNavigate();
  const { logout } = useAuth();

  return (
    <div className="min-h-screen bg-[#0a0e1a]">
      {/* Header */}
      <header className="border-b border-blue-500/20 bg-[#0d1225]/80 backdrop-blur-sm">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-6">
            <button 
              onClick={() => navigate("/")}
              className="flex items-center gap-3 hover:opacity-80 transition-opacity"
            >
              <div className="relative">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-cyan-600 shadow-lg shadow-blue-500/30">
                  <Sparkles className="h-4 w-4 text-white" />
                </div>
                <div className="absolute inset-0 blur-md bg-cyan-400/30 rounded-lg" />
              </div>
              <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                COS
              </span>
            </button>

            {/* Project Selector */}
            <div className="relative">
              <ProjectSelector />
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Navigation */}
            <nav className="flex items-center gap-1">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                      isActive
                        ? "bg-blue-500/20 text-cyan-300 border border-blue-500/30"
                        : "text-blue-300/70 hover:bg-blue-500/10 hover:text-cyan-300"
                    }`
                  }
                >
                  <item.icon className="h-4 w-4" />
                  <span className="hidden md:inline">{item.label}</span>
                </NavLink>
              ))}
            </nav>
            <Button
              variant="ghost"
              size="sm"
              className="text-blue-300/70 hover:bg-blue-500/10 hover:text-cyan-300"
              onClick={() => {
                logout();
                navigate("/");
              }}
            >
              Log Out
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container py-8">
        <Outlet />
      </main>
    </div>
  );
}
