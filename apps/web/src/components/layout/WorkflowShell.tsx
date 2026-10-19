import { Activity, ArrowLeft, ArrowRight, FilePlus2, Home, LockKeyhole, Settings, Sparkles } from 'lucide-react';
import { useEffect, useRef, type ReactNode } from 'react';
import { Link, NavLink, useLocation } from 'react-router';
import logo from '../../assets/filingguard-logo.png';
import '../../features/intake/prepared.css';
import './workflow.css';

import { IdentityBadge } from '../../features/identity/IdentityBadge';

export function WorkflowShell({ children, connection }: { children: ReactNode; connection?: ReactNode }) {
  const { pathname } = useLocation();
  const main = useRef<HTMLElement>(null);
  const previousPath = useRef(pathname);
  useEffect(() => {
    if (previousPath.current !== pathname) {
      window.scrollTo({ top: 0, behavior: 'instant' });
      main.current?.focus({ preventScroll: true });
      previousPath.current = pathname;
    }
  }, [pathname]);
  return <div className="document-workspace">
    <a className="skip-link" href="#main">Skip to content</a>
    <header className="document-header"><Link className="document-brand" to="/" aria-label="FilingGuard AI home"><img src={logo} alt="FilingGuard AI" /></Link>
      <nav aria-label="Main navigation"><NavLink to="/" end><Home size={16} />Home</NavLink>
        <NavLink to="/demo"><Sparkles size={16} />Sample</NavLink><NavLink to="/activity"><Activity size={16} />Activity</NavLink>
        <NavLink to="/settings"><Settings size={16} />Settings</NavLink></nav>
      <div className="workflow-header-actions"><IdentityBadge /><Link className="workflow-new-document" to="/"><FilePlus2 size={16} />New document</Link></div></header>
    <main ref={main} id="main" tabIndex={-1}><div key={pathname} className="workflow-route">{children}</div></main>
    <footer className="document-footer"><div><span>FILINGGUARD AI · PRE-FILING REVIEW</span><p>Human review required. Not legal advice.</p></div>
      <div className="workflow-footer-links"><Link to="/privacy"><LockKeyhole size={14} />Privacy & limits</Link>{connection}</div></footer>
  </div>;
}

export function WorkflowHero({ eyebrow, title, description, children }: { eyebrow: string; title: string; description: string; children?: ReactNode }) {
  return <><div className="document-wayfinding"><Link to="/"><ArrowLeft size={15} />Back to home</Link><span>YOUR REVIEW WORKSPACE</span></div>
    <header className="workflow-hero"><div><div className="document-kicker"><span />{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>{children}</header></>;
}

export function StartReviewLink() {
  return <Link to="/" className="primary-button">Prepare a document<ArrowRight size={16} /></Link>;
}
