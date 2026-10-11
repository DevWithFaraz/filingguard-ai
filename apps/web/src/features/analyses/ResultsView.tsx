import { useMutation, useQuery } from '@tanstack/react-query';
import { Background, Controls, ReactFlow, type Node } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { ArrowLeft, ArrowRight, Check, ChevronRight, Download, FileText, ShieldCheck } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useParams } from 'react-router';
import { downloadReport, getEvidence, getGraph, getResults, safeSourceURL,
  type ResultFinding, type ReviewGraph } from '../../lib/api/results';
import './results.css';
import { WorkflowHero } from '../../components/layout/WorkflowShell';

const severityOrder: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };
function label(value: string) { return value.replaceAll('_', ' '); }

function EvidenceDetail({ analysisId, finding }: { analysisId: string; finding: ResultFinding }) {
  const panel = useRef<HTMLElement>(null);
  useEffect(() => {
    panel.current?.focus({ preventScroll: true });
    panel.current?.scrollIntoView?.({ block: 'nearest' });
  }, [finding.id]);
  const query = useQuery({ queryKey: ['finding-evidence', analysisId, finding.id],
    queryFn: ({ signal }) => getEvidence(analysisId, finding.id, signal), retry: false, gcTime: 0 });
  return <section ref={panel} tabIndex={-1} className="result-detail" aria-labelledby="finding-detail-title">
    <a className="document-text-link" href="#findings-title"><ArrowLeft size={15} />Back to findings</a>
    <span className={`result-badge severity-${finding.severity}`}>{finding.severity}</span>
    <h2 id="finding-detail-title">{finding.title}</h2><p>{finding.description}</p>
    {finding.masked_excerpt && <><h3>Filing excerpt</h3><blockquote>{finding.masked_excerpt}</blockquote>
      {finding.start !== null && <small>Original span {finding.start}–{finding.end} · Unicode code points</small>}</>}
    <p className="result-limitation">{finding.ai_assisted ? 'AI assisted review; inspect the source and uncertainty.' : 'Deterministic or heuristic check; inspect its method and scope.'}</p>
    {query.isPending && <p role="status">Loading finding evidence</p>}
    {query.isError && <p role="alert">Evidence unavailable. <button className="secondary-button" onClick={() => void query.refetch()}>Retry evidence</button></p>}
    {query.data && <><h3>Evidence ({query.data.evidence.length})</h3>
      {!query.data.evidence.length && <p>No stored evidence is available for this finding.</p>}
      {query.data.evidence.map(item => <article className="result-evidence" key={item.id}>
        <blockquote>{item.excerpt}</blockquote>
        {item.source_url && safeSourceURL(item.source_url) && <a href={item.source_url} target="_blank" rel="noreferrer">Open source <span className="sr-only">in a new tab</span></a>}
        <dl><dt>Provenance</dt><dd>{label(item.provenance)}</dd><dt>Method</dt><dd>{item.method_version}</dd>
          <dt>Source span</dt><dd>{item.source_start}–{item.source_end} · Unicode code points</dd>
          <dt>Retrieved</dt><dd>{new Date(item.retrieved_at).toLocaleString()}</dd>
          <dt>Snapshot SHA-256</dt><dd className="result-hash">{item.source_sha256}</dd>
          {item.model_version && <><dt>Model</dt><dd>{item.model_version}</dd></>}
          {item.prompt_version && <><dt>Prompt</dt><dd>{item.prompt_version}</dd></>}</dl>
      </article>)}</>}
    <p className="result-next-action">Next review action: compare the filing and stored source, inspect any missing coverage, and resolve the issue with a qualified reviewer before filing.</p>
  </section>;
}

