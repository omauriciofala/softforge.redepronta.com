import React, { useEffect, useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider, useAuth } from "./features/auth/AuthContext";
import { AuthForms } from "./features/auth/AuthForms";
import { DocsViewer } from "./features/docs/DocsViewer";
import { ProjectDashboard } from "./features/projects/ProjectDashboard";
import { WorkspaceProvider } from "./features/workspaces/WorkspaceContext";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutos
      retry: 1,
    },
  },
});

const AppContent: React.FC = () => {
  const { user, isLoading } = useAuth();
  const [showDocs, setShowDocs] = useState<boolean>(() => window.location.hash === "#docs");

  useEffect(() => {
    const handleHashChange = () => {
      setShowDocs(window.location.hash === "#docs");
    };
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  const openDocs = () => {
    window.location.hash = "#docs";
    setShowDocs(true);
  };

  const closeDocs = () => {
    window.location.hash = "";
    setShowDocs(false);
  };

  if (showDocs) {
    return <DocsViewer onClose={closeDocs} />;
  }

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center space-y-3">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="text-sm font-medium text-muted-foreground">Iniciando SoftForge...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <AuthForms onOpenDocs={openDocs} />;
  }

  return (
    <WorkspaceProvider>
      <ProjectDashboard onOpenDocs={openDocs} />
    </WorkspaceProvider>
  );
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
