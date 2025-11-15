import { useNavigate } from "react-router-dom";

interface EditorStatusViewProps {
  loading: boolean;
  error: string | null;
  navigate: ReturnType<typeof useNavigate>;
}

export const EditorStatusView = ({ loading, error, navigate }: EditorStatusViewProps) => {
  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-sm text-muted-foreground">Loading project...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 mb-4">⚠️</div>
          <p className="text-sm text-muted-foreground mb-4">{error}</p>
          <button 
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
           Try Again
          </button>
        </div>
      </div>
    );
  }

  return null;
};