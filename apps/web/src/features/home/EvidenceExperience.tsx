import { useEffect, useRef, useState } from 'react';
import { ArrowDownRight, ArrowRight, FileText, Layers, ScanSearch } from 'lucide-react';
import type { EvidenceScene } from './evidenceScene';

const steps = [
  { title: 'The filing', caption: 'A convincing argument. An altered quotation.', icon: FileText },
  { title: 'The authority', caption: 'The cited opinion, beside the words attributed to it.', icon: Layers },
  { title: 'The difference', caption: 'Equal. Unequal. One missing prefix reverses the meaning.', icon: ScanSearch },
];

export function EvidenceExperience() {
  const host = useRef<HTMLDivElement>(null);
  const scene = useRef<EvidenceScene | null>(null);
  const selected = useRef(0);
  const [step, setStep] = useState(0);
  const [status, setStatus] = useState<'loading' | 'ready' | 'fallback'>('loading');
  useEffect(() => {
    const element = host.current;
    if (!element || typeof IntersectionObserver === 'undefined') return;
    let cancelled = false;
    let started = false;
    let visible = false;
    const fail = () => { scene.current?.dispose(); scene.current = null; if (!cancelled) setStatus('fallback'); };
    const observer = new IntersectionObserver(entries => {
      visible = entries[0]?.isIntersecting ?? false;
      scene.current?.visible(visible);
      if (!visible || started) return;
      started = true;
      void import('./evidenceScene').then(({ createEvidenceScene }) => {
        if (cancelled) return;
        scene.current = createEvidenceScene(element, fail);
        scene.current.visible(visible);
        scene.current.select(selected.current);
        setStatus('ready');
      }).catch(fail);
    }, { rootMargin: '100px' });
    observer.observe(element);
    return () => { cancelled = true; observer.disconnect(); scene.current?.dispose(); scene.current = null; };
  }, []);
  const choose = (next: number) => { selected.current = next; setStep(next); scene.current?.select(next); };
  return <section className="evidence-experience" aria-labelledby="experience-title" data-scene-status={status}>
    <div className="experience-heading">
      <div><span className="section-kicker">01 / FOLLOW THE EVIDENCE</span>
        <h2 id="experience-title">Look beneath<br /><span>the argument.</span></h2></div>
      <p>From the words on the page<br />to the source behind them.<ArrowDownRight size={32} strokeWidth={1} /></p>
    </div>
    <div className="evidence-stage" ref={host}>
      <span className="scene-index" aria-hidden="true">0{step + 1}<span>/ 03</span></span>
      {status !== 'ready' && <div className="evidence-fallback">
        <FileText size={44} strokeWidth={1} /><span>SYNTHETIC FILING / CITED SOURCE</span>
        <p>“equal.” <ArrowRight size={24} /> “unequal.”</p>
        <small>{status === 'loading' ? 'Preparing evidence study' : 'Evidence study: static view'}</small>
      </div>}
      <span className="scene-provenance">BROWN v. BOARD OF EDUCATION<br />347 U.S. 483, 495 (1954)</span>
    </div>
    <div className="experience-controls">
      <div className="evidence-steps" role="group" aria-label="Evidence study stages">
        {steps.map(({ title, icon: Icon }, index) => <button key={title} type="button" aria-pressed={step === index}
          onClick={() => choose(index)}><span className="step-number">0{index + 1}</span><Icon size={17} />{title}<ArrowRight className="step-arrow" size={17} /></button>)}
      </div>
      <p className="scene-caption" aria-live="polite">{steps[step]?.caption}</p>
      <p className="scene-disclaimer">Interactive illustration of our curated sample. Not live analysis.</p>
    </div>
  </section>;
}
