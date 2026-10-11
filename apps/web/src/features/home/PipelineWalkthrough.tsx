import { useEffect, useRef, useState } from 'react';
import { ArrowDownRight, Pause, Play, RotateCcw } from 'lucide-react';
import desktopMp4 from '../../assets/video/pipeline-film-desktop.mp4';
import desktopWebm from '../../assets/video/pipeline-film-desktop.webm';
import mobileMp4 from '../../assets/video/pipeline-film-mobile.mp4';
import mobileWebm from '../../assets/video/pipeline-film-mobile.webm';
import poster from '../../assets/video/pipeline-film-poster.webp';
import './pipeline-walkthrough.css';

type Playback = 'poster' | 'playing' | 'paused' | 'failed';
type Intent = 'auto' | 'play' | 'pause';

const stages = [
  'Upload brief', 'Extract text', 'Look up authorities', 'Compare quotations',
  'Review propositions', 'Check privacy & court rules', 'Map risk', 'Build evidence report',
];

export function PipelineWalkthrough() {
  const frame = useRef<HTMLDivElement>(null);
  const video = useRef<HTMLVideoElement>(null);
  const policy = useRef({ inView: false, reducedMotion: false, failed: false, intent: 'auto' as Intent });
  const synchronize = useRef<() => void>(() => {});
  const reportFailure = useRef<() => void>(() => {});
  const restorePosition = useRef<number | null>(null);
  const [mediaRequested, setMediaRequested] = useState(false);
  const [compactRendition, setCompactRendition] = useState(() => window.matchMedia('(max-width: 767px)').matches);
  const [playback, setPlayback] = useState<Playback>('poster');

  useEffect(() => {
    const element = video.current;
    const host = frame.current;
    if (!element || !host) return;
    let active = true;
    let attempt = 0;
    const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const viewport = window.matchMedia('(max-width: 767px)');
    policy.current.reducedMotion = motion.matches;

    const shouldPlay = () => policy.current.inView && !document.hidden && !policy.current.failed
      && policy.current.intent !== 'pause'
      && (!policy.current.reducedMotion || policy.current.intent === 'play');
    const failed = () => {
      if (!active) return;
      policy.current.failed = true;
      if (!element.paused) element.pause();
      setPlayback('failed');
    };
    const sync = () => {
      if (!active) return;
      const thisAttempt = ++attempt;
      if (!shouldPlay()) {
        if (!element.paused) element.pause();
        if (policy.current.reducedMotion && policy.current.intent !== 'play' && !policy.current.failed) setPlayback('poster');
        return;
      }
      setMediaRequested(true);
      if (!element.querySelector('source') || !element.paused) return;
      void element.play().catch((error: unknown) => {
        if (!active || thisAttempt !== attempt || !shouldPlay()) return;
        if (error instanceof DOMException && error.name === 'AbortError') return;
        if (error instanceof DOMException && error.name === 'NotAllowedError') {
          // A browser can require a deliberate click even for muted playback.
          policy.current.intent = 'pause';
          setPlayback('poster');
          return;
        }
        failed();
      });
    };
    const playing = () => {
      if (!shouldPlay()) { if (!element.paused) element.pause(); return; }
      setPlayback('playing');
    };
    const paused = () => {
      if (!active || policy.current.failed) return;
      setPlayback(policy.current.reducedMotion && policy.current.intent !== 'play' ? 'poster' : 'paused');
    };
    const changedMotion = () => {
      policy.current.reducedMotion = motion.matches;
      // Opting into reduced motion cancels an earlier play request. The next
      // deliberate click may start the film again under the new preference.
      if (motion.matches && policy.current.intent === 'play') policy.current.intent = 'auto';
      sync();
    };
    const changedRendition = () => {
      attempt++;
      if (element.querySelector('source')) restorePosition.current ??= element.currentTime;
      if (!element.paused) element.pause();
      setCompactRendition(viewport.matches);
    };
    const loadedMetadata = () => {
      const position = restorePosition.current;
      restorePosition.current = null;
      if (position !== null && Number.isFinite(element.duration)) {
        element.currentTime = Math.min(position, Math.max(0, element.duration - 0.001));
      }
    };
    let observer: IntersectionObserver | undefined;
    if (typeof IntersectionObserver !== 'undefined') {
      observer = new IntersectionObserver(entries => {
        if (!active) return;
        const entry = entries[0];
        policy.current.inView = !!entry?.isIntersecting && entry.intersectionRatio >= 0.2;
        sync();
      }, { threshold: [0, 0.2] });
      observer.observe(host);
    } else {
      // Without visibility observation, retain the poster until a click.
      policy.current.inView = true;
      policy.current.intent = 'pause';
    }
    synchronize.current = sync;
    reportFailure.current = failed;
    element.addEventListener('playing', playing);
    element.addEventListener('pause', paused);
    element.addEventListener('error', failed);
    element.addEventListener('loadedmetadata', loadedMetadata);
    document.addEventListener('visibilitychange', sync);
    motion.addEventListener('change', changedMotion);
    viewport.addEventListener('change', changedRendition);
    return () => {
      active = false;
      attempt++;
      observer?.disconnect();
      element.removeEventListener('playing', playing);
      element.removeEventListener('pause', paused);
      element.removeEventListener('error', failed);
      element.removeEventListener('loadedmetadata', loadedMetadata);
      document.removeEventListener('visibilitychange', sync);
      motion.removeEventListener('change', changedMotion);
      viewport.removeEventListener('change', changedRendition);
      if (!element.paused) element.pause();
      synchronize.current = () => {};
      reportFailure.current = () => {};
    };
  }, []);

  useEffect(() => {
    if (!mediaRequested) return;
    video.current?.load();
    synchronize.current();
  }, [mediaRequested, compactRendition]);

  const toggle = () => {
    if (playback === 'playing') {
      policy.current.intent = 'pause';
    } else {
      policy.current.intent = 'play';
      if (policy.current.failed) {
        policy.current.failed = false;
        video.current?.load();
      }
    }
    synchronize.current();
  };
  const ButtonIcon = playback === 'playing' ? Pause : playback === 'failed' ? RotateCcw : Play;
  const buttonLabel = playback === 'playing' ? 'Pause film' : playback === 'failed' ? 'Retry film' : 'Play film';
  const posterVisible = playback === 'poster' || playback === 'failed';

  return <section id="how-it-works" className="pipeline-walkthrough" aria-labelledby="pipeline-title">
    <div className="pipeline-inner">
      <div className="pipeline-heading">
        <div><span className="section-kicker">THE REVIEW PIPELINE</span>
          <h2 id="pipeline-title">How it works<span>.</span></h2></div>
        <p id="pipeline-description">Follow the path from your brief <br />to the evidence behind it.<ArrowDownRight size={30} strokeWidth={1} aria-hidden="true" /></p>
      </div>
      <div className="pipeline-frame" ref={frame} data-playback={playback}>
        <video id="pipeline-film" ref={video} className="pipeline-film" muted loop playsInline preload={mediaRequested ? 'metadata' : 'none'}
          poster={poster} width="2560" height="1440" aria-label="FilingGuard AI pipeline film"
          aria-describedby="pipeline-description pipeline-summary">
          {mediaRequested && <>
            <source src={compactRendition ? mobileWebm : desktopWebm} type="video/webm" />
            <source src={compactRendition ? mobileMp4 : desktopMp4} type="video/mp4" onError={() => reportFailure.current()} />
          </>}
        </video>
        {posterVisible && <img className="pipeline-poster" src={poster} alt="" width="2560" height="1440" loading="lazy" />}
      </div>
      <div className="pipeline-toolbar">
        <span>26 seconds <span aria-hidden="true">/</span> Silent loop</span>
        <button type="button" className="pipeline-playback" aria-controls="pipeline-film" onClick={toggle}>
          <ButtonIcon size={15} aria-hidden="true" />{buttonLabel}</button>
      </div>
      {playback === 'failed' && <p className="pipeline-unavailable" role="status">The film is unavailable. Follow the stages below.</p>}
      <ol className="pipeline-summary" id="pipeline-summary" aria-label="Review pipeline stages">
        {stages.map((stage, index) => <li key={stage}><span aria-hidden="true">0{index + 1}</span>{stage}</li>)}
      </ol>
    </div>
  </section>;
}
