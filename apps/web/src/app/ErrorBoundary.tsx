import { Component, type ReactNode } from 'react';

export class ErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() {
    if (this.state.failed) return (
      <main className="fatal"><h1>Workspace unavailable</h1>
        <button onClick={() => window.location.reload()}>Reload</button></main>
    );
    return this.props.children;
  }
}
