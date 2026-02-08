import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

export type UserRole = "guest" | "admin" | "team";

interface AuthState {
  role: UserRole;
  teamMemberName: string;
}

interface AuthContextValue {
  role: UserRole;
  teamMemberName: string;
  loginAsAdmin: () => void;
  loginAsTeamMember: (name: string) => void;
  logout: () => void;
}

const STORAGE_KEY = "cos_auth_state";

function loadAuthState(): AuthState {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return { role: "guest", teamMemberName: "" };
    }
    const parsed = JSON.parse(raw) as AuthState;
    if (!parsed.role || !["guest", "admin", "team"].includes(parsed.role)) {
      return { role: "guest", teamMemberName: "" };
    }
    return {
      role: parsed.role,
      teamMemberName: parsed.teamMemberName ?? "",
    };
  } catch {
    return { role: "guest", teamMemberName: "" };
  }
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(() => loadAuthState());

  const persist = (nextState: AuthState) => {
    setState(nextState);
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(nextState));
  };

  const value = useMemo<AuthContextValue>(
    () => ({
      role: state.role,
      teamMemberName: state.teamMemberName,
      loginAsAdmin: () => persist({ role: "admin", teamMemberName: "" }),
      loginAsTeamMember: (name: string) =>
        persist({ role: "team", teamMemberName: name.trim() }),
      logout: () => persist({ role: "guest", teamMemberName: "" }),
    }),
    [state.role, state.teamMemberName]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
