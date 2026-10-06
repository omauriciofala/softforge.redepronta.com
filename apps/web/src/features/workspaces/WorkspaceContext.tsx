import React, { createContext, useContext, useEffect, useState } from "react";
import { AXIOS_INSTANCE } from "@/lib/api-client";
import { useAuth } from "../auth/AuthContext";

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  owner_id: string;
  role: "owner" | "admin" | "member" | "viewer";
  created_at: string;
}

interface WorkspaceContextType {
  workspaces: Workspace[];
  activeWorkspace: Workspace | null;
  isLoading: boolean;
  setActiveWorkspace: (ws: Workspace) => void;
  createWorkspace: (name: string) => Promise<Workspace>;
  refreshWorkspaces: () => Promise<void>;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export const WorkspaceProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeWorkspace, setActiveWorkspace] = useState<Workspace | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchWorkspaces = async () => {
    if (!user) {
      setWorkspaces([]);
      setActiveWorkspace(null);
      return;
    }
    setIsLoading(true);
    try {
      const res = await AXIOS_INSTANCE.get<Workspace[]>("/api/v1/workspaces");
      setWorkspaces(res.data);
      if (res.data.length > 0 && !activeWorkspace) {
        setActiveWorkspace(res.data[0]);
      }
    } catch (err) {
      console.error("Erro ao carregar workspaces:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkspaces();
  }, [user]);

  const createWorkspace = async (name: string): Promise<Workspace> => {
    const res = await AXIOS_INSTANCE.post<Workspace>("/api/v1/workspaces", { name });
    const newWs = res.data;
    setWorkspaces((prev) => [newWs, ...prev]);
    setActiveWorkspace(newWs);
    return newWs;
  };

  return (
    <WorkspaceContext.Provider
      value={{
        workspaces,
        activeWorkspace,
        isLoading,
        setActiveWorkspace,
        createWorkspace,
        refreshWorkspaces: fetchWorkspaces,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
};

export const useWorkspaces = (): WorkspaceContextType => {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error("useWorkspaces deve ser utilizado dentro de um WorkspaceProvider");
  }
  return context;
};
