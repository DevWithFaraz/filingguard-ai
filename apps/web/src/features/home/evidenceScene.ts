import * as THREE from 'three';
import gsap from 'gsap';

export interface EvidenceScene {
  select: (step: number) => void;
  visible: (value: boolean) => void;
  dispose: () => void;
}

// These are illustrations of the reviewed fixture, never live analysis results.
export function createEvidenceScene(host: HTMLDivElement, onFailure: () => void): EvidenceScene {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
  renderer.setClearColor(0x141617, 0);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.domElement.setAttribute('aria-hidden', 'true');
  host.appendChild(renderer.domElement);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(34, 1, 0.1, 100);
  camera.position.set(0, 0, 12);
  const assembly = new THREE.Group();
  scene.add(assembly);
  const resources: Array<{ dispose: () => void }> = [];
  const own = <T extends { dispose: () => void }>(resource: T): T => { resources.push(resource); return resource; };
  const paperGeometry = own(new THREE.PlaneGeometry(2.8, 3.7));
  const textures: THREE.CanvasTexture[] = [];
  let active = true;
  let disposed = false;
  let step = 0;
  let narrow = false;
  let timeline: gsap.core.Timeline | undefined;
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const render = () => {
    if (disposed || !active || document.hidden) return;
    renderer.render(scene, camera);
    renderer.domElement.dataset.renderCount = String(Number(renderer.domElement.dataset.renderCount ?? 0) + 1);
  };

  function paperTexture(source: boolean) {
    const canvas = document.createElement('canvas');
    canvas.width = 840; canvas.height = 1110;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Canvas is unavailable');
    ctx.fillStyle = '#fafaf6'; ctx.fillRect(0, 0, 840, 1110);
    ctx.fillStyle = source ? '#466e57' : '#663b9d'; ctx.fillRect(0, 0, 840, 13);
    ctx.font = '22px Arial'; ctx.fillText(source ? '02 / THE AUTHORITY' : '01 / SYNTHETIC FILING', 70, 85);
    ctx.fillStyle = '#292832'; ctx.font = 'bold 48px Georgia';
    ctx.fillText(source ? 'Brown v. Board' : 'A motion for', 70, 190);
    ctx.fillText(source ? 'of Education' : 'a closer look.', 70, 247);
    ctx.fillStyle = '#707176'; ctx.font = '22px Arial';
    ctx.fillText(source ? '347 U.S. 483 (1954)  /  p. 495' : 'Curated example / not a real filing', 70, 302);
    ctx.fillStyle = '#d2d3ce';
    [615, 680, 570, 644, 480].forEach((width, i) => ctx.fillRect(70, 366 + i * 28, width, 5));
    ctx.fillStyle = source ? '#e4ebd3' : '#f0dfef'; ctx.fillRect(55, 560, 730, 251);
    ctx.fillStyle = '#302a35'; ctx.font = '35px Georgia';
    ctx.fillText('Separate educational', 78, 620);
    ctx.fillText('facilities are inherently', 78, 670);
    ctx.font = 'bold 49px Georgia'; ctx.fillStyle = source ? '#345644' : '#88354b';
    ctx.fillText(source ? 'unequal.' : 'equal.', 78, 744);
    ctx.fillStyle = '#d2d3ce';
    [650, 570, 620, 430].forEach((width, i) => ctx.fillRect(70, 874 + i * 28, width, 5));
    ctx.fillStyle = '#7c7b78'; ctx.font = '18px Arial'; ctx.fillText('FILINGGUARD AI / EVIDENCE STUDY', 70, 1050);
    const texture = own(new THREE.CanvasTexture(canvas));
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.anisotropy = Math.min(4, renderer.capabilities.getMaxAnisotropy());
    textures.push(texture);
    return texture;
  }

  const makePaper = (texture: THREE.Texture) => new THREE.Mesh(paperGeometry,
    own(new THREE.MeshBasicMaterial({ map: texture, side: THREE.DoubleSide })));
  const filing = new THREE.Group();
  const source = new THREE.Group();
  assembly.add(filing, source);
  const backingMaterial = own(new THREE.MeshBasicMaterial({ color: '#c5bdd2', side: THREE.DoubleSide }));
  const layers = Array.from({ length: 3 }, (_, i) => {
    const layer = new THREE.Mesh(paperGeometry, backingMaterial);
    layer.position.set(-0.06 * (i + 1), -0.06 * (i + 1), -0.07 * (i + 1));
    filing.add(layer);
    return layer;
  });
  filing.add(makePaper(paperTexture(false)));
  source.add(makePaper(paperTexture(true)));

  const linkGeometry = own(new THREE.BufferGeometry());
  const linkPoints = new Float32Array(6);
  linkGeometry.setAttribute('position', new THREE.BufferAttribute(linkPoints, 3));
  const linkMaterial = own(new THREE.LineBasicMaterial({ color: '#e4da72', transparent: true, opacity: 0 }));
  const link = new THREE.Line(linkGeometry, linkMaterial);
  assembly.add(link);
  const markerGeometry = own(new THREE.RingGeometry(0.065, 0.085, 32));
  const markerMaterial = own(new THREE.MeshBasicMaterial({ color: '#e4da72', transparent: true, opacity: 0 }));
  const markers = [new THREE.Mesh(markerGeometry, markerMaterial), new THREE.Mesh(markerGeometry, markerMaterial)];
  assembly.add(...markers);
  function updateLink() {
    const y = narrow ? -0.5 : -0.9;
    const positions: [number, number, number][] = narrow ? [[-0.18, y + 0.35, 0.8], [0.18, y - 0.35, 0.8]] : [[-0.35, y, 0.8], [0.35, y, 0.8]];
    positions.forEach((p, i) => { markers[i]?.position.set(...p); linkPoints.set(p, i * 3); });
    linkGeometry.getAttribute('position').needsUpdate = true;
  }

  const poses = () => narrow ? [
    { f: [0, 0.1, 0.5, -0.10, 0.20, -0.10, 1], s: [0.15, 0, -0.5, 0, 0, 0, 0.86] },
    { f: [-0.72, 0.88, 0, 0.10, 0.24, -0.12, 0.74], s: [0.72, -0.86, 0.6, -0.06, -0.17, 0.10, 0.74] },
    { f: [-0.85, 0.50, 0.1, 0, 0.12, -0.035, 0.70], s: [0.85, -0.50, 0.5, 0, -0.12, 0.035, 0.70] },
  ] : [
    { f: [0, 0, 0.5, -0.15, -0.30, -0.10, 1.04], s: [0.06, 0, -0.5, 0, 0, 0, 0.92] },
    { f: [-1.95, 0.10, 0, -0.04, 0.30, -0.11, 1], s: [1.95, 0.10, 0.2, 0.04, -0.26, 0.10, 1] },
    { f: [-1.80, 0, 0.2, 0, 0.12, -0.025, 1.07], s: [1.80, 0, 0.2, 0, -0.12, 0.025, 1.07] },
  ];
  function select(next: number, instant = false) {
    step = next;
    timeline?.kill();
    renderer.domElement.dataset.stage = String(step);
    renderer.domElement.dataset.transitioning = 'true';
    const pose = poses()[step]!;
    timeline = gsap.timeline({ defaults: { duration: instant || reducedMotion.matches ? 0 : 1.15, ease: 'power3.inOut' }, onUpdate: render,
      onComplete: () => { renderer.domElement.dataset.transitioning = 'false'; render(); } });
    [filing, source].forEach((object, i) => {
      const p = i === 0 ? pose.f : pose.s;
      timeline!.to(object.position, { x: p[0], y: p[1], z: p[2] }, 0)
        .to(object.rotation, { x: p[3], y: p[4], z: p[5] }, 0)
        .to(object.scale, { x: p[6], y: p[6], z: p[6] }, 0);
    });
    layers.forEach((layer, i) => timeline!.to(layer.position, {
      x: step === 0 ? -0.16 * (i + 1) : -0.03 * (i + 1),
      y: step === 0 ? -0.11 * (i + 1) : -0.03 * (i + 1),
      z: step === 0 ? -0.22 * (i + 1) : -0.03 * (i + 1),
    }, 0));
    timeline.to([linkMaterial, markerMaterial], { opacity: step === 2 ? 1 : 0 }, 0);
    updateLink();
    render();
  }
  const rotateX = gsap.quickTo(assembly.rotation, 'x', { duration: 0.7, ease: 'power3.out', onUpdate: render });
  const rotateY = gsap.quickTo(assembly.rotation, 'y', { duration: 0.7, ease: 'power3.out', onUpdate: render });
  function pointer(event: PointerEvent) {
    if (reducedMotion.matches || event.pointerType !== 'mouse' || !active) return;
    const box = host.getBoundingClientRect();
    rotateY(((event.clientX - box.left) / box.width - 0.5) * 0.16);
    rotateX(((event.clientY - box.top) / box.height - 0.5) * 0.10);
  }
  const resetPointer = () => { rotateX(0); rotateY(0); };
  const resize = () => {
    const { width, height } = host.getBoundingClientRect();
    if (!width || !height || disposed) return;
    const newNarrow = width < 650;
    camera.aspect = width / height;
    camera.position.z = newNarrow ? 10.5 : 8.8;
    camera.updateProjectionMatrix();
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.6, Math.sqrt(1800000 / (width * height))));
    renderer.setSize(width, height, false);
    narrow = newNarrow;
    select(step, true);
  };
  const resizeObserver = new ResizeObserver(resize);
  resizeObserver.observe(host);
  const onVisibility = () => { if (!document.hidden) render(); };
  const onMotion = () => { resetPointer(); select(step, true); };
  const onContextLost = (event: Event) => { event.preventDefault(); onFailure(); };
  host.addEventListener('pointermove', pointer);
  host.addEventListener('pointerleave', resetPointer);
  renderer.domElement.addEventListener('webglcontextlost', onContextLost);
  document.addEventListener('visibilitychange', onVisibility);
  reducedMotion.addEventListener('change', onMotion);
  resize();

  return {
    select,
    visible(value) { active = value; if (value) render(); },
    dispose() {
      disposed = true; timeline?.kill(); rotateX.tween.kill(); rotateY.tween.kill();
      resizeObserver.disconnect();
      host.removeEventListener('pointermove', pointer); host.removeEventListener('pointerleave', resetPointer);
      document.removeEventListener('visibilitychange', onVisibility);
      reducedMotion.removeEventListener('change', onMotion);
      renderer.domElement.removeEventListener('webglcontextlost', onContextLost);
      resources.forEach(resource => resource.dispose());
      textures.forEach(texture => { const canvas = texture.image as HTMLCanvasElement; canvas.width = 0; canvas.height = 0; });
      renderer.dispose(); renderer.forceContextLoss(); renderer.domElement.remove();
    },
  };
}
