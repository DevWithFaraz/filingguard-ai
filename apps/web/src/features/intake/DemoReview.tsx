import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, ArrowRight, ExternalLink, FileText, RefreshCw, Sparkles } from 'lucide-react';
import { getDemo } from '../../lib/api/client';
import { Link } from 'react-router';
import { WorkflowHero } from '../../components/layout/WorkflowShell';

const categories = { citation: 'Citation', proposition: 'Proposition', quote: 'Quotation',
  privacy: 'Privacy', court_rules: 'Court rule' };

export function DemoReview({ onReset }: { onReset: () => void }) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const evidence = useRef<HTMLElement>(null);
  useEffect(() => {
    if (selectedId) {
      evidence.current?.focus({ preventScroll: true });
      evidence.current?.scrollIntoView?.({ block: 'nearest' });
    }
  }, [selectedId]);
  const query = useQuery({ queryKey: ['reviewed-demo'], queryFn: ({ signal }) => getDemo(signal),
    retry: false, gcTime: 0 });
  const demo = !query.isError ? query.data : undefined;
  const selected = demo?.examples.find(item => item.id === selectedId);
  const source = demo?.sources.find(item => item.authority_id === selected?.authority_id);
  return <section className="demo-review">
    <WorkflowHero eyebrow="EXPLORE THE EVIDENCE" title="Reviewed sample" description="A guided look at citation, claim and quotation scenarios. Choose an example to compare the filing with its source.">
      <div className="workflow-hero-note"><Sparkles size={28} /><strong>Learn before you review.</strong><span>These are recorded expectations. Preparing the demo from home runs fresh checks.</span><Link to="/" className="secondary-button">Prepare the demo<ArrowRight size={16} /></Link></div></WorkflowHero>
    <div className="demo-actions">
      <button className="secondary-button" onClick={onReset}><ArrowLeft size={17} />Reset sample</button>
      <span>Analysis not run</span>
    </div>
    <p className="demo-notice">Synthetic filing. AI-reviewed expectations, with conditional judgments.
      Human and legal-expert validation remain pending.</p>
    {query.isPending && <p role="status">Loading reviewed sample...</p>}
    {query.isError && <div role="alert"><p>Reviewed sample unavailable. No results loaded.</p>
      <button className="secondary-button" disabled={query.isFetching} onClick={() => void query.refetch()}>
        <RefreshCw size={17} />Retry sample</button></div>}
    {demo && <>
      <p className="demo-meta">{demo.reviewer} / {demo.reviewed_at} / {demo.fixture_id}</p>
      <div className="demo-layout">
        <div className="demo-filing"><h2><FileText size={17} />Sample filing</h2>
          <pre tabIndex={0} role="region" aria-label="Sample filing text">{demo.document}</pre>
          <details><summary>Document fingerprint</summary><code>{demo.document_sha256}</code></details>
        </div>
        <div className="demo-examples"><h2>Expected scenarios</h2><p className="demo-meta">Select a scenario, then inspect its evidence below.</p>
          <ul className="scenario-list">{demo.examples.map(example => <li key={example.id}>
            <button className="scenario-button" aria-pressed={selectedId === example.id}
              aria-controls={selectedId ? 'demo-evidence' : undefined}
              onClick={() => setSelectedId(example.id)}>
              <span>{example.id.replaceAll('-', ' ')}</span>
              <span>{categories[example.category]} / {example.judgment === 'conditional' ? 'Conditional' : 'Reviewed'}</span>
            </button></li>)}</ul>
        </div>
      </div>
      {selected && <section ref={evidence} tabIndex={-1} id="demo-evidence" className="demo-evidence" aria-label="Selected scenario evidence">
        <h2>{selected.id.replaceAll('-', ' ')}</h2>
        <p>Expected: <strong>{selected.expected_status.replaceAll('_', ' ')}</strong>. Execution: not run.</p>
        {selected.condition && <p className="demo-condition">{selected.condition}</p>}
        {selected.simulation && <p>Simulated dependency: {selected.simulation.replaceAll('_', ' ')}</p>}
        {selected.preconditions && <p>Scenario inputs: {Object.entries(selected.preconditions)
          .map(([key, value]) => `${key}=${String(value)}`).join(', ')}</p>}
        <div className="evidence-columns"><div><h3>Filing excerpt</h3>
          <blockquote>{selected.filing_span.text}</blockquote>
          <small>Text offsets {selected.filing_span.start}-{selected.filing_span.end}, Unicode code points</small>
        </div><div><h3>Source excerpt</h3>
          {selected.source_span ? <><blockquote>{selected.source_span.text}</blockquote>
            <small>Source offsets {selected.source_span.start}-{selected.source_span.end}</small></>
            : <p>No source passage is asserted for this scenario.</p>}
          {source && <><a href={source.source_url} target="_blank" rel="noopener noreferrer">
            {source.case_name}, {source.citation}<ExternalLink size={14} aria-hidden="true" /></a>
            <p className="demo-meta">Cached public source / {source.retrieved_at}</p>
            <details><summary>Source fingerprint</summary><code>{source.sha256}</code></details></>}
        </div></div>
        <p>{selected.reason}</p>
      </section>}
      <details className="demo-limits"><summary>Sample limits</summary>
        <ul>{demo.limitations.map(limit => <li key={limit}>{limit}</li>)}</ul>
      </details>
    </>}
  </section>;
}
