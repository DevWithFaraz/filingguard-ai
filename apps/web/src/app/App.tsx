import { useQuery } from '@tanstack/react-query';
import { Activity, ArrowRight, FileText, LockKeyhole, RefreshCw, Settings, ShieldCheck } from 'lucide-react';
import { NavLink, Route, Routes } from 'react-router';
import { apiOrigin, getHealth } from '../lib/api/client';

export function App() {
  const health = useQuery({ queryKey: ['health'], queryFn: ({ signal }) => getHealth(signal),
    refetchInterval: 30000 });
  return (
    <div className="workspace">
      <a className="skip-link" href="#main">Skip to content</a>
      <aside className="sidebar">
        <div className="brand"><ShieldCheck size={28} aria-hidden="true" />
          <span>FilingGuard <strong>AI</strong></span></div>
        <div className="workspace-label">WORKSPACE</div>
        <nav aria-label="Main navigation">
          <NavLink to="/" end><FileText size={18} />Review</NavLink>
          <NavLink to="/activity"><Activity size={18} />Activity</NavLink>
          <NavLink to="/settings"><Settings size={18} />Settings</NavLink>
        </nav>
        <div className="sidebar-footer"><span className="edition">LEXHACK 2026</span>
          <span>Development preview</span></div>
      </aside>
      <div className="content">
        <header className="topbar"><span>Pre-filing review</span>
          <div className="connection" role="status">
            <span className={`status-dot ${health.isSuccess ? 'online' : ''}`} />
            {health.isPending ? 'Connecting' : health.isError ? 'API unavailable' : 'API connected'}
            <button className="icon-button" aria-label="Refresh API connection" title="Refresh API connection"
              disabled={health.isFetching} onClick={() => void health.refetch()}>
              <RefreshCw size={16} className={health.isFetching ? 'spinning' : ''} /></button>
          </div>
        </header>
        <main id="main" tabIndex={-1}>
          <Routes>
            <Route path="/" element={<Review />} />
            <Route path="/activity" element={<section><div className="eyebrow">WORKSPACE</div>
              <h1>Activity</h1><div className="empty-state"><Activity size={30} />
                <h2>No reviews yet</h2><span>Analysis history is not available in this preview.</span></div></section>} />
            <Route path="/settings" element={<section><div className="eyebrow">WORKSPACE</div>
              <h1>Settings</h1><dl className="settings-list"><dt>API endpoint</dt>
                <dd>{apiOrigin || 'Same-origin /api proxy'}</dd><dt>Submission</dt><dd>Disabled</dd>
                <dt>Environment</dt><dd>Development preview</dd></dl></section>} />
            <Route path="*" element={<section><h1>Page not found</h1><NavLink to="/">Return to review</NavLink></section>} />
          </Routes>
        </main>
        <footer className="page-footer">Human review required. Not legal advice.</footer>
      </div>
    </div>
  );
}

function Review() {
  return <section>
    <div className="eyebrow">DOCUMENT REVIEW</div>
    <div className="heading-row"><h1>New review</h1><span className="preview-label">Preview</span></div>
    <div className="document-heading"><h2>Document</h2><span><LockKeyhole size={14} />Submission disabled</span></div>
    <div className="document-toolbar"><span><FileText size={17} />Filing text</span>
      <button className="secondary-button" disabled>Upload PDF</button></div>
    <label className="sr-only" htmlFor="filing">Filing text</label>
    <textarea id="filing" disabled placeholder="Document intake is not available in this preview." />
    <div className="document-bottom"><span>No document selected</span>
      <button className="primary-button" disabled>Run review<ArrowRight size={17} /></button></div>
    <div className="review-status"><h2>Review status</h2>
      <div><span>Authorities</span><span>Not run</span></div>
      <div><span>Propositions & quotations</span><span>Not run</span></div>
      <div><span>Privacy & court requirements</span><span>Not run</span></div>
    </div>
  </section>;
}
