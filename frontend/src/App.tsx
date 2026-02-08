import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Routes, Route } from "react-router-dom";
import { Layout } from "@/components/Layout";
import { ProjectProvider } from "@/contexts/ProjectContext";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import ProjectBrief from "@/pages/ProjectBrief";
import Meetings from "@/pages/Meetings";
import DecisionEvolution from "@/pages/DecisionEvolution";
import AlignmentDashboard from "@/pages/AlignmentDashboard";
import TeamPortal from "@/pages/TeamPortal";
import NotFound from "@/pages/NotFound";

const queryClient = new QueryClient();

function RequireAdmin({ children }: { children: JSX.Element }) {
  const { role } = useAuth();
  if (role !== "admin") {
    return <Navigate to="/" replace />;
  }
  return children;
}

function RequireTeamMember({ children }: { children: JSX.Element }) {
  const { role } = useAuth();
  if (role !== "team") {
    return <Navigate to="/" replace />;
  }
  return children;
}

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <AuthProvider>
        <ProjectProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<ProjectBrief />} />
              <Route
                path="/team"
                element={
                  <RequireTeamMember>
                    <TeamPortal />
                  </RequireTeamMember>
                }
              />
              <Route
                element={
                  <RequireAdmin>
                    <Layout />
                  </RequireAdmin>
                }
              >
                <Route path="/meetings" element={<Meetings />} />
                <Route path="/evolution" element={<DecisionEvolution />} />
                <Route path="/alignment" element={<AlignmentDashboard />} />
              </Route>
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </ProjectProvider>
      </AuthProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
