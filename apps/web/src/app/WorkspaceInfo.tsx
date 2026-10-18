import { useQuery } from '@tanstack/react-query';
import { ArrowRight, Clock3, FileText, LockKeyhole, Server, ShieldCheck, SlidersHorizontal } from 'lucide-react';
import { Link } from 'react-router';
import { apiOrigin } from '../lib/api/client';
import { getCapabilities } from '../lib/api/intake';
import { StartReviewLink, WorkflowHero } from '../components/layout/WorkflowShell';

export function SettingsView() {
  const query = useQuery({ queryKey: ['capabilities'], queryFn: ({ signal }) => getCapabilities(signal), retry: false });
  return <section className="workspace-info"><WorkflowHero eyebrow="WORKSPACE AVAILABILITY" title="Settings" description="Know what’s available before you begin. These settings reflect the server’s configuration." >
    <div className="workflow-hero-note"><SlidersHorizontal size={28} /><strong>Your review, in context.</strong><span>Configuration is managed by the server. No account or paid upgrade is required here.</span></div></WorkflowHero>
    {query.isPending && <p className="workflow-notice" role="status" aria-live="polite">Loading service availability</p>}
    {query.isError && <div className="workflow-notice" role="alert"><strong>Availability could not be confirmed.</strong><p>{query.error.message}</p><button className="secondary-button" onClick={() => void query.refetch()}>Retry availability</button></div>}
    <div className="workflow-info-grid"><article className="workflow-card"><FileText size={23} /><h2>Document preparation</h2><span className="workflow-status">{query.data ? query.data.intake_enabled ? 'Available · private sessions' : 'Disabled' : 'Availability unknown'}</span>
      <p>Prepare pasted text, a text-based PDF or the curated synthetic demo. Preparation alone does not run the review.</p><StartReviewLink /></article>
      <article className="workflow-card"><ShieldCheck size={23} /><h2>External review</h2><span className="workflow-status">{query.data ? query.data.legal_analysis_enabled ? 'Enabled for private sessions' : 'Disabled; local checks available' : 'Availability unknown'}</span>
        <p>Individual source and model stages depend on provider configuration. The review’s stage coverage shows what actually ran.</p><Link className="document-text-link" to="/activity">View your reviews<ArrowRight size={15} /></Link></article></div>
    <section className="workflow-card workflow-service-details"><div className="workflow-section-title"><Server size={21} /><h2>Service details</h2></div><dl className="settings-list"><dt>API endpoint</dt><dd>{apiOrigin || 'Same-origin /api proxy'}</dd>
      <dt>Text limit</dt><dd>{query.data ? `${query.data.max_characters.toLocaleString()} Unicode characters` : 'Unconfirmed'}</dd><dt>PDF size limit</dt><dd>{query.data ? `${query.data.max_file_bytes / 1048576} MB` : 'Unconfirmed'}</dd>
      <dt>Environment</dt><dd>Development preview</dd></dl><Link className="document-text-link" to="/privacy">Understand privacy & limits<ArrowRight size={15} /></Link></section>
  </section>;
}

export function PrivacyView() {
  return <section className="workspace-info"><WorkflowHero eyebrow="PRIVACY & REVIEW LIMITS" title="Know the boundaries." description="A clear view of how this development preview handles documents—and where human judgment remains essential.">
    <div className="workflow-hero-note"><LockKeyhole size={28} /><strong>Use public or synthetic text.</strong><span>Confidential client use awaits hosted security and release verification.</span></div></WorkflowHero>
    <div className="workflow-info-grid"><article className="workflow-card"><LockKeyhole size={23} /><h2>A temporary private session</h2><p>A token in this browser tab controls access to its documents. This is temporary ownership, not an account. Copying the token or cloning a tab can share access.</p><p>Filing text and findings are not persisted in browser storage. Prepared text is stored privately on the server during the session.</p></article>
      <article className="workflow-card"><Clock3 size={23} /><h2>Retention & deletion</h2><p>The document page shows its expiry. Expired content becomes unavailable; you can also delete a document or reset a prepared demo from that page.</p><p>The local preview uses disposable storage. Retention and cleanup are best effort, not guaranteed secure erasure.</p><Link className="document-text-link" to="/activity">Manage this tab’s documents<ArrowRight size={15} /></Link></article>
      <article className="workflow-card"><ShieldCheck size={23} /><h2>Masking has limits</h2><p>Provider-bound filing excerpts are masked locally against the complete filing before selection. Pattern matching can miss sensitive content or mask ordinary text.</p><p>Check masking signals and the original extraction yourself. Source and model requests depend on enabled review stages.</p></article>
      <article className="workflow-card"><FileText size={23} /><h2>Evidence supports judgment</h2><p>Scores are provisional review signals. Missing checks are not a pass, quotation similarity does not prove legal support, and AI confidence is not calibrated.</p><p>Inspect coverage, original sources and limitations with a qualified reviewer before filing.</p><Link className="document-text-link" to="/demo">Explore the synthetic sample<ArrowRight size={15} /></Link></article></div>
    <div className="workflow-closing"><div><h2>Ready for a closer look?</h2><p>Start with a public or synthetic document.</p></div><StartReviewLink /></div>
  </section>;
}
