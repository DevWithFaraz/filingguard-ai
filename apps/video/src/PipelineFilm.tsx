import { useEffect, useState } from "react";
import { AbsoluteFill, cancelRender, continueRender, delayRender, staticFile, useCurrentFrame } from "remotion";
import { Background, Caption, Hud } from "./components/chrome";
import { FilingSheet } from "./components/FilingSheet";
import { B, C, F, tween, windowed } from "./brand";
import { IntakeScene } from "./scenes/IntakeScene";
import { AuthoritiesScene } from "./scenes/AuthoritiesScene";
import { QuotesScene } from "./scenes/QuotesScene";
import { ClaimsScene } from "./scenes/ClaimsScene";
import { GraphScene } from "./scenes/GraphScene";
import { ScoreScene } from "./scenes/ScoreScene";
import { LogoScene } from "./scenes/LogoScene";
import { MobileFilm } from "./MobileFilm";

let loadedFonts: Promise<void> | undefined;
const ensureFonts = () => {
  loadedFonts ??= Promise.all([
    new FontFace("Film Inter", "url(" + staticFile("fonts/inter-latin.woff2") + ")", { weight: "100 900" }).load(),
    new FontFace("Film Mono", "url(" + staticFile("fonts/jetbrains-mono-latin.woff2") + ")", { weight: "100 800" }).load(),
  ]).then((fonts) => { fonts.forEach((font) => document.fonts.add(font)); });
  return loadedFonts;
};

const ParsingScene = ({ frame }: { frame: number }) => {
  const [start, end] = B.parse;
  if (frame < start || frame >= end) return null;
  return <>
    <Caption frame={frame} start={start} end={end} eyebrow="02 / DOCUMENT ENGINE"
      title="Text deconstruction" sub="From a page of words to passages, citations and precise locations." />
    <div style={{ position: "absolute", left: 880, top: 866, width: 840, display: "flex", justifyContent: "center", gap: 24,
      opacity: windowed(frame, start + 26, end, 8, 8), fontFamily: F.mono, fontSize: 23 }}>
      {["PARAGRAPHS", "CITATIONS", "QUOTATIONS"].map((label, i) => <span key={label} style={{ padding: "12px 18px", border: "1px solid " + C.lilac + "66",
        borderRadius: 8, background: "linear-gradient(135deg,#3E0F8DDD,#170A33EE)", boxShadow:"0 6px 0 #0E0620,0 14px 24px #06020F44", color: i === 1 ? C.yellow : C.lilacSoft, transform: "translateY(" + tween(frame, [start + 28 + i * 5, start + 44 + i * 5], [22, 0]) + "px)" }}><span style={{color:C.yellow,marginRight:10}}>⌁</span>{label}</span>)}
    </div>
  </>;
};

const PrivacyScene = ({ frame }: { frame: number }) => {
  const [start, end] = B.privacy;
  if (frame < start || frame >= end) return null;
  return <Caption frame={frame} start={start} end={end} eyebrow="06 / LOCAL CHECKS"
    title="Privacy & court rules" sub="Sensitive patterns and disclosure requirements, located in the filing." />;
};

export const PipelineFilm = ({ mobile = false }: { mobile?: boolean }) => {
  const frame = useCurrentFrame();
  const [handle] = useState(() => delayRender("Loading local film fonts"));
  useEffect(() => {
    let mounted = true;
    ensureFonts().then(() => { if (mounted) continueRender(handle); }).catch(cancelRender);
    return () => { mounted = false; };
  }, [handle]);
  if (mobile) return <AbsoluteFill style={{ overflow: "hidden", fontFamily: F.sans }}>
    <Background frame={frame} />
    <MobileFilm frame={frame} />
  </AbsoluteFill>;
  return <AbsoluteFill style={{ overflow: "hidden", fontFamily: F.sans }}>
    <Background frame={frame} />
    <IntakeScene frame={frame} />
    <GraphScene frame={frame} />
    <FilingSheet frame={frame} />
    <ParsingScene frame={frame} />
    <AuthoritiesScene frame={frame} />
    <QuotesScene frame={frame} />
    <ClaimsScene frame={frame} />
    <PrivacyScene frame={frame} />
    <ScoreScene frame={frame} />
    <LogoScene frame={frame} />
    <Hud frame={frame} />
  </AbsoluteFill>;
};
