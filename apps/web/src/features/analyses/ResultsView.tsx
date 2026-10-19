import { useMutation, useQuery } from '@tanstack/react-query';
import { Background, Controls, Panel, ReactFlow, ReactFlowProvider, useReactFlow, type Node } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {
  ArrowLeft,
  ArrowRight,
  Check,
  ChevronRight,
  Download,
  FileText,
  GitCommit,
  HelpCircle,
  Maximize2,
  RotateCcw,
  ShieldCheck,
  X,
  ZoomIn,
  ZoomOut,
} from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useParams } from 'react-router';
import { downloadReport, getEvidence, getGraph, getResults, safeSourceURL,
  type FindingEvidence, type ResultFinding, type ReviewGraph } from '../../lib/api/results';
import { ClaimCorrectionForm } from '../findings/ClaimCorrectionForm';
import './results.css';
import { WorkflowHero } from '../../components/layout/WorkflowShell';
import { RedTeamPanel } from '../red-team/RedTeamPanel';
import { FindingQA } from './FindingQA';

const severityOrder: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };
function label(value: string) { return value.replaceAll('_', ' '); }

function getDeterminationDetails(finding: ResultFinding) {
  switch (finding.type) {
    case 'citation':
      return {
        methodName: 'Citation verification & reporter matching',
        description: 'Verified through the citation resolver and CourtListener legal database. Citations are extracted via Eyecite regex patterns, normalized, and checked for reporter volumes and page clusters.',
        limitation: 'Absence from CourtListener indicates an unverified authority, but does not conclusively prove the citation is fabricated. Manual reporter verification is required.',
      };
    case 'quote':
      return {
        methodName: 'Multi-tier quotation forensics',
        description: 'Evaluated using exact string matching, whitespace/punctuation-normalized comparison, RapidFuzz string similarity, and a separate local token-overlap semantic review signal when strings diverge.',
        limitation: 'String similarity measures lexical overlap and does not establish that a quotation preserves original legal meaning. The local semantic signal is uncalibrated and is not exact quotation or legal-meaning proof. Any ellipses, brackets, or wording changes require human inspection.',
      };
    case 'claim_support':
      if (/fact/i.test(finding.title)) {
        return {
          methodName: 'Heuristic filing-versus-source fact comparison',
          description: 'Bounded dates, named parties, and numeric holdings in the filing excerpt were compared with retrieved source passages. This is a separate review signal from proposition support classification and does not invent legal analogies.',
          limitation: 'Heuristic fact matching is an uncalibrated review flag, not a legal determination. Missing source facts are insufficient or unavailable, never a pass. Primary passages require human review.',
        };
      }
      return {
        methodName: 'Grounded proposition semantic analysis',
        description: 'The claim was extracted from surrounding text and evaluated against retrieved authoritative opinion passages using structured generative analysis.',
        limitation: 'AI-assisted classification provides an uncalibrated heuristic review signal, not legal advice or a binding judicial conclusion. Primary source passages must be compared directly.',
      };
    case 'privacy':
      return {
        methodName: 'Deterministic identifier pattern scanning',
        description: 'Scanned using deterministic regular expression patterns for protected personal identifiers (e.g. Social Security numbers, financial accounts, full dates of birth).',
        limitation: 'Pattern heuristics detect standard formats but cannot guarantee detection of non-standard or contextually confidential information. A full pre-filing redaction review is advised.',
      };
    case 'court_rule':
      return {
        methodName: 'Court profile rule compliance',
        description: 'Evaluated against requirements defined in the selected court profile, including mandatory AI-disclosure language and filing length bounds.',
        limitation: 'Court profiles represent documented baseline rules. Specific judges or individual divisions may enforce standing orders not captured in this profile.',
      };
    case 'table_of_authorities':
      return {
        methodName: 'Table of Authorities consistency audit',
        description: 'Detected a Table of Authorities heading, extracted comparable reporter identities from the table and body, and compared them both ways, including listed page leaders when present.',
        limitation: 'Heuristic section bounds and Eyecite coverage can miss short forms, unnamed authorities, and non-reporter entries. This is a document-consistency signal, not a court-rule determination.',
      };
    default:
      return {
        methodName: 'System & intake integrity checks',
        description: 'Evaluated by the document intake pipeline and boundary validators.',
        limitation: 'Inspect filing formatting and processing diagnostics before submission.',
      };
  }
}

