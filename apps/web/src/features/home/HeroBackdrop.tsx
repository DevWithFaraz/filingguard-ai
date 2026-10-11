import { useEffect, useRef } from 'react';
import type { HeroSceneController } from './heroDepthScene';

export function HeroBackdrop() {
  const host = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = host.current;
    const parent = element?.parentElement;
    if (!element || !parent) return;
    let cancelled = false;
    let started = false;
    let visible = false;
    let controller: HeroSceneController | undefined;
    const fail = () => {
      controller?.dispose();
      controller = undefined;
      if (!cancelled) element.dataset.sceneStatus = 'fallback';
    };
    const activate = (next: boolean) => {
      visible = next;
      controller?.visible(next);
      if (!next || started) return;
      started = true;
      void import('./heroDepthScene').then(({ createHeroScene }) => {
        if (cancelled) return;
        controller = createHeroScene(element, parent, fail);
        element.dataset.sceneStatus = 'ready';
        controller.visible(visible);
      }).catch(fail);
    };
    const observer = typeof IntersectionObserver === 'undefined' ? undefined :
      new IntersectionObserver(entries => activate(entries[0]?.isIntersecting ?? false));
    if (observer) observer.observe(element);
    else element.dataset.sceneStatus = 'fallback';
    return () => {
      cancelled = true;
      observer?.disconnect();
      controller?.dispose();
    };
  }, []);

  return <div ref={host} className="hero-scene" aria-hidden="true"
    data-scene-status="loading" style={{ pointerEvents: 'none' }} />;
}