function EvidenceGraph({ graph, onSelectFinding }: { graph: ReviewGraph; onSelectFinding: (id: string) => void }) {
  const [selected, setSelected] = useState<string | null>(null);
  const { nodes, edges } = useMemo(() => {
    const indices = { section: 0, claim: 0, authority: 0 };
    const columns = { section: 0, claim: 1, authority: 2 };
    const nodes: Node[] = graph.nodes.slice(0, 200).map(item => ({ id: item.id,
      data: { label: `${label(item.kind)} · ${item.label}\n${label(item.status)}` },
      position: { x: columns[item.kind] * 270, y: indices[item.kind]++ * 115 },
      style: { width: 230 }, ariaLabel: `${label(item.kind)} ${item.label}: ${label(item.status)}` }));
    const ids = new Set(nodes.map(node => node.id));
    return { nodes, edges: graph.edges.filter(edge => ids.has(edge.source) && ids.has(edge.target)) };
  }, [graph]);
  function select(id: string) {
    setSelected(id);
    const findingId = graph.nodes.find(node => node.id === id)?.finding_ids?.[0];
    if (findingId) onSelectFinding(findingId);
  }
  const selectedNode = graph.nodes.find(node => node.id === selected);
  return <section className="result-graph" aria-labelledby="graph-title"><h2 id="graph-title">Evidence relationships</h2>
    <p>{graph.nodes.length} stored nodes · {graph.edges.length} relationships. Select a node to inspect its related finding.</p>
    {!graph.nodes.length ? <p>No persisted sections, claims or authorities are available.</p> : <>
      {graph.nodes.length > 200 && <p className="result-limitation">The visual graph shows the first 200 nodes. The list below includes every stored node and relationship.</p>}
      <div className="result-graph-canvas" aria-label="Evidence relationship graph">
        <ReactFlow nodes={nodes} edges={edges} nodesDraggable={false} nodesConnectable={false}
          onNodeClick={(_event, node) => select(node.id)} fitView minZoom={0.15} maxZoom={1.5}
          proOptions={{ hideAttribution: false }}><Background /><Controls showInteractive={false} /></ReactFlow>
      </div>
      <details className="result-graph-list"><summary>Keyboard accessible graph list ({graph.nodes.length} nodes)</summary>
        <ul>{graph.nodes.map(node => <li key={node.id}><button type="button" onClick={() => select(node.id)}
          aria-pressed={selected === node.id}>{label(node.kind)}: {node.label} · {label(node.status)}</button>
          <ul>{graph.edges.filter(edge => edge.source === node.id).map(edge => <li key={edge.id}>
            {edge.label} → {graph.nodes.find(target => target.id === edge.target)?.label}</li>)}</ul></li>)}</ul>
      </details>
      {selectedNode && <p role="status">Selected {label(selectedNode.kind)}: {selectedNode.label}. {label(selectedNode.status)}.
        {!selectedNode.finding_ids?.length && ' No finding is linked to this node.'}</p>}
    </>}
  </section>;
}

