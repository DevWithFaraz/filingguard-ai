# Homepage

October 11 T059 corrects two stale sentences: the quote comparison is illustrative,
and executed findings require human review. Layout, assets and motion are preserved.

## October 11 glass input preview (D008)

The user explicitly requested this scoped homepage change. The composer retains
its layout and submission/state behavior, with a single lilac translucent gradient,
28px backdrop blur, restrained saturation, reflective edge and layered shadow.
Darker secondary text keeps the busy background readable. Inner rows remain
transparent; native selects and the main action keep their solid treatments.
Unsupported blur uses an opaque background. Reduced transparency/increased
contrast disable blur and use a defined border; forced colors use system colors.
Existing motion and focus feedback remain; there is no animated blur or new JS.
Desktop/mobile keyboard/axe checks pass 2/2; build and actual material preference
emulation pass. Local screenshots and scope limits are recorded in
[[docs/sessions/2026-10-11 - Glass input composer preview]]. User aesthetic approval
remains pending. Continuing UI scope is in [[AGENTS]] and [[docs/product/UI direction]].

First design pass implemented September 29 (D001), expanded by D002 after user
feedback requesting stronger motion, glass and 3D. `HomePage.tsx` owns the image
hero, responsive navigation, curated quote comparison, privacy/limits and health
footer. `home.css` scopes homepage styling; inner review screens retain their
workspace layout. IntakeComposer owns submission behavior and API queries.

## Pipeline film

`PipelineWalkthrough.tsx` owns the D006 "How it works" band directly below the
hero; `pipeline-walkthrough.css` scopes its layout. The navigation anchor now
targets this band, while the existing evidence study and quotation comparison
continue below it. Film source, beat timing and encode budgets belong to
[[apps/video/README]], [[apps/video/brief/BRIEF]] and [[apps/video/brief/BEATS]].

The browser consumes local rendered MP4/WebM and a WebP poster from
`apps/web/src/assets/video`; it does not execute Remotion. Smaller viewports
select the 1920x1080 rendition, while desktop uses 2560x1440. Sources attach only
when playback is first requested in view. Crossing the 767px breakpoint reloads
the appropriate rendition while restoring the film position and preserving a
deliberate pause. The film is silent, muted, looping and
inline. A visible keyboard-accessible play/pause button controls it, and eight
process stages provide equivalent static page text.

An IntersectionObserver pauses playback outside the visible band; document
visibility also suspends it. A deliberate pause persists across those events.
Reduced motion retains the poster until a deliberate play request; changing to
reduced motion pauses an existing film and restores the poster. Playback errors
retain the poster and process text with a retry control. On October 7, the final
exported assets passed metadata/size checks and the installed-Chrome browser
suite passed 22 cases across desktop and mobile viewport projects. The suite
covered the film controls, reduced motion, failures/retry, source switching,
homepage, evidence experience and synthetic intake. Actual uninterrupted loops
selected WebM at 2560x1440 and 1920x1080 respectively, advanced through nine beat
samples and wrapped once at 26 seconds with no page errors. A later mobile copy
spacing repair passed the existing two rendition/layout cases; the full suite
was not repeated after that text-only change. CSS-pixel screenshots confirm the
essential quotation difference at the 390px viewport. This is desktop Chrome
viewport emulation, not a physical-device performance result or proof of MP4
fallback playback. See [[apps/video/brief/REVIEW]],
[[docs/sessions/2026-10-06 - Programmatic video production]] and
[[docs/sessions/2026-10-07 - Pipeline film visual revision]].

Related: [[docs/decisions/ADR-010 - Remotion pipeline film]],
[[docs/feedback/FB-009 - Programmatic pipeline film]], [[TODO]] (D006).

The supplied JPG background and PNG logo are unchanged; GC Avalance SemiBold is locally
served for the main heading, with Bold retained for other display type.
Source and permission provenance: [[apps/web/src/assets/README]].
GSAP/useGSAP provide scoped entrance and mode-panel animation with cleanup and
matchMedia reduced-motion handling. CSS animates the mode indicator and control
feedback. Content is available immediately; form controls never trigger requests
through animation callbacks. ScrollTrigger choreographs editorial blocks together
to avoid heading/body overlap; it does not hijack scrolling or pin the page.

## Three.js ownership
`HeroBackdrop.tsx` lazily imports `heroDepthScene.ts` for layered paper sheets at
the hero edges. D004 restores gentle S-curves after feedback on D003's flat sheets.
Left and right differ in bend direction, phase, dimensions and resting angles.
Bounded cursor tilt and independent proximity lift ease back on pointer exit.
Matte paper and tone-mapped lighting preserve line detail.
Scissoring keeps the center transparent;
the canvas ignores pointer events. Mouse parallax is bounded, touch stays native,
and mobile renders fewer forms. The 3888x2592 replacement background renders at
full opacity without blur; a dark overlay maintains foreground readability.

`EvidenceExperience.tsx` owns keyboard/touch stage buttons, DOM captions and
fallback content. `evidenceScene.ts` renders the synthetic filing and Brown source
as textured 3D pages. Three selectable stages rearrange the pages; the last links
the comparison. It is an illustration, not a finding or a legal engine. Actual
quote text remains available in the DOM comparison immediately below the scene.

Both factories cap DPR and total drawing-buffer pixels, render only on change,
stop drawing offscreen/while hidden, and dispose graphics/listeners on unmount.
Reduced motion keeps static selectable states. WebGL failures retain usable DOM
content. Buffers are preserved because rendering is on demand; this also permits
explicit pixel verification. This is a bounded memory tradeoff, not a zero-cost
effect. The hero and study share one asynchronously loaded Three.js bundle.
Reference: [Three.js cleanup](https://threejs.org/manual/pages/cleanup.html),
[responsive rendering](https://threejs.org/manual/pages/responsive.html).

Use distinctly named TSX components and TS renderer helpers: Windows resolution
cannot distinguish same-stem filenames by letter case. A local collision was
fixed by `HeroBackdrop.tsx` / `heroDepthScene.ts`.

Mobile navigation is an expandable nonmodal navigation region; Escape closes it
and returns focus to its toggle. D003 uses full-width square-edged light frosted
navigation and the original logo colors without CSS filtering. The expanded
footer repeats the unmodified logo with sample/privacy/top links and API status.
Native anchors preserve scrolling and skip links.
Header color trial: lavender-to-palette-yellow (#e4da72) linear gradient with
translucent stops over the existing glass blur. The user accepted the initial
homepage direction, including the current header. Revert the trial by
removing the gradient override and restoring the supports background to
`rgb(242 238 249 / 68%)`. No layout or other surface colors changed.
Text survives switching source modes. The `/demo` route uses the existing reviewed
fixture adapter and resets back to home. Quote text is a static illustration of
the existing curated fixture, explicitly labelled; no live finding is inferred.

The demo sources and existing conditional judgments remain in
[[docs/product/Demo fixture review]]. No actual legal engines were added here.
Backend availability still controls intake; disabled deployments remain disabled.

Verification and remaining design scope:
[[docs/sessions/2026-09-29 - Glass homepage and evidence motion]], [[design]],
[[docs/product/UI direction]], [[TODO]].