function FindingLineageChain({ finding, evidence }: { finding: ResultFinding; evidence: FindingEvidence['evidence'] }) {
  const primary = evidence[0];
  const spanText = finding.start !== null && finding.end !== null
    ? `${finding.start}–${finding.end}`
    : 'Document scope';

  return (
    <div className="lineage-chain-card" aria-label="Evidence lineage chain">
      <div className="lineage-chain-header">
        <GitCommit size={16} className="lineage-icon" />
        <h3>Evidence Lineage Chain</h3>
        <span className="lineage-badge">5 Hops</span>
      </div>
      <p className="lineage-subtitle">
        Document-to-source-to-method chain linking every hop to persisted evidence.
      </p>

      <ol className="lineage-steps">
        <li className="lineage-step">
          <div className="lineage-step-marker">01</div>
          <div className="lineage-step-content">
            <span className="lineage-step-label">Document Span</span>
            <span className="lineage-step-value">Offsets {spanText}</span>
            {finding.masked_excerpt && (
              <blockquote className="lineage-excerpt">{finding.masked_excerpt}</blockquote>
            )}
          </div>
        </li>

        <li className="lineage-step">
          <div className="lineage-step-marker">02</div>
          <div className="lineage-step-content">
            <span className="lineage-step-label">Extraction Target</span>
            <span className="lineage-step-value">{label(finding.type)}</span>
            <small className="lineage-step-hint">
              {finding.type === 'citation' && 'Case citation occurrence'}
              {finding.type === 'quote' && 'Filing quotation passage'}
              {finding.type === 'claim_support' && (/fact/i.test(finding.title) ? 'Filing fact versus source fact' : 'Extracted proposition')}
              {finding.type === 'privacy' && 'Personal data pattern'}
              {finding.type === 'court_rule' && 'Court profile rule'}
              {finding.type === 'table_of_authorities' && 'Table of Authorities entry'}
              {finding.type === 'system' && 'Pipeline boundary'}
            </small>
          </div>
        </li>

        <li className="lineage-step">
          <div className="lineage-step-marker">03</div>
          <div className="lineage-step-content">
            <span className="lineage-step-label">Source Authority</span>
            {primary ? (
              <>
                {primary.source_url && safeSourceURL(primary.source_url) ? (
                  <a href={primary.source_url} target="_blank" rel="noreferrer" className="lineage-source-link">
                    Open official source <ArrowRight size={12} />
                  </a>
                ) : (
                  <span className="lineage-step-value">Stored primary snapshot</span>
                )}
                <span className="lineage-step-hash" title={primary.source_sha256}>
                  SHA: {primary.source_sha256.slice(0, 12)}…
                </span>
                <small className="lineage-step-hint">
                  Offsets {primary.source_start}–{primary.source_end}
                </small>
              </>
            ) : (
              <span className="lineage-step-value">Original filing / rule snapshot</span>
            )}
          </div>
        </li>

        <li className="lineage-step">
          <div className="lineage-step-marker">04</div>
          <div className="lineage-step-content">
            <span className="lineage-step-label">Verification Method</span>
            <span className="lineage-step-value">
              {primary ? primary.method_version : (finding.ai_assisted ? 'AI-assisted analysis' : 'Deterministic evaluation')}
            </span>
            <span className="lineage-step-provenance">
              Provenance: {primary ? label(primary.provenance) : 'deterministic'}
            </span>
            {primary?.model_version && (
              <small className="lineage-step-hint">Model: {primary.model_version}</small>
            )}
          </div>
        </li>

        <li className="lineage-step lineage-step-verdict">
          <div className="lineage-step-marker">05</div>
          <div className="lineage-step-content">
            <span className="lineage-step-label">Finding Verdict</span>
            <div className="lineage-verdict-row">
              <span className={`result-badge severity-${finding.severity}`}>{finding.severity}</span>
              <strong>{finding.title}</strong>
            </div>
          </div>
        </li>
      </ol>
    </div>
  );
}