export function ResultsView() {
  const { id = '' } = useParams();
  const [typeFilter, setTypeFilter] = useState('all');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const query = useQuery({ queryKey: ['review-results', id], queryFn: ({ signal }) => getResults(id, signal),
    retry: false, gcTime: 0, refetchInterval: state => ['queued', 'running'].includes(state.state.data?.status ?? '') ? 1500 : false });
  const graph = useQuery({ queryKey: ['review-graph', id, query.data?.status],
    queryFn: ({ signal }) => getGraph(id, signal), enabled: !!query.data, retry: false, gcTime: 0 });
  const report = useMutation({ mutationFn: (format: 'markdown' | 'html') => downloadReport(id, format), retry: false });
  if (query.isPending) return <section className="results-view"><WorkflowHero eyebrow="OPENING YOUR SAVED REVIEW" title="Review results" description="Loading the private findings, coverage and evidence for this document." /><p className="workflow-notice" role="status">Loading private review results</p></section>;
  if (query.isError) return <section className="results-view"><WorkflowHero eyebrow="RECONNECT TO YOUR REVIEW" title="Results unavailable" description="This saved review could not be opened. Retry the request or return to your document to check its status." /><div className="workflow-notice" role="alert">{query.error.message}</div>
    <div className="workflow-actions results-bottom-actions"><button className="secondary-button" onClick={() => void query.refetch()}>Retry results</button><Link className="document-text-link" to={`/analyses/${id}`}>Back to document and review progress<ArrowRight size={15} /></Link></div></section>;
  const results = query.data;
  const coverage = results.coverage;
  const incomplete = results.status !== 'completed' || coverage.unavailable > 0 || coverage.pending > 0 || coverage.truncated;
  const selectedFinding = results.findings.find(item => item.id === selectedId);
  const filtered = results.findings.filter(item => (typeFilter === 'all' || item.type === typeFilter)
    && (severityFilter === 'all' || item.severity === severityFilter))
    .sort((a, b) => (severityOrder[a.severity] ?? 5) - (severityOrder[b.severity] ?? 5));
  const critical = results.findings.filter(item => item.severity === 'critical').length;
  return <section className="results-view"><nav className="document-steps" aria-label="Review steps"><Link to="/"><span><Check size={14} /></span><div>01 <strong>Prepare document</strong></div></Link><ChevronRight size={16} />
    <Link to={`/analyses/${id}`}><span><Check size={14} /></span><div>02 <strong>Review checks</strong></div></Link><ChevronRight size={16} /><a href="#results-overview" aria-current="step"><span>3</span><div>03 <strong>Explore results</strong></div></a></nav>
    <WorkflowHero eyebrow="SAVED REVIEW · STEP 03" title="Review results" description="Evidence in view. Judgment in your hands. Inspect the findings, compare their sources and take a saved report with you.">
      <div className="workflow-hero-note"><ShieldCheck size={28} /><strong>{results.findings.length} findings to inspect</strong><span>{results.document_name}</span><a className="secondary-button" href="#findings-title">Inspect findings<ArrowRight size={16} /></a></div></WorkflowHero>
    <div className="results-heading"><span className="demo-label">{results.mode === 'demo' ? 'Synthetic demo · cached public sources' : 'Private review'}</span><p className="result-limitation">{new Date(results.created_at).toLocaleString()} · Court profile: {results.court_profile_id}</p></div>
    <nav className="results-jump-nav" aria-label="Results sections"><a href="#results-overview">Overview</a><a href="#findings-title">Findings</a><a href="#result-checks">Source checks</a><a href="#result-relationships">Relationships</a><a href="#result-report">Report<Download size={14} /></a></nav>
    <div className={`results-coverage-notice ${incomplete ? 'incomplete' : ''}`} role="status" aria-live="polite">
      <strong>{incomplete ? 'Incomplete review' : 'Review checks completed'} · {label(results.status)}</strong>
      <p>{coverage.evaluated} of {coverage.eligible} eligible checks evaluated · {coverage.unavailable} unavailable · {coverage.pending} pending.</p>
      {coverage.truncated && <p>Processing was bounded. {coverage.limitation}</p>}
      {!coverage.eligible && <p>No applicable checks have been evaluated. Absence of results is not a pass.</p>}
      <p>{results.limitation}</p>
    </div>
    {critical > 0 && <p role="alert" className="results-critical">{critical} critical finding{critical === 1 ? ' requires' : 's require'} attention. Critical findings appear first below.</p>}
    <div id="results-overview" className="results-summary"><article className="result-score"><h2>Filing integrity signal</h2>
      <p className="result-score-number">{results.score.value === null ? 'Unknown' : `${results.score.value}/100`}</p>
      <p>{results.score.risk_level ? label(results.score.risk_level) : 'No risk label available'} · Provisional</p>
      <p className="result-limitation">{results.score.limitation}</p>
      <p>A review signal; this score does not certify filing safety.</p>
      {!!results.score.categories?.length && <div className="result-category-scores" aria-label="Category signals">
        <h3>Category signals · Provisional</h3><ul>{results.score.categories.map(category => <li key={category.type}>
          <strong>{label(category.type)}</strong><span>{category.value === null ? 'Unknown' : `${category.value}/100`}</span>
          <small>{category.evaluated}/{category.eligible} evaluated · {category.deducted_points} points deducted</small>
        </li>)}</ul></div>}
      <details><summary>Score deductions ({results.score.deductions.length})</summary><ul>
        {results.score.deductions.map((item, index) => <li key={`${item.finding_id}-${index}`}>
          <button onClick={() => setSelectedId(item.finding_id)}>{results.findings.find(finding => finding.id === item.finding_id)?.title ?? label(item.type)}</button>
          {' '}−{item.points} · {item.severity}</li>)}</ul><small>Scoring method: {results.score.version}</small></details>
    </article><article className="result-stage-summary"><h2>Stage coverage</h2><ol>{results.stages.map(stage => <li key={stage.name}>
      <strong>{label(stage.name)}</strong><span>{label(stage.status)} · {stage.coverage.evaluated}/{stage.coverage.eligible} evaluated</span>
      {stage.reason && <small>{stage.reason}</small>}</li>)}</ol></article></div>
    <section aria-labelledby="findings-title"><div className="results-section-heading"><h2 id="findings-title">Findings ({results.findings.length})</h2>
      <div className="results-filters"><label>Finding category<select value={typeFilter} onChange={event => setTypeFilter(event.target.value)}>
        <option value="all">All categories</option>{['citation', 'claim_support', 'quote', 'privacy', 'court_rule', 'system'].map(value => <option value={value} key={value}>{label(value)}</option>)}</select></label>
        <label>Finding severity<select value={severityFilter} onChange={event => setSeverityFilter(event.target.value)}><option value="all">All severities</option>
          {['critical', 'high', 'medium', 'low', 'info'].map(value => <option key={value} value={value}>{value}</option>)}</select></label></div></div>
      <div className="results-findings-layout"><div><p className="sr-only" role="status">{filtered.length} findings match the filters</p>
        {!filtered.length && <p>{results.findings.length ? 'No findings match these filters.' : 'No findings were recorded. Inspect coverage before drawing conclusions.'}</p>}
        <ul className="results-finding-list">{filtered.map(item => <li key={item.id}><button aria-pressed={selectedId === item.id}
          className="result-finding-button" onClick={() => setSelectedId(item.id)}><span className={`result-badge severity-${item.severity}`}>{item.severity}</span>
          <strong>{item.title}</strong><small>{label(item.type)} · {item.evidence_count} evidence record{item.evidence_count === 1 ? '' : 's'}</small></button></li>)}</ul></div>
        {selectedFinding ? <EvidenceDetail key={selectedFinding.id} analysisId={id} finding={selectedFinding} /> : <aside className="result-detail result-detail-empty"><FileText size={26} /><p>Select a finding to inspect its filing excerpt, source evidence and review method.</p></aside>}
      </div>
    </section>
    <section id="result-checks" className="results-checks" aria-label="Citation, claim and quotation outcomes"><div className="results-section-heading"><h2>Inspect the source checks</h2><p className="result-limitation">Expand a category to examine the saved outcomes.</p></div>
      <details><summary>Citation occurrences ({results.citations.length})</summary><ul>{results.citations.map(item => <li key={item.id}>
        <strong>{item.masked_raw_text}</strong> · {label(item.verification_status)}<p>{item.reason}</p>{item.limitation && <p>{item.limitation}</p>}
        <small>Span {item.location.start}–{item.location.end}{item.location.page_number ? ` · Page ${item.location.page_number}` : ''}</small></li>)}</ul></details>
      <details><summary>Extracted claims ({results.claims.length})</summary><ul>{results.claims.map(item => <li key={item.id}><p>{item.text}</p>
        <small>{label(item.extraction_method)} extraction · Span {item.location.start}–{item.location.end}</small>
        {!item.links.length && <p>No authority links were available.</p>}
        <ul>{item.links.map(link => <li key={link.id}><strong>{label(link.support_status)}</strong><p>{link.explanation ?? 'No support explanation is available.'}</p></li>)}</ul></li>)}</ul></details>
      <details><summary>Quotation checks ({results.quotes.length})</summary><ul>{results.quotes.map(item => <li key={item.id}><blockquote>{item.text}</blockquote>
        <p>{label(item.match_status)}{item.similarity !== null ? ` · String similarity ${Math.round(item.similarity * 100)}%` : ''}</p>
        {item.closest_passage && <><h3>Closest source passage</h3><blockquote>{item.closest_passage}</blockquote></>}
        <small>Span {item.location.start}–{item.location.end}. String similarity does not establish equivalent meaning or legal support.</small></li>)}</ul></details>
    </section>
    <div id="result-relationships">{graph.isPending && <p role="status">Loading evidence relationships</p>}
    {graph.isError && <p role="alert">Graph unavailable. <button className="secondary-button" onClick={() => void graph.refetch()}>Retry graph</button></p>}
    {graph.data && <EvidenceGraph graph={graph.data} onSelectFinding={setSelectedId} />}</div>
    <section id="result-report" className="results-export"><div><span className="document-kicker">TAKE THE EVIDENCE WITH YOU</span><h2>Saved-result report</h2><p>Export this review and its stored evidence. No new classification is performed.</p></div>
      <button className="secondary-button" onClick={() => report.mutate('markdown')} disabled={report.isPending}><Download size={16} />Download Markdown</button>
      <button className="secondary-button" onClick={() => report.mutate('html')} disabled={report.isPending}><Download size={16} />Download HTML</button>
      {report.isPending && <p role="status">Preparing authenticated report download</p>}
      {report.isError && <p role="alert">Report unavailable. {report.error.message}</p>}
    </section><div className="workflow-actions results-bottom-actions"><Link className="secondary-button" to={`/analyses/${id}`}><ArrowLeft size={16} />Back to document and review status</Link><Link className="document-text-link" to="/activity">View all documents<ArrowRight size={16} /></Link></div>
  </section>;
}
