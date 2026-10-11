import { useQuery } from '@tanstack/react-query';
import { ArrowRight, Clock3, FileText, RefreshCw } from 'lucide-react';
import { Link } from 'react-router';
import { getActivity, getCapabilities } from '../../lib/api/intake';
import { StartReviewLink, WorkflowHero } from '../../components/layout/WorkflowShell';

export function ActivityView() {
  const capabilities = useQuery({ queryKey: ['capabilities'], queryFn: ({ signal }) => getCapabilities(signal), retry: false });
  const query = useQuery({ queryKey: ['private-activity'], queryFn: ({ signal }) => getActivity(signal),
    enabled: capabilities.data?.intake_enabled === true, retry: false, staleTime: 0, gcTime: 0,
    refetchInterval: 60000 });
  return <section className="workflow-activity"><WorkflowHero eyebrow="THIS TAB’S DOCUMENTS" title="Activity" description="Pick up where you left off. Your temporary session keeps preparation, progress and saved reviews together.">
    <div className="workflow-hero-note"><Clock3 size={28} /><strong>A temporary workspace.</strong><span>Documents belong to this browser tab and remain available until expiry.</span></div></WorkflowHero>
    <div className="workflow-list-heading"><div><h2>Your documents</h2><p>{query.data?.length ?? 0} available in this session</p></div><StartReviewLink /></div>
    {capabilities.isError && <div className="workflow-notice" role="alert"><p>Session availability could not be confirmed.</p><button className="secondary-button" onClick={() => void capabilities.refetch()}>Retry availability</button></div>}
    {capabilities.isPending && <p role="status">Checking private session availability</p>}
    {query.isFetching && <p role="status">Loading private session</p>}
    {query.isError && <p role="alert">{query.error.message}<button className="secondary-button" onClick={() => void query.refetch()}>Retry</button></p>}
    {capabilities.data && (!query.data || !query.data.length) && !query.isFetching && !query.isError
      && <div className="workflow-empty"><FileText size={35} /><h2>No reviews yet</h2><p>{capabilities.data.intake_enabled ? 'Prepare your first document to see it here. Try the synthetic demo to explore the workflow.' : 'Document preparation is currently disabled. You can still explore the reviewed sample.'}</p><div className="workflow-actions"><Link className="secondary-button" to="/demo">Explore sample<ArrowRight size={16} /></Link><Link to="/" className="document-text-link">New document<ArrowRight size={16} /></Link></div></div>}
    <ul className="activity-list">{!query.isError && query.data?.map(value => <li key={value.analysis_id}>
      <div className="activity-document-icon"><FileText size={22} /></div><div className="activity-document-body"><Link to={`/analyses/${value.analysis_id}`}>{value.document_name}<ArrowRight size={16} /></Link>
        <p>{value.mode === 'demo' ? 'Synthetic demo' : 'Private document'} · {value.paragraph_count} paragraphs · Expires {new Date(value.expires_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p></div>
      <span className="workflow-status">{value.execution_status === 'not_run' ? 'Prepared · checks not run' : value.execution_status.replaceAll('_', ' ')}</span></li>)}</ul>
    {!!query.data?.length && <button className="document-text-link" onClick={() => void query.refetch()} disabled={query.isFetching}><RefreshCw size={15} />Refresh documents</button>}
  </section>;
}
