---
type: design
status: proposed
date: 2026-09-27
tags: [design, motion, frontend]
---
# UI direction

## October 11, 2026: continuing scope and glass composer preview

The user reaffirmed that the established UI scope applies throughout remaining
development. Future features follow the homepage identity, apple-design material/
interaction principles, clear steps, timely/quick navigation and accessible motion.
Persistent guidance is in [[AGENTS]]; scope feedback is
[[docs/feedback/FB-013 - Glass composer and continuing UI scope]].
The user explicitly requested a glass version of the homepage's rounded input box.
Its layout and behavior stay intact; a single lilac frosted surface, reflective
edge, depth and darker text replace the nearly opaque fill. Reduced transparency,
increased contrast and unsupported blur have solid fallbacks. This is a local
preview awaiting aesthetic review, not permission to redesign the rest of home.

## October 10, 2026: remaining workflow pages

After the first page, the user authorized redesigning every remaining page except
home. All non-home routes now share WorkflowShell: glass brand navigation,
active page links, persistent preparation shortcut and privacy/service footer.
Results retain the document steps and add direct overview/findings/source-checks/
relationships/report navigation. Finding selection brings evidence into view
with keyboard focus; graph and report inspection stay integrated in results.
Activity reflects actual saved status; settings explicitly distinguish unknown
capabilities; sample expectations remain separate from executed review outcomes.
Privacy/limits and not-found/loading/failure states use the same visual language.
The original homepage is unchanged. Motion is brief, responsive to input and
disabled for reduced-motion preferences; reduced transparency uses solid chrome.
Implementation and local verification: [[docs/sessions/2026-10-10 - Remaining workflow pages redesign]].
Task completion belongs to [[TODO]] D007. Broader accessibility, performance and
hosted release gates remain separate; no aesthetic acceptance is invented.

## October 10, 2026: first workflow page for review

The user requested one complete non-home page before continuing the redesign.
The prepared document/review workspace (`/analyses/:id`) now uses the installed
apple-design skill with the accepted homepage's logo, image, purple/yellow palette
and display font. Glass navigation, a clear three-step path and status-aware next
actions replace the generic sidebar on this route only. Details/findings expand
when needed; exact document text remains inspectable. Brief arrival/press feedback
has reduced-motion equivalents; reduced transparency uses a solid toolbar.
Desktop/mobile browser verification is recorded in
[[docs/sessions/2026-10-10 - Document workspace redesign]]. This first page is
implemented for visual review; user aesthetic approval and remaining pages are
pending. The homepage is unchanged. Scope: [[TODO]] D007;
feedback: [[docs/feedback/FB-012 - Match workflow pages to homepage theme]].

User references: AirForShare's centered text/file surface, Kombai's product
demonstrations and motion, GC Avalance display typography, a purple/lilac/yellow/
light-gray palette, and a dithered graphic reference. These are inspiration,
not permission to copy branding, assets or unsupported product claims.

Related: [[docs/feedback/FB-003 - Image-backed filing composer]],
[[docs/feedback/FB-002 - Plan visual design before final UI]],
[[docs/architecture/stack]], [[TODO]]. User authorized the first homepage and motion
implementation on September 29; final design acceptance remains open.

## First viewport
Full-bleed user-supplied HD image, with readable FilingGuard-AI display title over
it, not enclosed in a decorative hero card. Simple nav: Review, How it works,
Limits; Demo as a clear action. Centered translucent intake surface is a genuine
tool: Text / PDF / Demo tabs, editable text or PDF drop target, court selection,
AI-used checkbox and Run review. User approved this filing-focused composer.
Do not introduce general chat or arbitrary image uploads; OCR is out of scope.
Show a hint of the next section on desktop and mobile. Main content remains
usable without waiting for animations. Background image and font supplied.
The user's purple legal/technology illustration is saved unchanged at
`apps/web/src/assets/filingguard-background.png` from the Downloads PNG.
Its dense detail requires controlled heading contrast and a sufficiently opaque
composer surface. Verify responsive cropping without distortion during UI work.
User supplied `C:/Users/IT/Downloads/avalance font`, containing eight GC Avalance
Demo TTF weights. The included READ ME!!.txt restricts free use to personal use
and points to a paid commercial license. User subsequently reported direct creator
permission via DM for this site's use and authorized proceeding on that basis.
This is user-reported permission, not independently verified license evidence;
retain the DM with asset records. GC Avalance Bold is now copied into served assets
and embedded in the first homepage title; no alternative is required now.

## Scroll sequence
1. A document-to-citation-to-source sequence illustrates the actual review flow.
2. D006 implements a "How it works" process-film band below the hero, with concise
   context and a silent rendered loop; stack text/video on mobile. The user's
   choices supersede the earlier future-recording plan. Delivery, copy, pause
   controls and reduced-motion poster are specified in [[apps/video/brief/BRIEF]]
   and [[docs/decisions/ADR-010 - Remotion pipeline film]]. Desktop and mobile use
   separate authored compositions for readable evidence text. Exports pass
   metadata/size and desktop/mobile browser checks. October 7 completes the
   larger Authority white-card text and a lit evidence
   workbench, layered paper/glass and meaningful scan/link motion. See
   [[docs/feedback/FB-010 - Readable authority card in pipeline film]] and
   [[docs/feedback/FB-011 - Richer programmatic film direction]].
