import { useMutation, useQuery } from '@tanstack/react-query';
import { Activity, ArrowLeft, ArrowRight, Check, ChevronRight, FileText, LockKeyhole, LoaderCircle, RotateCcw, ShieldCheck, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router';
import { deletePrepared, getPrepared, getReviewStatus, getSafeFindings, prepareRerun, runLocalReview } from '../../lib/api/intake';
import { reviewPollInterval } from './reviewPolling';
export function PreparedView() {
  const { id = '' } = useParams();
  const navigate = useNavigate();
  const query = useQuery({ queryKey: ['prepared', id], queryFn: ({ signal }) => getPrepared(id, signal), retry: false, gcTime: 0 });
  const review = useQuery({ queryKey: ['review-status', id], queryFn: ({ signal }) => getReviewStatus(id, signal),
    retry: false, gcTime: 0, refetchInterval: state => reviewPollInterval(
      state.state.data?.status, !!state.state.error, state.state.fetchFailureCount) });
  const active = review.data?.status === 'queued' || review.data?.status === 'running';
  const evaluatedChecks = review.data?.stages?.filter(stage => stage.name !== 'document')
    .reduce((count, stage) => count + (stage.coverage?.evaluated ?? 0), 0) ?? 0;
  const findings = useQuery({ queryKey: ['review-findings', id,
    review.data?.stages?.map(stage => stage.status).join(',')], queryFn: ({ signal }) => getSafeFindings(id, signal),
    enabled: review.data?.status !== 'not_run' && !!review.data, retry: false, gcTime: 0,
    refetchInterval: active ? 1000 : false });
  const run = useMutation({ mutationFn: () => runLocalReview(id), retry: false,
    onSuccess: () => { void review.refetch(); } });
  const rerun = useMutation({ mutationFn: () => prepareRerun(id), retry: false,
    onSuccess: value => navigate(`/analyses/${value.analysis_id}`) });
  const [now, setNow] = useState(Date.now);
  useEffect(() => {
    if (!query.data) return;
    const timer = window.setTimeout(() => setNow(Date.now()),
      Math.max(0, Date.parse(query.data.expires_at) - Date.now() + 1));
    return () => window.clearTimeout(timer);
  }, [query.data]);
  const deletion = useMutation({ mutationFn: () => deletePrepared(id), retry: false,
    onSuccess: () => { navigate('/'); } });
  if (query.isPending) return <><section className="document-state" role="status" aria-live="polite"><LoaderCircle className="spinning" /><h1>Opening your document</h1><p>Loading the private preparation and review status.</p></section></>;
  if (query.isError) return <><section className="document-state"><FileText /><h1>Document unavailable</h1><p role="alert">{query.error.message}</p>
    <button className="secondary-button" onClick={() => void query.refetch()}>Retry</button><Link to="/">New document</Link></section></>;
  const value = query.data;
  if (Date.parse(value.expires_at) <= now) return <><section className="document-state"><LockKeyhole /><h1>Document expired</h1>
    <Link to="/">New document</Link></section></>;
  const terminal = !!review.data && ['completed', 'partial', 'failed', 'interrupted'].includes(review.data.status);
  return <><section className="prepared-view">
    <div className="document-wayfinding"><Link to="/"><ArrowLeft size={15} />Back to home</Link><span>YOUR REVIEW WORKSPACE</span></div>
    <nav className="document-steps" aria-label="Review steps"><Link to="/"><span><Check size={14} /></span><div>01 <strong>Prepare document</strong></div></Link>
      <ChevronRight size={16} /><a href="#local-review" aria-current="step"><span>2</span><div>02 <strong>Review checks</strong></div></a>
      <ChevronRight size={16} />{terminal ? <Link to={`/analyses/${id}/results`}><span>3</span><div>03 <strong>Explore results</strong></div></Link>
        : <div className="step-upcoming" aria-disabled="true"><span>3</span><div>03 <strong>Explore results</strong></div></div>}</nav>
    <div className="prepared-hero"><div><div className="document-kicker"><span />{value.mode === 'demo' ? 'CURATED DEMO' : 'PRIVATE DOCUMENT'} · STEP 02</div>
      <h1>{active ? 'A closer look.\nIn progress.' : terminal ? 'Your review.\nReady to explore.' : 'Ready for\na closer look.'}</h1>
      <p>{active ? 'Follow each check as it runs. You can inspect the prepared text while you wait.' : terminal ? 'Inspect what was checked, what needs attention, and the evidence behind each finding.' : 'Your document is prepared. Check the extraction, then start the review when you’re ready.'}</p>
      <a className="hero-document-link" href="#document-preview"><FileText size={17} /><span>{value.document_name}</span><ArrowRight size={16} /></a></div>
      <aside className="next-action-card"><div className="next-action-icon"><ShieldCheck size={26} /></div><span className="document-kicker">YOUR NEXT STEP</span>
        <h2>{active ? 'Review in progress' : terminal ? 'Explore the evidence' : 'Start your review'}</h2>
        <p>{active ? 'Stage status updates automatically. Results become available when this attempt ends.' : terminal ? 'The attempt has ended. Results include coverage, limitations and findings requiring human judgment.' : 'Local checks examine the prepared text. Source and model checks depend on availability and configuration.'}</p>
        {review.data?.status === 'not_run' && <button className="primary-button" disabled={run.isPending || review.isFetching} onClick={() => run.mutate()}>
          {run.isPending ? <LoaderCircle size={17} className="spinning" /> : <ShieldCheck size={17} />}Run local checks<ArrowRight size={17} /></button>}
        {active && <a className="secondary-button" href="#local-review"><LoaderCircle size={16} className="spinning" />Follow review progress</a>}
        {terminal && <Link className="primary-button" to={`/analyses/${id}/results`}>Open review results<ArrowRight size={17} /></Link>}
        {!review.data && <a className="secondary-button" href="#local-review">Check review status<ArrowRight size={16} /></a>}
        <small><LockKeyhole size={12} />Temporary, private to this browser tab</small></aside></div>
    <div className="document-overview"><div><FileText size={18} /><span>Document<strong>{value.document.paragraphs.length} paragraphs</strong></span></div>
      <div><ShieldCheck size={18} /><span>Masking signals<strong>{value.masking_count} detected</strong></span></div>
      <div><Activity size={18} /><span>Checks evaluated<strong>{evaluatedChecks} local checks</strong></span></div>
      <a href="#document-details"><LockKeyhole size={18} /><span>Available until<strong>{new Date(value.expires_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</strong></span><ChevronRight size={14} /></a></div>
    {value.mode === 'demo' && <p className="review-limitation">Cached public opinions for the exact curated sample.
      Findings are freshly computed; model review depends on provider configuration. AI-reviewed sample, not expert validation.</p>}
    <div className="demo-notice" role="status" aria-live="polite">{(review.data?.status ?? value.execution_status) === 'not_run'
      ? 'Document prepared. Local checks have not run. No legal analysis or filing integrity score.'
      : `Review status: ${review.data?.status ?? value.execution_status}. ${review.data?.overall_score == null
        ? 'No filing integrity score.' : `Provisional review score: ${review.data.overall_score}. Human review required.`}`}</div>
    {run.isPending && <p className="sr-only" role="status" aria-live="polite">Starting local review checks…</p>}
    {rerun.isPending && <p className="sr-only" role="status" aria-live="polite">Preparing new review attempt…</p>}
    {deletion.isPending && <p className="sr-only" role="status" aria-live="polite">Deleting document…</p>}
    <section id="local-review" className="local-review" aria-labelledby="local-review-heading">
      <div className="local-review-heading"><h2 id="local-review-heading"><ShieldCheck size={18} />Local review</h2>
        <a className="document-text-link" href="#document-preview">Inspect document<ArrowRight size={15} /></a>
        {value.mode === 'live' && review.data && ['completed', 'partial', 'failed', 'interrupted'].includes(review.data.status)
          && <button className="secondary-button" disabled={rerun.isPending} onClick={() => rerun.mutate()}>
            <RotateCcw size={16} />New attempt</button>}</div>
      {review.isError && <p role="alert">Status unavailable. {review.error.message}
        <button className="secondary-button" onClick={() => void review.refetch()}>Retry status</button></p>}
      {(run.isError || rerun.isError) && <p role="alert">{run.error?.message || rerun.error?.message}</p>}
      {review.data && <><p role="status" aria-live="polite">{active ? 'Review in progress' : `Review ${review.data.status.replaceAll('_', ' ')}`}
        {` · ${evaluatedChecks} local checks evaluated`}</p>
        <ol className="stage-list">{review.data.stages?.filter(stage => stage.name !== 'document').map(stage =>
          <li key={stage.name}><strong>{stage.name.replaceAll('_', ' ')}</strong><span>{stage.status.replaceAll('_', ' ')}
            {stage.reason ? ` · ${stage.reason}` : ''}</span></li>)}</ol></>}
      {findings.isError && <p role="alert">Findings unavailable. <button className="secondary-button"
        onClick={() => void findings.refetch()}>Retry findings</button></p>}
      {findings.isPending && review.data?.status !== 'not_run' && <p className="sr-only" role="status" aria-live="polite">Loading review findings…</p>}
      {findings.data && <details className="document-findings"><summary>Findings ({findings.data.findings.length}) · expand to inspect</summary>
        <p className="review-limitation">{findings.data.limitation}</p>
        <ul className="finding-list">{findings.data.findings.map(item => <li key={item.id}>
          <div><strong>{item.title}</strong><span>{item.severity}</span></div>
          <p>{item.description}</p>{item.masked_excerpt && <blockquote>{item.masked_excerpt}</blockquote>}
        </li>)}</ul></details>}
    </section>
    <details id="document-details" className="document-details"><summary><span>Preparation details</span><span>Extraction, privacy & retention</span></summary>
    <dl className="settings-list"><dt>Extraction</dt><dd>{value.document.method}</dd>
      <dt>Paragraphs</dt><dd>{value.document.paragraphs.length}</dd>
      <dt>Page coverage</dt><dd>{value.document.pages.length ? `${value.document.pages.length} PDF pages` : 'Pasted text; no page numbers'}</dd>
      <dt>Court profile</dt><dd>{value.court_profile_id === 'synthetic-demo-v1' ? 'Synthetic demo court' : value.court_profile_id === 'us-txnd-lr7-2f-v1' ? 'N.D. Tex. LR 7.2(f)' : 'Rules unavailable'}</dd>
      <dt>AI used</dt><dd>{value.ai_used ? 'Yes' : 'No'}</dd>
      <dt>Expiry</dt><dd>{new Date(value.expires_at).toLocaleString()}</dd>
      <dt>Local masking signals</dt><dd>{value.masking_count}. {value.masking_limitation}
        {(review.data?.status ?? value.execution_status) === 'not_run' ? ' No provider request sent.' : ''}</dd></dl></details>
    {value.document.pages.filter(page => page.warning).map(page => <p key={page.page_number} className="demo-notice">
      Page {page.page_number}: {page.warning?.replaceAll('_', ' ')}. Review extraction or paste the missing text.</p>)}
    <section id="document-preview" className="document-preview"><div className="preview-heading"><div><span className="document-kicker">THE PREPARED TEXT · {value.mode === 'demo' ? <span className="demo-label">Demo</span> : 'PRIVATE'}</span><h2><FileText size={17} />{value.document_name}</h2></div><a href="#local-review" className="document-text-link">Back to checks<ArrowRight size={15} /></a></div>
    <h3 className="sr-only">Extracted paragraphs</h3>
    <p className="preview-description">Inspect the text used for this review. Check any extraction gaps before relying on the findings.</p>
    <ol className="paragraph-list" tabIndex={0} aria-label="Prepared document paragraphs">{value.document.paragraphs.map(paragraph => <li key={paragraph.paragraph_index}>
      <small>{paragraph.page_number ? `Page ${paragraph.page_number} | ` : ''}Span {paragraph.start}-{paragraph.end} (Unicode code points)</small>
      <p>{paragraph.text}</p></li>)}</ol></section>
    {deletion.isError && <p role="alert">{deletion.error.message}</p>}
    <div className="document-bottom"><Link to="/" className="secondary-button"><ArrowLeft size={16} />New document</Link>
      {value.mode === 'demo' && <button className="secondary-button" disabled={deletion.isPending || active}
        onClick={() => deletion.mutate()}><RotateCcw size={16} />Reset demo</button>}
      <button className="secondary-button" disabled={deletion.isPending}
        onClick={() => { if (window.confirm('Delete this private document and its saved extraction?')) deletion.mutate(); }}>
        <Trash2 size={16} />{deletion.isPending ? 'Deleting' : 'Delete document'}</button></div>
  </section></>;
}
