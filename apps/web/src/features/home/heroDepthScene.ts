import * as THREE from 'three';

export interface HeroSceneController {
  visible: (value: boolean) => void;
  dispose: () => void;
}

// Decorative paper studies only; these never represent analysis results.
export function createHeroScene(host: HTMLDivElement, parent: HTMLElement, onFailure: () => void): HeroSceneController {
  const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'low-power', preserveDrawingBuffer: true });
  const resources: Array<{ dispose: () => void }> = [];
  const own = <T extends { dispose: () => void }>(resource: T): T => {
    resources.push(resource);
    return resource;
  };
  let disposed = false;
  let active = false;
  let frame = 0;
  let width = 0;
  let height = 0;
  let edge = 0.22;
  let stopAt = 0;
  let lastTime = 0;
  let resizeObserver: ResizeObserver | undefined;
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)');
  const pose = { x: 0, y: 0, leftLift: 0, rightLift: 0 };
  const target = { ...pose };
  const poseKeys = ['x', 'y', 'leftLift', 'rightLift'] as const;
  const leftOrigin = new THREE.Vector3();
  const rightOrigin = new THREE.Vector3();
  const projected = new THREE.Vector3();
  const scene = new THREE.Scene();
  const camera = new THREE.OrthographicCamera(-6, 6, 4, -4, 0.1, 60);
  camera.position.set(0, 0, 20);
  const left = new THREE.Group();
  const right = new THREE.Group();
  scene.add(left, right);

  function dispose() {
    if (disposed) return;
    disposed = true;
    cancelAnimationFrame(frame);
    resizeObserver?.disconnect();
    parent.removeEventListener('pointermove', pointer);
    parent.removeEventListener('pointerleave', reset);
    parent.removeEventListener('pointercancel', reset);
    window.removeEventListener('blur', reset);
    document.removeEventListener('visibilitychange', visibility);
    motion.removeEventListener('change', preference);
    finePointer.removeEventListener('change', preference);
    window.removeEventListener('resize', resize);
    renderer.domElement.removeEventListener('webglcontextlost', contextLost);
    resources.forEach(resource => resource.dispose());
    scene.clear();
    renderer.dispose();
    renderer.forceContextLoss();
    renderer.domElement.remove();
  }

  function render() {
    if (disposed || !active || document.hidden || !width || !height) return;
    try {
      left.rotation.set(pose.y * 0.19 - pose.leftLift * 0.09,
        pose.x * 0.25 - pose.leftLift * 0.12, -pose.leftLift * 0.035);
      right.rotation.set(-pose.y * 0.16 - pose.rightLift * 0.09,
        -pose.x * 0.25 + pose.rightLift * 0.12, pose.rightLift * 0.035);
      left.position.copy(leftOrigin).add(new THREE.Vector3(pose.x * 0.20,
        -pose.y * 0.15 + pose.leftLift * 0.22, pose.leftLift * 0.45));
      right.position.copy(rightOrigin).add(new THREE.Vector3(pose.x * 0.20,
        -pose.y * 0.15 + pose.rightLift * 0.22, pose.rightLift * 0.45));
      renderer.setScissorTest(false);
      renderer.domElement.dataset.renderCount = String(Number(renderer.domElement.dataset.renderCount ?? 0) + 1);
      renderer.clear();
      // A hard clear middle protects the title/composer even during parallax.
      renderer.setScissorTest(true);
      const band = Math.ceil(width * edge);
      renderer.setScissor(0, 0, band, height);
      renderer.render(scene, camera);
      renderer.setScissor(width - band, 0, band, height);
      renderer.render(scene, camera);
      renderer.setScissorTest(false);
    } catch {
      dispose();
      onFailure();
    }
  }

  function tick(time: number) {
    frame = 0;
    if (disposed || !active || document.hidden) return;
    const blend = 1 - Math.exp(-Math.min(time - lastTime, 64) / 95);
    lastTime = time;
    for (const key of poseKeys) pose[key] = time >= stopAt
      ? target[key] : THREE.MathUtils.lerp(pose[key], target[key], blend);
    render();
    if (!disposed && time < stopAt) frame = requestAnimationFrame(tick);
  }

  function requestPose(x: number, y: number, leftLift = 0, rightLift = 0) {
    target.x = x;
    target.y = y;
    target.leftLift = leftLift;
    target.rightLift = rightLift;
    const now = performance.now();
    stopAt = now + 650;
    if (!frame) lastTime = now;
    if (!frame && active && !document.hidden && !disposed) frame = requestAnimationFrame(tick);
  }

  function pointer(event: PointerEvent) {
    if (!active || document.hidden || motion.matches || !finePointer.matches || event.pointerType !== 'mouse' || width < 768) return;
    const box = parent.getBoundingClientRect();
    if (!box.width || !box.height) return;
    const canvasBox = host.getBoundingClientRect();
    if (!canvasBox.width || !canvasBox.height) return;
    // Use resting anchors so the hover response cannot chase its own movement.
    const distance = (origin: THREE.Vector3) => {
      projected.copy(origin).project(camera);
      const x = canvasBox.left + (projected.x + 1) * canvasBox.width / 2;
      const y = canvasBox.top + (1 - projected.y) * canvasBox.height / 2;
      const radius = Math.max(140, canvasBox.width * 0.15);
      return Math.hypot(event.clientX - x, event.clientY - y) / radius;
    };
    const leftDistance = distance(leftOrigin);
    const rightDistance = distance(rightOrigin);
    const lift = 1 - THREE.MathUtils.smoothstep(Math.min(leftDistance, rightDistance), 0.1, 1.4);
    requestPose(THREE.MathUtils.clamp((event.clientX - box.left) / box.width * 2 - 1, -1, 1),
      THREE.MathUtils.clamp((event.clientY - box.top) / box.height * 2 - 1, -1, 1),
      leftDistance < rightDistance ? lift : 0, rightDistance <= leftDistance ? lift : 0);
  }
  function reset() {
    if (motion.matches || !finePointer.matches || width < 768) { pause(); render(); return; }
    requestPose(0, 0);
  }
  function pause() {
    cancelAnimationFrame(frame);
    frame = 0;
    for (const key of poseKeys) pose[key] = target[key] = 0;
  }
  function visibility() { pause(); if (!document.hidden) render(); }
  function preference() { pause(); render(); }
  function contextLost(event: Event) { event.preventDefault(); dispose(); onFailure(); }

  function resize() {
    if (disposed) return;
    const box = host.getBoundingClientRect();
    width = Math.round(box.width);
    height = Math.round(box.height);
    if (!width || !height) { pause(); return; }
    const phone = width < 768;
    const tablet = width < 1100;
    edge = phone ? 0.12 : tablet ? 0.16 : 0.22;
    camera.top = 6 * height / width;
    camera.bottom = -camera.top;
    camera.updateProjectionMatrix();
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, phone ? 1.25 : 1.5,
      Math.sqrt(1_500_000 / (width * height))));
    renderer.setSize(width, height, false);
    leftOrigin.set(phone ? -5.8 : tablet ? -5.3 : -4.9, camera.top * 0.13, 0);
    rightOrigin.set(phone ? 5.8 : tablet ? 5.3 : 4.9, -camera.top * 0.08, 0);
    left.scale.setScalar(phone ? 0.65 : tablet ? 0.76 : 0.86);
    right.scale.copy(left.scale);
    left.children.forEach((child, i) => { child.visible = !phone || i === 0; });
    right.children.forEach((child, i) => { child.visible = !phone || i === 0; });
    pause();
    render();
  }

  try {
    renderer.setClearColor(0x000000, 0);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.setScissorTest(false);
    renderer.domElement.setAttribute('aria-hidden', 'true');
    renderer.domElement.style.cssText = 'display:block;width:100%;height:100%;pointer-events:none';
    scene.add(new THREE.HemisphereLight(0xffffff, 0x66727c, 1.3));
    const key = new THREE.DirectionalLight(0xfff5e6, 2.2);
    key.position.set(-3, 7, 5);
    const rim = new THREE.DirectionalLight(0xc5e9e2, 0.9);
    rim.position.set(6, -2, 5);
    scene.add(key, rim);

    const paper = document.createElement('canvas');
    paper.width = 256;
    paper.height = 512;
    const context = paper.getContext('2d');
    if (!context) throw new Error('Decorative canvas unavailable');
    context.fillStyle = '#f0f3ee';
    context.fillRect(0, 0, 256, 512);
    context.fillStyle = '#99aaa8';
    context.fillRect(28, 48, 68, 5);
    context.fillStyle = '#cad1cb';
    for (let i = 0; i < 19; i++) context.fillRect(28, 100 + i * 17, i % 5 === 4 ? 125 : 200, 2);
    context.fillStyle = '#adc7bd';
    context.fillRect(28, 227, 188, 24);
    context.fillStyle = '#f0f3ee';
    context.fillRect(36, 237, 142, 2);
    const texture = own(new THREE.CanvasTexture(paper));
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.anisotropy = Math.min(2, renderer.capabilities.getMaxAnisotropy());
    own({ dispose() { paper.width = 0; paper.height = 0; } });
    const paperMaterial = own(new THREE.MeshStandardMaterial({ map: texture, roughness: 0.9,
      metalness: 0, side: THREE.DoubleSide }));
    const backingMaterial = own(new THREE.MeshStandardMaterial({ color: 0xdcdce6,
      roughness: 0.95, side: THREE.DoubleSide }));
    // Depth-only S curves keep vertical ordering intact, so sheets cannot fold
    // through themselves. Each side has its own silhouette and inflection point.
    [left, right].forEach((group, side) => {
      const sign = side === 0 ? -1 : 1;
      const height = side === 0 ? 3.65 : 3.3;
      const geometry = own(new THREE.PlaneGeometry(side === 0 ? 1.95 : 2.08, height, 1, 64));
      const positions = geometry.getAttribute('position');
      for (let i = 0; i < positions.count; i++) {
        const t = positions.getY(i) / height;
        positions.setZ(i, Math.sin(t * Math.PI * 1.65 + (side === 0 ? 0 : 0.28)) * (side === 0 ? 0.58 : -0.46));
      }
      geometry.computeVertexNormals();
      geometry.computeBoundingSphere();
      const sheet = new THREE.Mesh(geometry, paperMaterial);
      sheet.rotation.set(side === 0 ? 0.10 : -0.06, side === 0 ? -0.30 : 0.40, side === 0 ? -0.20 : 0.13);
      group.add(sheet);
      const backing = new THREE.Mesh(geometry, backingMaterial);
      backing.rotation.copy(sheet.rotation);
      // Offset in the page's own coordinates; the matching curves stay separated.
      backing.position.set(sign * 0.12, -0.07, -0.18).applyEuler(sheet.rotation);
      group.add(backing);
    });

    host.appendChild(renderer.domElement);
    parent.addEventListener('pointermove', pointer, { passive: true });
    parent.addEventListener('pointerleave', reset, { passive: true });
    parent.addEventListener('pointercancel', reset, { passive: true });
    window.addEventListener('blur', reset);
    document.addEventListener('visibilitychange', visibility);
    motion.addEventListener('change', preference);
    finePointer.addEventListener('change', preference);
    renderer.domElement.addEventListener('webglcontextlost', contextLost);
    if (typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(resize);
      resizeObserver.observe(host);
    }
    window.addEventListener('resize', resize, { passive: true });
    resize();
    return {
      visible(value) { active = value; pause(); if (value) render(); },
      dispose,
    };
  } catch (error) {
    dispose();
    throw error;
  }
}
