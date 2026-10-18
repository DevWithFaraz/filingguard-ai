import { useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router';
import type { UseQueryResult } from '@tanstack/react-query';
import { ArrowDown, ArrowRight, ArrowUpRight, FileText, LockKeyhole, Menu, RefreshCw, Search, X } from 'lucide-react';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import logo from '../../assets/filingguard-logo.png';
import background from '../../assets/filingguard-background.jpg';
import { IntakeComposer } from '../intake/IntakeComposer';
import { EvidenceExperience } from './EvidenceExperience';
import { HeroBackdrop } from './HeroBackdrop';
import { PipelineWalkthrough } from './PipelineWalkthrough';
import './home.css';

gsap.registerPlugin(useGSAP, ScrollTrigger);

export function HomePage({ health }: { health: UseQueryResult<{ status: string }, Error> }) {
  const root = useRef<HTMLDivElement>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [focusDifference, setFocusDifference] = useState(false);
  const menuToggle = useRef<HTMLButtonElement>(null);
  const navigate = useNavigate();
  useGSAP(() => {
    const media = gsap.matchMedia();
    media.add('(prefers-reduced-motion: no-preference)', () => {
      gsap.timeline({ defaults: { ease: 'power3.out', duration: 0.65, clearProps: 'transform,opacity' } })
        .from('.title-piece', { yPercent: 110, rotation: 5, duration: 1, stagger: 0.09, transformOrigin: '0 100%' }, 0)
        .from('.hero-intro', { y: 14, opacity: 0.6 }, 0.08)
        .from('.home-composer-wrap', { y: 28, duration: 0.9 }, 0.22);
      gsap.utils.toArray<HTMLElement>('.experience-heading, .evidence-intro, .limits-heading', root.current).forEach(element => {
        gsap.from(element, { y: 25, duration: 1, ease: 'power3.out', clearProps: 'transform',
          scrollTrigger: { trigger: element, start: 'top 92%', once: true } });
      });
      gsap.from('.limits-list > div', { y: 25, opacity: 0.3, stagger: 0.12, duration: 0.7,
        clearProps: 'transform,opacity', scrollTrigger: { trigger: '.limits-list', start: 'top 88%', once: true } });
      gsap.from('.quote-comparison blockquote', { x: 25, stagger: 0.18, duration: 0.85,
        clearProps: 'transform', scrollTrigger: { trigger: '.quote-comparison', start: 'top 85%', once: true } });
      gsap.to('.hero-background', { y: 40, ease: 'none', scrollTrigger: { trigger: '.home-hero', start: 'top top', end: 'bottom top', scrub: 0.7 } });
    }, root);
    return () => media.revert();
  }, { scope: root });

  return <div className="home-page" ref={root}>
    <a className="skip-link" href="#main">Skip to content</a>
    <header className="home-header" onKeyDown={event => {
      if (event.key === 'Escape' && menuOpen) { setMenuOpen(false); menuToggle.current?.focus(); }
    }}>
      <Link to="/" className="home-brand" aria-label="FilingGuard AI home">
        <img src={logo} alt="FilingGuard AI" width="2172" height="724" /></Link>
      <button type="button" ref={menuToggle} className="home-menu-toggle" aria-label={menuOpen ? 'Close navigation' : 'Open navigation'}
        aria-expanded={menuOpen} aria-controls="home-navigation" onClick={() => setMenuOpen(!menuOpen)}>
        {menuOpen ? <X size={22} /> : <Menu size={22} />}</button>
      <nav id="home-navigation" className={menuOpen ? 'home-navigation is-open' : 'home-navigation'} aria-label="Main navigation">
        <a href="#how-it-works" onClick={() => setMenuOpen(false)}>How it works</a>
        <a href="#limits" onClick={() => setMenuOpen(false)}>Privacy & limits</a>
        <Link to="/activity">Activity</Link>
        <Link to="/settings" className="mobile-settings">Settings</Link>
        <Link to="/demo" className="home-sample-link">Explore sample <ArrowUpRight size={16} /></Link>
      </nav>
    </header>
    <main id="main" className="home-main" tabIndex={-1}>
      <section className="home-hero" aria-labelledby="home-title">
        <img className="hero-background" src={background} alt="" fetchPriority="high" width="3888" height="2592" />
        <HeroBackdrop />
        <div className="hero-content">
          <div className="hero-intro hero-eyebrow"><span /> A SECOND LOOK. BEFORE YOU FILE.</div>
          <h1 className="hero-title" id="home-title" aria-label="FilingGuard-AI"><span className="title-mask" aria-hidden="true"><span className="title-piece">Filing</span><span className="title-piece">Guard</span><span className="title-piece title-accent">-AI</span></span></h1>
          <p className="hero-intro hero-description">Every citation has a source. Every argument deserves a closer look.</p>
          <div className="home-composer-wrap"><IntakeComposer /></div>
          <div className="hero-footnote"><LockKeyhole size={13} /><span>Temporary private session. Public or synthetic documents only.</span></div>
        </div>
      </section>
      <PipelineWalkthrough />
      <EvidenceExperience />
      <section id="quote-comparison" className="home-evidence" aria-labelledby="evidence-title">
        <div className="section-kicker"><span>02 / ONE WORD CHANGES EVERYTHING</span><ArrowDown size={19} /></div>
        <div className="evidence-editorial">
          <div className="evidence-intro"><h2 id="evidence-title">One word.<br />A different meaning.</h2>
            <p>A real case can still be quoted incorrectly. Our curated sample puts the filing beside its source, so the difference is there to inspect.</p>
            <button className="home-text-action" onClick={() => navigate('/demo')}>Open reviewed sample <ArrowUpRight size={19} /></button>
          </div>
          <div className={`quote-comparison${focusDifference ? ' difference-focused' : ''}`} aria-label="Illustrative quote comparison">
            <div className="quote-label"><FileText size={16} /><span>SYNTHETIC FILING</span><span className="sample-marker">Sample</span></div>
            <blockquote><span className="quote-context">“Separate educational facilities are inherently </span><mark className="changed-word">equal.</mark><span className="quote-context">”</span></blockquote>
            <div className="quote-divider"><Search size={17} /><span>Compare with the source</span>
              <button type="button" className="difference-toggle" aria-pressed={focusDifference} onClick={() => setFocusDifference(!focusDifference)}>Focus difference <span aria-hidden="true" /></button></div>
            <div className="quote-label"><span>BROWN v. BOARD OF EDUCATION</span><span>347 U.S. 483</span></div>
            <blockquote><span className="quote-context">“Separate educational facilities are inherently </span><mark className="source-word">unequal.</mark><span className="quote-context">”</span></blockquote>
            <p className="quote-note">Illustrative comparison. Executed checks appear in review results.</p>
          </div>
        </div>
      </section>
      <section className="home-limits" id="limits" aria-labelledby="limits-title">
        <div className="limits-heading"><span className="section-kicker">03 / YOU STAY IN CONTROL</span>
          <h2 id="limits-title">Your judgment.<br />With the evidence in view.</h2>
          <a className="home-text-action" href="#home-title">Start with a document <ArrowRight size={19} /></a></div>
        <dl className="limits-list">
          <div><dt>Temporary by design</dt><dd>Documents belong to your anonymous session. Access expires after 55 minutes; you can delete a prepared document sooner.</dd></div>
          <div><dt>Preparation is available</dt><dd>Paste text or upload a text-based PDF. Extraction preserves the original passages. Scanned PDFs need pasted text.</dd></div>
          <div><dt>Human review comes first</dt><dd>Use public or synthetic material. Review flags require human judgment; FilingGuard does not provide legal advice or certify a filing.</dd></div>
        </dl>
      </section>
    </main>
    <footer className="home-footer">
      <div className="footer-main">
        <div className="footer-identity">
          <Link to="/" aria-label="FilingGuard AI footer home"><img src={logo} alt="FilingGuard AI" width="2172" height="724" /></Link>
          <p>A second look.<br />Before you file.</p>
        </div>
        <nav className="footer-navigation" aria-label="Footer navigation">
          <span>EXPLORE</span>
          <Link to="/demo">Review the sample <ArrowUpRight size={15} /></Link>
          <a href="#limits">Privacy and limitations <ArrowUpRight size={15} /></a>
          <a href="#home-title">Back to top <ArrowUpRight size={15} /></a>
        </nav>
        <div className="footer-note"><span>BUILT FOR A CLOSER LOOK</span>
          <p>Evidence in view.<br />Judgment in your hands.</p>
          <small>For public or synthetic documents. Not legal advice.</small>
        </div>
      </div>
      <div className="footer-bottom"><span>FilingGuard AI / Pre-filing review</span>
      <div className="connection" role="status" aria-live="polite"><span className={`status-dot ${health.isSuccess ? 'online' : ''}`} />
        {health.isPending ? 'Connecting' : health.isError ? 'API unavailable' : 'API connected'}
        <button className="icon-button" aria-label="Refresh API connection" title="Refresh API connection"
          disabled={health.isFetching} onClick={() => void health.refetch()}><RefreshCw size={14} className={health.isFetching ? 'spinning' : ''} /></button></div>
      <Link to="/settings">Settings <ArrowUpRight size={14} /></Link>
      </div>
    </footer>
  </div>;
}