3. Evidence-focused examples show a quotation comparison and claim-authority
   relationship using clearly marked sample material, not invented live results.
4. Limits/privacy and human-review notice lead back to the composer.

No invented user statistics, citation coverage guarantees, testimonials or claims
of collaboration. Teams/multiple reviewers remain P2, not an advertised P0 feature.

## Pages and actions
- /: usable filing composer plus scroll narrative, not a marketing-only entrance.
- /analyses/:id: progress, coverage, findings and evidence detail; graph/report tabs.
- /activity: only the anonymous session's results, with delete and start-new actions.
- /settings: provider availability and public limits, never editable API secrets.
- /privacy: retention, provider processing and prototype limitations.
Session-scoped access and routes require actual services before becoming enabled.
User confirmed anonymous private sessions with automatic expiry and no signup for
P0. Activity is temporary session history, not an account archive. Losing the
session credential can lose access; closing the tab does not itself prove server
deletion. Retention notices must match the implemented server policy. Accounts
and shared team reviews remain P2. See
[[docs/decisions/ADR-004 - Truthful contracts and scoped evidence]].
Upload, run, retry, delete and export use familiar icon-plus-text commands.

## Visual and motion proposal
Purple #3E0F8D and lilac #9564DD are accents, not an all-purple wash. Yellow #E4DA72
marks selected emphasis, not error severity. Light gray #EEEEEE and charcoal give
review content readable neutral surfaces. Risk statuses also have text/icons.
GC Avalance is for brand/display only; reading and evidence need a legible text
font. No unlicensed embedding or silent font substitution.

GSAP + React scoping/cleanup + ScrollTrigger are proposed for one composed
entrance and a purposeful verification narrative. Transform/opacity first; no
scroll hijacking, perpetual decorative motion, pointer-dependent controls or
animating long evidence text. Mobile uses shorter unpinned transitions; reduced
motion removes parallax/scrubbing and shows all information immediately. Animate
UI progress only from real lifecycle events; narrative animation is illustrative.
Three.js is not required for this direction and is deferred unless a meaningful
3D interaction is chosen. Translucency needs an opaque fallback and contrast tests.

## Responsive acceptance
Inspect 360/390px phones, 768/1024px tablets and 1440px desktop; long brand words,
controls and findings cannot overlap or introduce page-wide horizontal scrolling.
Use explicit type sizes at breakpoints, not viewport-scaled fonts. Mobile wraps
FilingGuard-AI deliberately if needed. Touch targets >=44px, keyboard reachability,
focus indicators, accessible tabs, and readable contrast are required.

## References checked
- [Kombai](https://kombai.com/#models): live Chrome inspection showed product
  demonstrations, section navigation and media-driven presentation. Exact motion
  timing and implementation are not copied or claimed known.
- [Official GSAP skills](https://github.com/greensock/gsap-skills): core, timelines,
  ScrollTrigger, React and performance guidance installed with user approval.
- [GC Avalance creator](https://glyphonic.gumroad.com/l/gc-avalance): user will
  source the font; free download alone is not proof of web embedding rights.

User asked not to constrain current work by the deadline. The official recorded
submission time remains unchanged; visual work is still planning with assets supplied.

September 28 update: the missed deadline is historical; the user now intends ongoing
product development. Their own logo from Downloads/logo.png is copied unchanged
to apps/web/src/assets/filingguard-logo.png and rendered in the current shell.
The reviewed demo screen now exposes source-linked expectations, conditional notes
and reset with desktop/mobile checks. This is functional scaffolding; the image-backed
composer, Avalance display type, GSAP motion and final results design remain planned.
See [[apps/web/src/assets/README]] and
[[docs/sessions/2026-09-28 - Product continuation and reviewed demo]].

Additional user input pending: widget animations, grid animations and page motion.
The user will supply their detailed plan later. These are not specified, approved
animation sequences or implemented effects; preserve room for them without choosing
behavior now. See [[docs/feedback/FB-004 - Durable context and additional motion]].

September 28 refinement: the user authorizes choosing GSAP/Three.js/Motion to pursue
a distinctive interactive redesign. [[design]] owns the expanded choreography,
micro-interaction and performance brief. GSAP/CSS is selected for the initial plan;
one meaningful, lazy-loaded Three.js evidence scene is now a proposed prototype,
not a committed dependency or implemented effect. This refines the earlier blanket
Three.js deferral without replacing the supplied bitmap hero or dense review UI.
See [[docs/feedback/FB-005 - Distinctive interactive redesign]].

September 29 implementation: the user approved starting the first homepage and
motion pass. Supplied background/logo and Avalance Bold now render with the working
composer, mobile navigation, curated quote comparison and privacy/limits band.
GSAP entrance/panel transitions and CSS control feedback respect reduced motion.
The public deployment is unchanged; this first pass awaits user visual feedback.
Larger scroll narratives, optional Three.js, user video and detailed widget/grid
ideas remain future work. See [[docs/sessions/2026-09-29 - First homepage design]].
