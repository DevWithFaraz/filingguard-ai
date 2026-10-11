# Pipeline film review — October 7, 2026

Task: [[TODO|D006]]. Criteria: [[apps/video/brief/CRITIQUE]]. This records
observed output and design judgments; task status remains in [[TODO]]. The
October 7 revision responds to [[docs/feedback/FB-010 - Readable authority card in pipeline film]]
and [[docs/feedback/FB-011 - Richer programmatic film direction]].

## Scope and inspected evidence

Desktop `PipelineFilm`: inspected the 20 newly rendered PNG samples at frames
0, 60, 144, 180, 192, 210, 240, 279, 336, 376, 414, 454, 504, 551, 594, 652,
672, 724, 756 and 779 in `out/stills`. Following the final source repairs,
frames 594, 690 and 724 were rendered again and inspected. These samples are
1920×1080 source renders, not decoded website media.

Mobile `PipelineFilmMobile`: the mobile reviewer inspected nine keyframes
(60, 144, 240, 336, 420, 510, 612, 690, 756) and five transition samples
(96, 180, 280, 550, 724). The evidence reviewer independently inspected the
same 14 PNGs in `out/mobile-stills`. Settled frames 144 and 690 were rerendered
after mobile spacing repairs. Transition 96 predates the parser spacing-only
repair; the final parser layout is represented by frame 144.

PNG samples and production intermediates remain under ignored `out`. A later
small-batch still capture overwrites `manifest.json`, so its last frame list is
not the complete review inventory above.

## Static critique

The desktop and mobile reviewers assigned the following scores to output they
actually inspected. Both renditions meet the static target for the seven rated
dimensions. Motion was unscored during this static round; actual playback
evidence is recorded separately. These scores do not establish the user's
aesthetic acceptance.

- **Brand — desktop 9/10, mobile 9/10.** The purple/lilac palette, yellow focus
  accents, Inter and citation mono type follow [[apps/video/brief/BRAND]]. The
  original PNG is intact on a light card at settled frame 756 in both
  renditions. Layered paper, glass edges, filing contours and a perspective
  workbench add depth while retaining a restrained reading surface.
- **Hierarchy — desktop 8/10, mobile 8/10.** Desktop stage titles remain the
  first reading point, followed by the filing/source comparison. Authority
  cards expose a consistent citation, name and source-ID order. Mobile uses
  one large stage title with simplified evidence panels. The desktop claim
  passage is the densest scene; its reading time still needs playback review.
- **Readability — desktop 8/10, mobile 8/10.** At inspected source size, native
  32px authority names and 24px citations replace the unreadable scaled full
  document. Quote words and the precise `equal.` / `unequal.` change remain
  clear. Mobile uses substantially larger evidence text, with the `un` prefix
  isolated. Inspection of full-size PNGs does not prove readability at the
  actual phone or homepage display size.
- **Composition — desktop 8/10, mobile 8/10.** Reviewed settled panels have
  clear separation and contain their essential text. The privacy disclosure
  line and report footer remain inside the desktop sheet. Mobile parser chips
  retain a bottom margin and report columns separate Privacy from its ¶6
  locator. Final desktop graph frame 594 clears the Quote ring from the source
  excerpt; final frame 724 has no exposed report text below the logo card.
- **Continuity — desktop 8/10, mobile 8/10.** Sampled desktop transitions retain
  the same filing object as its geometry changes. Authority source surfaces
  are absent at frames 180 and 192, after which frame 210 shows the separate
  source cards and accurate row connectors. Mobile samples preserve the
  title/panel grammar across beats. This rates sampled visual relationships,
  not the smoothness of intervening frames.
- **Evidence — desktop 9/10, mobile 9/10.** Brown, Miranda and Obergefell keep
  their curated citation/source identities. The unresolved reference is
  visibly distinct. Draft/source quotation changes are precisely paired;
  the claim scene uses the selected Brown majority passage. No percentage,
  live latency, automated approval or fabricated confidence result appears.
