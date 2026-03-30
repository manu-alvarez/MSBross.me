import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ error, errorInfo });
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-950 text-white flex items-center justify-center p-6">
          <div className="max-w-lg w-full rounded-xl bg-black/60 p-6 border border-white/20">
            <h1 className="text-2xl font-bold mb-2">Oops! Algo falló.</h1>
            <p className="mb-4">Recarga la página o contacta soporte si el problema persiste.</p>
            <button
              className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded text-white"
              onClick={() => window.location.reload()}
            >
              Recargar
            </button>
            {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
              <details className="mt-4 text-xs text-left text-red-200">
                <summary>Detalles del error</summary>
                <pre>{this.state.error && this.state.error.toString()}</pre>
                <pre>{this.state.errorInfo.componentStack}</pre>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
