import { useAuth } from "@/context/useAuth"
import AuthPage from "@/pages/AuthPage"
import TasksPage from "@/pages/TasksPage"

function AppContent() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-muted-foreground text-sm">Loading...</p>
      </div>
    )
  }

  return user ? <TasksPage /> : <AuthPage />
}

export default function App() {
  return <AppContent />
}