function EvidenceDetail({ analysisId, finding }: { analysisId: string; finding: ResultFinding }) {
  const panel = useRef<HTMLElement>(null);
  useEffect(() => {
    panel.current?.focus({ preventScroll: true });
    panel.current?.scrollIntoView?.({ block: 'nearest' });
  }, [finding.id]);
  const query = useQuery({ queryKey: ['finding-evidence', analysisId, finding.id],
    queryFn: ({ signal }) => getEvidence(analysisId, finding.id, signal), retry: false, gcTime: 0 });
  const determination = getDeterminationDetails(finding);

  return <section ref={panel} tabIndex={-1} className="result-detail" aria-labelledby="finding-detail-title">
    <a className="document-text-link" href="#findings-title"><ArrowLeft size={15} />Back to findings</a>
    <span className={`result-badge severity-${finding.severity}`}>{finding.severity}</span>
    <h2 id="finding-detail-title">{finding.title}</h2><p>{finding.description}</p>
    {finding.masked_excerpt && <><h3>Filing excerpt</h3><blockquote>{finding.masked_excerpt}</blockquote>
      {finding.start !== null && <small>Original span {finding.start}–{finding.end} · Unicode code points</small>}</>}
    <p className="result-limitation">{finding.ai_assisted ? 'AI assisted review; inspect the source and uncertainty.' : 'Deterministic or heuristic check; inspect its method and scope.'}</p>

    <details className="determination-details">
      <summary className="determination-summary">
        <HelpCircle size={15} />
        <span>How was this determined?</span>
      </summary>
      <div className="determination-body">
        <div className="determination-method-badge">
          <span className={finding.ai_assisted ? 'badge-ai' : 'badge-deterministic'}>
            {finding.ai_assisted ? 'AI-Assisted Evaluation' : 'Deterministic Forensic Check'}
          </span>
          <strong>{determination.methodName}</strong>
        </div>
        <p className="determination-description">{determination.description}</p>
        <div className="determination-uncertainty">
          <strong>Methodology & Uncertainty Disclosure:</strong>
          <p>{determination.limitation}</p>
        </div>
      </div>
    </details>

    <FindingLineageChain finding={finding} evidence={query.data?.evidence ?? []} />

    {query.isPending && <p role="status" aria-live="polite">Loading finding evidence</p>}
    {query.isError && <p role="alert">Evidence unavailable. <button className="secondary-button" onClick={() => void query.refetch()}>Retry evidence</button></p>}
    {query.data && <><h3>Stored Evidence Records ({query.data.evidence.length})</h3>
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

    <FindingQA analysisId={analysisId} finding={finding} />

    <p className="result-next-action">Next review action: compare the filing and stored source, inspect any missing coverage, and resolve the issue with a qualified reviewer before filing.</p>
  </section>;
}

interface EvidenceGraphProps {
  graph: ReviewGraph;
  selectedFindingId: string | null;
  onSelectFinding: (id: string) => void;
  findings: ResultFinding[];
  onDownloadGraph: () => void;
  graphDownloadPending: boolean;
}

function GraphControlsBar({
  onDownloadGraph,
  graphDownloadPending,
}: {
  onDownloadGraph: () => void;
  graphDownloadPending: boolean;
}) {
  const { zoomIn, zoomOut, fitView } = useReactFlow();
  return (
    <Panel position="top-right" className="graph-toolbar" aria-label="Graph viewport controls">
      <button
        type="button"
        className="graph-toolbar-btn"
        onClick={() => void zoomIn({ duration: 300 })}
        title="Zoom in graph (+)"
        aria-label="Zoom in graph"
      >
        <ZoomIn size={14} />
      </button>
      <button
        type="button"
        className="graph-toolbar-btn"
        onClick={() => void zoomOut({ duration: 300 })}
        title="Zoom out graph (-)"
        aria-label="Zoom out graph"
      >
        <ZoomOut size={14} />
      </button>
      <button
        type="button"
        className="graph-toolbar-btn"
        onClick={() => void fitView({ padding: 0.2, duration: 400 })}
        title="Fit graph to view"
        aria-label="Fit graph to view"
      >
        <Maximize2 size={14} />
      </button>
      <button
        type="button"
        className="graph-toolbar-btn"
        onClick={() => void fitView({ padding: 0.1, duration: 300 })}
        title="Reset graph view"
        aria-label="Reset graph view"
      >
        <RotateCcw size={14} />
      </button>
      <button
        type="button"
        className="graph-toolbar-btn"
        onClick={onDownloadGraph}
        disabled={graphDownloadPending}
        title="Download graph as SVG from saved analysis"
        aria-label="Download graph"
      >
        <Download size={14} />
      </button>
    </Panel>
  );
}

function EvidenceGraphInner({
  graph,
  selectedFindingId,
  onSelectFinding,
  findings,
  onDownloadGraph,
  graphDownloadPending,
}: EvidenceGraphProps) {
  const [selectedNodeOverride, setSelectedNodeOverride] = useState<{
    findingId: string | null;
    nodeId: string | null;
  }>({
    findingId: selectedFindingId,
    nodeId: null,
  });

  const selectedNodeId =
    selectedNodeOverride.findingId === selectedFindingId && selectedNodeOverride.nodeId !== null
      ? selectedNodeOverride.nodeId
      : (graph.nodes.find(n => Boolean(selectedFindingId && n.finding_ids?.includes(selectedFindingId)))?.id ?? null);

  const { nodes, edges } = useMemo(() => {
    const indices = { section: 0, claim: 0, authority: 0 };
    const columns = { section: 0, claim: 1, authority: 2 };
    const nodes: Node[] = graph.nodes.slice(0, 200).map(item => {
      const isUnsupported =
        item.kind === 'claim' &&
        (item.status === 'unsupported' ||
          item.status === 'contradicted' ||
          item.status === 'misrepresented' ||
          item.status === 'warning');
      const isLinkedToSelected = Boolean(
        selectedFindingId && item.finding_ids?.includes(selectedFindingId)
      );

      const statusTag = isUnsupported ? '⚠️ UNSUPPORTED' : label(item.status);
      const displayLabel = `${label(item.kind)} · ${item.label}\n${statusTag}`;

      return {
        id: item.id,
        data: { label: displayLabel },
        position: { x: columns[item.kind] * 270, y: indices[item.kind]++ * 115 },
        style: {
          width: 230,
          border: isLinkedToSelected
            ? '2px solid #5d2f96'
            : isUnsupported
              ? '2px solid #e11d48'
              : '1px solid #b395cf',
          background: isLinkedToSelected
            ? '#f3ebfc'
            : isUnsupported
              ? '#fff1f2'
              : '#ffffff',
          color: isUnsupported ? '#9f1239' : '#2b1f3d',
          fontWeight: isUnsupported || isLinkedToSelected ? 600 : 400,
          boxShadow: isLinkedToSelected
            ? '0 0 0 3px rgba(93, 47, 150, 0.25)'
            : isUnsupported
              ? '0 2px 8px rgba(225, 29, 72, 0.12)'
              : '0 2px 6px rgba(0, 0, 0, 0.04)',
          borderRadius: 10,
          padding: 8,
        },
        ariaLabel: isUnsupported
          ? `Warning: Unsupported claim: ${item.label}: ${statusTag}`
          : `${label(item.kind)} ${item.label}: ${label(item.status)}`,
      };
    });
    const ids = new Set(nodes.map(node => node.id));
    return { nodes, edges: graph.edges.filter(edge => ids.has(edge.source) && ids.has(edge.target)) };
  }, [graph, selectedFindingId]);

  function select(id: string) {
    const node = graph.nodes.find(n => n.id === id);
    const findingId = node?.finding_ids?.[0] ?? selectedFindingId;
    setSelectedNodeOverride({ findingId, nodeId: id });
    if (node?.finding_ids?.[0]) {
      onSelectFinding(node.finding_ids[0]);
    }
  }

  const selectedNode = graph.nodes.find(node => node.id === selectedNodeId);
  const citingEdges = selectedNode ? graph.edges.filter(edge => edge.target === selectedNode.id) : [];
  const citingClaims = selectedNode
    ? graph.nodes.filter(n => citingEdges.some(e => e.source === n.id))
    : [];

  return (
    <section className="result-graph" aria-labelledby="graph-title">
      <div className="result-graph-header">
        <div>
          <h2 id="graph-title">Evidence relationships</h2>
          <p>
            {graph.nodes.length} stored nodes · {graph.edges.length} relationships. Select a node to inspect its related finding.
          </p>
        </div>
      </div>
      {!graph.nodes.length ? (
        <p>No persisted sections, claims or authorities are available.</p>
      ) : (
        <>
          {graph.nodes.length > 200 && (
            <p className="result-limitation">
              The visual graph shows the first 200 nodes. The list below includes every stored node and relationship.
            </p>
          )}
          <div className="result-graph-canvas" aria-label="Evidence relationship graph">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              nodesDraggable={false}
              nodesConnectable={false}
              onNodeClick={(_event, node) => select(node.id)}
              fitView
              minZoom={0.15}
              maxZoom={1.5}
              proOptions={{ hideAttribution: false }}
            >
              <Background />
              <Controls showInteractive={true} />
              <GraphControlsBar
                onDownloadGraph={onDownloadGraph}
                graphDownloadPending={graphDownloadPending}
              />
            </ReactFlow>
          </div>
          <details className="result-graph-list">
            <summary>Keyboard accessible graph list ({graph.nodes.length} nodes)</summary>
            <ul>
              {graph.nodes.map(node => {
                const isUnsupported =
                  node.kind === 'claim' &&
                  (node.status === 'unsupported' ||
                    node.status === 'contradicted' ||
                    node.status === 'misrepresented' ||
                    node.status === 'warning');
                const isSelected = selectedNodeId === node.id;
                const nodeEdges = graph.edges.filter(edge => edge.source === node.id);

                return (
                  <li key={node.id}>
                    <button
                      type="button"
                      onClick={() => select(node.id)}
                      aria-pressed={isSelected}
                    >
                      {label(node.kind)}: {node.label} · {label(node.status)}
                      {isUnsupported && ' ⚠️ [Warning: Unsupported claim]'}
                    </button>
                    {nodeEdges.length > 0 && (
                      <ul>
                        {nodeEdges.map(edge => (
                          <li key={edge.id}>
                            {edge.label} → {graph.nodes.find(target => target.id === edge.target)?.label}
                          </li>
                        ))}
                      </ul>
                    )}
                  </li>
                );
              })}
            </ul>
          </details>
          {selectedNode && (
            <div className="result-graph-selection-detail" role="status" aria-live="polite">
              <p>
                Selected {label(selectedNode.kind)}: <strong>{selectedNode.label}</strong>. Status: {label(selectedNode.status)}.
                {!selectedNode.finding_ids?.length && ' No finding is linked to this node.'}
              </p>
              {selectedNode.kind === 'authority' && citingClaims.length > 0 && (
                <div className="graph-authority-claims">
                  <strong>Associated claims ({citingClaims.length}):</strong>
                  <ul>
                    {citingClaims.map(claim => (
                      <li key={claim.id}>
                        <button
                          type="button"
                          className="link-style-btn"
                          onClick={() => select(claim.id)}
                        >
                          {claim.label} (<em>{label(claim.status)}</em>)
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {selectedNode.finding_ids && selectedNode.finding_ids.length > 0 && (
                <div className="graph-linked-findings-bar">
                  <span>Linked findings:</span>
                  <div className="graph-finding-pills">
                    {selectedNode.finding_ids.map(fId => {
                      const f = findings.find(item => item.id === fId);
                      const isCurrent = fId === selectedFindingId;
                      return (
                        <button
                          key={fId}
                          type="button"
                          className={`secondary-button finding-pill-btn ${isCurrent ? 'active' : ''}`}
                          onClick={() => onSelectFinding(fId)}
                        >
                          {f ? `${f.severity.toUpperCase()}: ${f.title}` : fId}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </section>
  );
}

function EvidenceGraph(props: EvidenceGraphProps) {
  return (
    <ReactFlowProvider>
      <EvidenceGraphInner {...props} />
    </ReactFlowProvider>
  );
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
  const report = useMutation({
    mutationFn: (format: 'markdown' | 'html' | 'pdf' | 'graph-svg' | 'graph-png') => downloadReport(id, format),
    retry: false,
  });
  if (query.isPending) return <section className="results-view"><WorkflowHero eyebrow="OPENING YOUR SAVED REVIEW" title="Review results" description="Loading the private findings, coverage and evidence for this document." /><p className="workflow-notice" role="status" aria-live="polite">Loading private review results</p></section>;
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
    <nav className="results-jump-nav" aria-label="Results sections"><a href="#results-overview">Overview</a><a href="#findings-title">Findings</a><a href="#result-checks">Source checks</a><a href="#result-red-team">Red Team</a><a href="#result-relationships">Relationships</a><a href="#result-report">Report<Download size={14} /></a></nav>
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
      {!!results.score.categories?.length && (
        <div className="result-category-scores" aria-label="Category signals">
          <div className="category-scores-header">
            <h3>Category signals · Provisional</h3>
            {typeFilter !== 'all' && (
              <button
                type="button"
                className="category-clear-btn"
                onClick={() => setTypeFilter('all')}
              >
                Show all categories
              </button>
            )}
          </div>
          <ul>
            {results.score.categories.map(category => {
              const isActive = typeFilter === category.type;
              return (
                <li key={category.type}>
                  <button
                    type="button"
                    className={`category-filter-btn ${isActive ? 'active' : ''}`}
                    aria-pressed={isActive}
                    onClick={() => {
                      setTypeFilter(prev => (prev === category.type ? 'all' : category.type));
                      document.getElementById('findings-title')?.scrollIntoView?.({ behavior: 'smooth' });
                    }}
                    title={isActive ? `Clear filter for ${label(category.type)}` : `Filter findings by ${label(category.type)}`}
                  >
                    <div className="category-btn-top">
                      <strong>{label(category.type)}</strong>
                      <span>{category.value === null ? 'Unknown' : `${category.value}/100`}</span>
                    </div>
                    <small>
                      {category.evaluated}/{category.eligible} evaluated · {category.deducted_points} points deducted
                    </small>
                    <span className="category-filter-hint">
                      {isActive ? '✓ Filtering findings' : 'Click to filter'}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      )}
      <details><summary>Score deductions ({results.score.deductions.length})</summary><ul>
        {results.score.deductions.map((item, index) => <li key={`${item.finding_id}-${index}`}>
          <button onClick={() => setSelectedId(item.finding_id)}>{results.findings.find(finding => finding.id === item.finding_id)?.title ?? label(item.type)}</button>
          {' '}−{item.points} · {item.severity}</li>)}</ul><small>Scoring method: {results.score.version}</small></details>
    </article><article className="result-stage-summary"><h2>Stage coverage</h2><ol>{results.stages.map(stage => <li key={stage.name}>
      <strong>{label(stage.name)}</strong><span>{label(stage.status)} · {stage.coverage.evaluated}/{stage.coverage.eligible} evaluated</span>
      {stage.reason && <small>{stage.reason}</small>}</li>)}</ol></article></div>
    <section aria-labelledby="findings-title"><div className="results-section-heading"><h2 id="findings-title">Findings ({results.findings.length})</h2>
      <div className="results-filters"><label>Finding category<select value={typeFilter} onChange={event => setTypeFilter(event.target.value)}>
        <option value="all">All categories</option>{['citation', 'claim_support', 'quote', 'privacy', 'court_rule', 'table_of_authorities', 'system'].map(value => <option value={value} key={value}>{label(value)}</option>)}</select></label>
        <label>Finding severity<select value={severityFilter} onChange={event => setSeverityFilter(event.target.value)}><option value="all">All severities</option>
          {['critical', 'high', 'medium', 'low', 'info'].map(value => <option key={value} value={value}>{value}</option>)}</select></label>
        {typeFilter !== 'all' && (
          <button
            type="button"
            className="secondary-button filter-reset-pill"
            onClick={() => setTypeFilter('all')}
            aria-label="Clear category filter"
          >
            Category: {label(typeFilter)} <X size={12} />
          </button>
        )}
      </div></div>
      <div className="results-findings-layout"><div><p className="sr-only" role="status" aria-live="polite">{filtered.length} findings match the filters</p>
        {!filtered.length && <p>{results.findings.length ? 'No findings match these filters.' : 'No findings were recorded. Inspect coverage before drawing conclusions.'}</p>}
        <ul className="results-finding-list">{filtered.map(item => <li key={item.id}><button aria-pressed={selectedId === item.id}
          className="result-finding-button" onClick={() => setSelectedId(item.id)}><span className={`result-badge severity-${item.severity}`}>{item.severity}</span>
          <strong>{item.title}</strong><small>{label(item.type)} · {item.evidence_count} evidence record{item.evidence_count === 1 ? '' : 's'}</small></button></li>)}</ul></div>
        {selectedFinding ? <EvidenceDetail key={selectedFinding.id} analysisId={id} finding={selectedFinding} /> : <aside className="result-detail result-detail-empty"><FileText size={26} /><p>Select a finding to inspect its filing excerpt, source evidence and review method.</p></aside>}
      </div>
    </section>
    <section id="result-checks" className="results-checks" aria-label="Citation, claim and quotation outcomes"><div className="results-section-heading"><h2>Inspect the source checks</h2><p className="result-limitation">Expand a category to examine the saved outcomes.</p></div>
      <details><summary>Citation occurrences ({results.citations.length})</summary><ul>{results.citations.map(item => <li key={item.id} className="citation-occurrence-item">
        <div className="citation-occurrence-header">
          <strong>{item.masked_raw_text}</strong> · {label(item.verification_status)}
          {item.duplicate_count && item.duplicate_count > 1 && (
            <span className="result-badge badge-duplicate" title={`Appears ${item.duplicate_count} times in filing`}>
              Repeated ({item.duplicate_count}x)
            </span>
          )}
        </div>
        <p>{item.reason}</p>{item.limitation && <p>{item.limitation}</p>}
        <small>Span {item.location.start}–{item.location.end}{item.location.page_number ? ` · Page ${item.location.page_number}` : ''}</small>
        {item.repeated_locations && item.repeated_locations.length > 1 && (
          <div className="citation-repeated-locations">
            <span className="repeated-locs-label">Repeated in filing:</span>
            <ul className="repeated-locs-list">
              {item.repeated_locations.map((loc, idx) => (
                <li key={idx} className="repeated-loc-pill">
                  Span {loc.start}–{loc.end}{loc.page_number ? ` (Page ${loc.page_number})` : ''}
                </li>
              ))}
            </ul>
          </div>
        )}</li>)}</ul></details>
      <details><summary>Extracted claims ({results.claims.length})</summary><ul>{results.claims.map(item => <li key={item.id}>
        <ClaimCorrectionForm analysisId={id} claim={item} />
        <small>{label(item.extraction_method)} extraction · Span {item.location.start}–{item.location.end}</small>
        {!item.links.length && <p>No authority links were available.</p>}
        <ul>{item.links.map(link => <li key={link.id}><strong>{label(link.support_status)}</strong><p>{link.explanation ?? 'No support explanation is available.'}</p></li>)}</ul></li>)}</ul></details>
      <details><summary>Quotation checks ({results.quotes.length})</summary><ul>{results.quotes.map(item => <li key={item.id}><blockquote>{item.text}</blockquote>
        <p>{label(item.match_status)}{item.similarity !== null ? ` · String similarity ${Math.round(item.similarity * 100)}%` : ''}</p>
        {item.closest_passage && <><h3>Closest source passage</h3><blockquote>{item.closest_passage}</blockquote></>}
        <small>Span {item.location.start}–{item.location.end}. String similarity does not establish equivalent meaning or legal support.</small></li>)}</ul></details>
    </section>
    <RedTeamPanel analysisId={id} onSelectFinding={setSelectedId} />
    <div id="result-relationships">{graph.isPending && <p role="status" aria-live="polite">Loading evidence relationships</p>}
    {graph.isError && <p role="alert">Graph unavailable. <button className="secondary-button" onClick={() => void graph.refetch()}>Retry graph</button></p>}
    {graph.data && (
      <EvidenceGraph
        graph={graph.data}
        selectedFindingId={selectedId}
        onSelectFinding={setSelectedId}
        findings={results.findings}
        onDownloadGraph={() => report.mutate('graph-svg')}
        graphDownloadPending={report.isPending}
      />
    )}</div>
    <section id="result-report" className="results-export"><div><span className="document-kicker">TAKE THE EVIDENCE WITH YOU</span><h2>Saved-result report</h2><p>Export this review and its stored evidence. No new classification is performed.</p></div>
      <button className="secondary-button" onClick={() => report.mutate('markdown')} disabled={report.isPending}><Download size={16} />Download Markdown</button>
      <button className="secondary-button" onClick={() => report.mutate('html')} disabled={report.isPending}><Download size={16} />Download HTML</button>
      <button className="secondary-button" onClick={() => report.mutate('pdf')} disabled={report.isPending}><Download size={16} />Download PDF</button>
      {report.isPending && <p role="status" aria-live="polite">Preparing authenticated report download</p>}
      {report.isError && <p role="alert">Report unavailable. {report.error.message}</p>}
    </section><div className="workflow-actions results-bottom-actions"><Link className="secondary-button" to={`/analyses/${id}`}><ArrowLeft size={16} />Back to document and review status</Link><Link className="document-text-link" to="/activity">View all documents<ArrowRight size={16} /></Link></div>
  </section>;
}