- **Copy — desktop 9/10, mobile 9/10.** Stage headings retain the agreed process
  wording, including Authority lookup, Quote forensics and Proposition review.
  Report copy describes findings, sources and document locations. The rejected
  review/redaction/sample overlays are absent from the inspected frames.
- **Motion — unassigned in both renditions.** Stills expose selected entrance
  states and settled layouts. They cannot establish a comfortable reading
  window, easing quality, compression stability or a seamless playback loop.

## Repairs confirmed in the final static round

[[docs/issues/BUG-008 - Authority transition overlaps source cards]] is addressed
by withholding source surfaces until the filing clears them. Frames 180 and
192 show the readable citation sheet without source cards; frames 210 and 240
show separated source surfaces and connectors aligned to their native rows.

The desktop graph Quote node was moved from y600 to y648. Rerendered frame 594
shows the ring separated from the source-excerpt panel. The report content now
fades during frames 714–720; rerendered frame 724 shows the incoming logo card
without report text exposed beneath it. Frame 690 confirms the settled report
footer still fits.

The mobile parser's lower chips were previously clipped. Adjusted citation/body
spacing and rerendered frame 144 show all three chips inside the paper. Wider
report columns and rerendered frame 690 remove the Privacy/¶6 near-collision.

## Source and text pairing

The source identities are retained from [[data/demo/curated-v1/README]] and
`data/demo/curated-v1/sources.json`: Brown `347 U.S. 483` / CourtListener
`105221`, Miranda `384 U.S. 436` / `107252`, and Obergefell `576 U.S. 644` /
`2812209`. Their on-screen Cached labels describe retained public snapshots.
`999 U.S. 999` remains the fixture's deliberately unresolved reference; it is
not presented as the result of a live database search.

The altered draft sentence is “Separate educational facilities are inherently
equal.” The source sentence is “Separate educational facilities are inherently
unequal.” Desktop highlights the changed word; mobile also isolates the added
`un` prefix. Both retain the source citation and distinguish the draft.

The desktop proposition scene uses the exact first two sentences selected by
`brown-misrepresented` in `data/demo/curated-v1/scenarios.json`, present in the
cached Brown text at line 275. This is the majority passage, including “has no
place” and “inherently unequal,” rather than a dissent in the combined snapshot.
The mobile draft label “Segregation permitted” is a concise claim summary,
paired with the exact source sentence and labeled Draft claim rather than
presented as a quotation. The graph and report retain the ¶4/source pairing;
privacy findings retain the ¶6 locator.

Authoring this curated pairing does not verify backend legal-engine behavior.
No live provider call or new legal finding was made for this review.

## Authored endpoint check

Desktop source PNGs at frames 0 and 779 have identical SHA256 values:
`DB81C2E0392BC228107BA79E2989BDBAAC3FD3C0D75FA71F58DDB0F192F56ACF`.
Their visible content is the same quiet background with foreground elements
gone. Equal endpoints support the authored seam state; they do not prove
playback pacing, the transition into/out of the seam, or decoder behavior.

## Encoded-frame review — final October 7 revision

The evidence reviewer inspected all 44 freshly decoded PNGs from the final four
website assets: desktop MP4, desktop WebM, mobile MP4 and mobile WebM, each at
frames 0, 180, 192, 210, 240, 336, 594, 690, 724, 756 and 779. Their native
dimensions are 2560×1440 desktop and 1920×1080 mobile. The decoding manifest
records `2026-10-07T11:17:28.713Z`; all 44 PNG modification times fall between
11:16:56 and 11:17:28 UTC, after the final media-report measurement at
`2026-10-07T11:13:41.390Z`. These samples therefore represent the revised
exports rather than the previous day's encodes.

- **Authority and transition:** desktop frames 180/192 retain the focused filing
  without premature source cards; frames 210/240 keep the source surfaces
  separated and connectors aligned. Native authority names, citations and
  source IDs remain readable in both compressed desktop formats. Mobile rows
  enter sequentially, with Cached and Unresolved labels kept distinct.
- **Quote comparison:** frame 336 in all four formats retains the exact Brown
  sentence, the draft `equal.` / source `unequal.` pairing and the highlighted
  difference. Mobile source text remains inside its panel, including the final
  period and highlighted `un` prefix. The inequality connector stays visible.
