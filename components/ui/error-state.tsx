interface ErrorStateProps {
  message: string
  onRetry?: () => void
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center gap-4 px-6">
      <p className="font-mono text-lg text-loss uppercase tracking-widest">Error</p>
      <p className="font-mono text-sm text-muted-foreground">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="font-mono text-xs text-foreground uppercase tracking-widest px-4 py-2 border border-border hover:border-foreground transition-colors"
        >
          Retry
        </button>
      )}
    </div>
  )
}
