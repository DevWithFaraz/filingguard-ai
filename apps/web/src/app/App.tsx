import { useQuery } from '@tanstack/react-query';
import { ArrowRight, FileQuestion, RefreshCw } from 'lucide-react';
import { Link, Route, Routes, useLocation, useNavigate } from 'react-router';
import { getHealth } from '../lib/api/client';
import { DemoReview } from '../features/intake/DemoReview';
import { HomePage } from '../features/home/HomePage';
import { PreparedView } from '../features/intake/PreparedView';
import { ActivityView } from '../features/intake/ActivityView';
import { ResultsView } from '../features/analyses/ResultsView';
import { WorkflowHero, WorkflowShell } from '../components/layout/WorkflowShell';
import { SettingsView, PrivacyView } from './WorkspaceInfo';

export function App() {
  const location = useLocation();
  const navigate = useNavigate();
  const health = useQuery({ queryKey: ['health'], queryFn: ({ signal }) => getHealth(signal), refetchInterval: 30000 });
  if (location.pathname === '/') return <HomePage health={health} />;
  return <WorkflowShell connection={<div className="connection" role="status" aria-live="polite"><span className={`status-dot ${health.isSuccess ? 'online' : ''}`} />
    {health.isPending ? 'Connecting' : health.isError ? 'API unavailable' : 'API connected'}
    <button className="icon-button" aria-label="Refresh API connection" title="Refresh API connection" disabled={health.isFetching}
      onClick={() => void health.refetch()}><RefreshCw size={14} className={health.isFetching ? 'spinning' : ''} /></button></div>}>
    <Routes>
      <Route path="/demo" element={<DemoReview onReset={() => navigate('/')} />} />
      <Route path="/activity" element={<ActivityView />} />
      <Route path="/analyses/:id" element={<PreparedView />} />
      <Route path="/analyses/:id/results" element={<ResultsView />} />
      <Route path="/settings" element={<SettingsView />} />
      <Route path="/privacy" element={<PrivacyView />} />
      <Route path="*" element={<section><WorkflowHero eyebrow="LET’S FIND YOUR WAY" title="Page not found" description="This address doesn’t point to a FilingGuard page. Start a new document or return to your session activity." />
        <div className="workflow-empty"><FileQuestion size={36} /><h2>Choose your next step</h2><div className="workflow-actions"><Link className="primary-button" to="/">Return to review<ArrowRight size={16} /></Link><Link className="secondary-button" to="/activity">Open activity</Link></div></div></section>} />
    </Routes>
  </WorkflowShell>;
}
