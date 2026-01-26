"use client";

import React, { Component, ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
    
    // Log to backend monitoring service
    this.logErrorToService(error, errorInfo);
  }

  logErrorToService(error: Error, errorInfo: React.ErrorInfo) {
    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
      
      fetch(`${API_BASE_URL}/api/v1/system/log-error`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          error_message: error.message,
          error_stack: error.stack,
          component_stack: errorInfo.componentStack,
          timestamp: new Date().toISOString(),
          user_agent: navigator.userAgent,
        }),
      }).catch(() => {
        // Silent fail - error logging shouldn't break the app
      });
    } catch {
      // Silent fail
    }
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex min-h-[400px] items-center justify-center p-8">
          <div className="w-full max-w-md rounded-2xl border border-red-500/30 bg-red-500/5 p-6">
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-red-500/20 p-3">
                <AlertTriangle size={24} className="text-red-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-zinc-100">
                  Something went wrong
                </h3>
                <p className="mt-1 text-sm text-zinc-400">
                  An unexpected error occurred in this component
                </p>
              </div>
            </div>

            {this.state.error && (
              <div className="mt-4 rounded-xl border border-white/10 bg-black/20 p-3">
                <div className="text-xs font-mono text-red-300">
                  {this.state.error.message}
                </div>
              </div>
            )}

            <div className="mt-6 flex gap-2">
              <button
                onClick={this.handleReset}
                className="flex items-center gap-2 rounded-xl bg-emerald-400 px-4 py-2 text-sm font-semibold text-black transition hover:bg-emerald-300"
              >
                <RefreshCw size={14} />
                Try Again
              </button>
              <button
                onClick={() => window.location.reload()}
                className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-zinc-200 transition hover:bg-white/10"
              >
                Reload Page
              </button>
            </div>

            {process.env.NODE_ENV === "development" && this.state.errorInfo && (
              <details className="mt-4">
                <summary className="cursor-pointer text-xs text-zinc-500">
                  Stack Trace (Dev Only)
                </summary>
                <pre className="mt-2 overflow-auto rounded-lg bg-black/40 p-2 text-[10px] text-zinc-400">
                  {this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