- **Graph and report:** frame 594 retains clear node labels and the filing/source
  relationship. Desktop's Quote ring clears the source excerpt; mobile status
  labels stay inside their boxes. Frame 690 has an unclipped desktop footer and
  separated mobile Privacy/¶6 columns.
- **Brand and endpoints:** frame 724 has no residual report text exposed below
  the incoming logo card. Settled frame 756 retains the original PNG's ratio,
  purple/yellow colors and clean light-card presentation. Decoded frames 0/779
  share the intended quiet background layout. Compression produces different
  fine texture in these endpoint frames; the source-PNG hash equality above
  does not imply byte-identical encoded endpoints.

There is no blocking clipping, evidence mismatch or essential-text degradation
in these samples. WebM smooths some grain and shows faint tonal steps in the
large dark-purple gradient, especially the quiet endpoint; MP4 retains more
fine texture. Neither sampled format loses the essential comparison or source
identity. The seven static scores remain unchanged after compressed inspection.
These decoded samples cannot establish temporal shimmer, compression pumping,
reading pace or decoder continuity.

The fresh `out/media-report.json` records a passing media check: both masters
and all four web assets are 26 seconds at 30 fps, with no audio track. Desktop
website MP4/WebM sizes are 6,545,687 / 5,133,879 bytes; mobile MP4/WebM sizes are
4,784,963 / 3,562,714 bytes. Each passes its configured byte budget. The 1920×1080
WebP poster is 83,874 bytes and also passes its budget. Delivery metadata
confirms dimensions and encoding, not visual pacing or physical-device speed.

Actual browser playback observations and the motion score belong in a separate
playback record below. Physical-device performance and the user's aesthetic
acceptance remain outside this encoded-frame review.

## Browser playback and final motion critique

The installed-Chrome run completed 22/22 desktop/mobile cases with one worker.
After a mobile description whitespace repair, the existing layout/rendition case
passed again on both projects (2/2). Normal playback ran uninterrupted through
all nine beats and wrapped once in each project. Both selected the WebM assets:
desktop 2560×1440 and mobile 1920×1080, duration 26 seconds. The traces captured 777
and 778 callbacks respectively, with nine distinct nonblank beat samples and zero
page errors. Mean callback gaps were about 33.4ms; maximum gaps 66.5/77ms.
These are measurements from this local Chrome run, not a physical-phone benchmark.

Root reviewed the actual homepage-sized quotation screenshot and the 390px mobile
section capture, plus continuous-playback graph/brand screenshots. Essential
comparison words remain clear, and the mobile description now reads “brief to”.
The 26-second film has brisk windows: proposition 2.6 seconds, report 2.4 seconds.
They show the process and essential contrast; reading every passage word for word
requires pausing. The settled panels and visible pause control support that use.

**Motion — desktop 8/10, mobile 8/10.** Entrances, scan/highlight movements and
evidence-path packets follow the stage sequence; settled evidence remains clear
in the sampled playback captures. Continuous decoding and the wrap checks pass.
The first/last background layout aligns, while WebM's fine grain is smoothed
differently at the endpoints. That minor codec texture difference remains a
quality limitation; no byte-identical encoded seam is claimed. Complete traces
and sampled screenshots establish the tested playback behavior, rather than an
eyeball inspection of every intervening frame. All eight critique dimensions now
meet the internal target. User aesthetic acceptance remains open.

Evidence: `.runtime/pipeline-loop-{desktop,mobile}.json`,
`.runtime/pipeline-loop-{desktop,mobile}-{11.2,20.4,24.5}.png`, and
`.runtime/pipeline-film-{desktop,mobile}.png`. The descriptions and full results
are recorded in [[docs/sessions/2026-10-07 - Pipeline film visual revision]].

[[apps/video/brief/BRIEF]] | [[apps/video/brief/BEATS]] |
[[apps/video/README]] | [[docs/sessions/2026-10-07 - Pipeline film visual revision]]
