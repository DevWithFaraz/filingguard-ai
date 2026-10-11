import { Component, type ReactNode } from 'react';
import logo from '../assets/filingguard-logo.png';
import '../components/layout/workflow.css';

export class ErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() {
    if (this.state.failed) return (
      <main className="document-workspace workflow-fatal"><img src={logo} alt="FilingGuard AI" /><h1>Workspace unavailable</h1>
        <p>The page could not be displayed. Reload to reconnect, or return home to start again.</p><div className="workflow-actions">
        <button className="primary-button" onClick={() => window.location.reload()}>Reload</button><a className="secondary-button" href="/">Return home</a></div></main>
    );
    return this.props.children;
  }
}
