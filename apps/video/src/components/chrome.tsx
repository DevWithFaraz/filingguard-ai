import React from "react";
import { AbsoluteFill } from "remotion";
import { B, C, DURATION, F, tween, windowed } from "../brand";

export const Background = ({ frame }: { frame: number }) => {
  const phase = frame / (DURATION - 1) * Math.PI * 2;
  const drift = Math.sin(phase);
  return <AbsoluteFill style={{ background: C.ink, overflow: "hidden" }}>
    <AbsoluteFill style={{ background: "linear-gradient(118deg,#0E0620 12%,#1C0B38 49%,#3E0F8D 79%,#170A33 100%)" }} />
    <div style={{ position: "absolute", right: -80, top: -180, width: 1280, height: 1220,
      background: "linear-gradient(132deg,transparent 28%,#9564DD18 29%,#C9B3F21A 38%,transparent 58%)",
      transform: "translateX(" + drift * 26 + "px) rotate(-9deg)" }} />
    <svg width="1920" height="1080" style={{ position: "absolute", inset: 0 }}>
      <defs>
        <linearGradient id="workbenchFloor" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#9564DD" stopOpacity=".04" /><stop offset=".65" stopColor="#9564DD" stopOpacity=".23" /><stop offset="1" stopColor="#3E0F8D" stopOpacity=".05" /></linearGradient>
        <linearGradient id="evidenceRibbon"><stop stopColor={C.lilac} stopOpacity="0" /><stop offset=".45" stopColor={C.lilac} stopOpacity=".27" /><stop offset=".8" stopColor={C.yellow} stopOpacity=".32" /><stop offset="1" stopColor={C.lilac} stopOpacity=".05" /></linearGradient>
        <linearGradient id="backlitGlass"><stop stopColor={C.lilacSoft} stopOpacity=".22" /><stop offset=".45" stopColor={C.lilac} stopOpacity=".035" /><stop offset="1" stopColor={C.paper} stopOpacity=".08" /></linearGradient>
        <pattern id="filmGrain" width="32" height="32" patternUnits="userSpaceOnUse"><circle cx="3" cy="4" r=".7" fill="#F4F0FB" /><circle cx="17" cy="11" r=".5" fill="#F4F0FB" /><circle cx="8" cy="27" r=".6" fill="#F4F0FB" /><circle cx="29" cy="21" r=".6" fill="#F4F0FB" /></pattern>
      </defs>
      <g transform={"translate(" + drift * 10 + " " + drift * 5 + ")"}>
        {/* Three filing contours form the walls of the evidence workbench. */}
        {[0, 1, 2].map(i => <g key={i} opacity={.56 - i * .12}>
          <path d={"M" + (1000 + i * 120) + " 238 L" + (1580 + i * 100) + " " + (54 + i * 35) + " L" + (1820 + i * 80) + " " + (444 + i * 90) + " L" + (1240 + i * 120) + " " + (628 + i * 125) + " Z"}
            fill="url(#backlitGlass)" stroke={C.lilacSoft} strokeOpacity=".22" strokeWidth="1.5" />
          {[0, 1, 2, 3, 4].map(j => <path key={j} d={"M" + (1100 + i * 120 + j * 16) + " " + (280 + j * 32) + " l 360 -114"} stroke={C.lilacSoft} strokeOpacity=".16" />)}
        </g>)}
        <path d="M748 949 L1690 997 L1852 745 L1046 653 Z" fill="#080314" fillOpacity=".62" />
        <path d="M748 931 L1690 979 L1852 727 L1046 635 Z" fill="url(#workbenchFloor)" stroke={C.lilac} strokeOpacity=".3" strokeWidth="2" />
        <path d="M748 931 L748 949 L1690 997 L1690 979" fill="#3E0F8D" fillOpacity=".2" stroke={C.lilac} strokeOpacity=".18" />
        {[0,1,2,3,4,5,6,7,8].map(i => <path key={i} d={"M"+(788+i*99)+" "+(935+i*5)+" L"+(1080+i*85)+" "+(650+i*8)} stroke={C.lilacSoft} strokeOpacity=".09" />)}
        {[0,1,2,3,4,5].map(i => <path key={i} d={"M"+(790+i*47)+" "+(890-i*45)+" L"+(1730+i*19)+" "+(929-i*40)} stroke={C.lilacSoft} strokeOpacity=".1" />)}
        <path d="M816 917 L1677 960 L1807 752" fill="none" stroke={C.lilac} strokeOpacity=".7" strokeWidth="2" />
        <path d="M1150 924 L1470 940" stroke={C.yellow} strokeOpacity=".6" strokeWidth="3" />
      </g>
      {/* Bundled paths echo the document-to-source relationships of the film. */}
      {Array.from({length:12},(_,i) => <path key={i} d={"M670 "+(820+i*8)+" C1030 "+(1050+i*7)+",1260 "+(260+i*19)+",1940 "+(360+i*12)}
        fill="none" stroke="url(#evidenceRibbon)" strokeWidth={i === 4 || i === 8 ? 1.8 : 1} opacity={i === 4 || i === 8 ? .85 : .4} />)}
      {[0,1,2].map(i => {
        const x=970+i*245+drift*30, y=855-i*122+Math.cos(phase+i)*12;
        return <g key={i} opacity=".5"><circle cx={x} cy={y} r="8" fill={C.ink} stroke={C.lilac} /><circle cx={x} cy={y} r="2.5" fill={C.yellow} /></g>;
      })}
      <path d="M68 620 C180 400 310 570 450 235 C560 -20 730 90 842 32" fill="none" stroke={C.lilac} strokeOpacity=".15" strokeWidth="1.5" />
      <path d="M42 658 C172 410 292 594 472 252 C591 -14 718 106 862 26" fill="none" stroke={C.lilac} strokeOpacity=".09" />
      <path d="M89 732 L89 755 L112 755 M1753 157 L1776 157 L1776 180" fill="none" stroke={C.yellow} strokeOpacity=".32" strokeWidth="2" />
      <rect width="1920" height="1080" fill="url(#filmGrain)" opacity=".12" />
      {[66, 1014].map((y) => <path key={y} d={"M 96 " + y + " H 1824"} stroke={C.lilac} strokeOpacity=".22" />)}
      {[72, 1848].map((x) => <path key={x} d={"M " + x + " 90 V 990"} stroke={C.lilac} strokeOpacity=".15" />)}
      <path d="M72 112V90H94 M1826 90H1848V112 M72 968V990H94 M1826 990H1848V968" fill="none" stroke={C.yellow} strokeWidth="2" opacity=".7" />
    </svg>
    <AbsoluteFill style={{ background: "linear-gradient(90deg,#0E062080 0%,#0E062000 46%,#0E062000 86%,#0E062033 100%),linear-gradient(0deg,#0E062088,transparent 20%,transparent 84%,#0E062044)" }} />
  </AbsoluteFill>;
};

const stages = [
  { label: "Extract", at: B.parse }, { label: "Sources", at: B.authorities },
  { label: "Quotes", at: B.quotes }, { label: "Claims", at: B.claims },
  { label: "Privacy", at: B.privacy }, { label: "Graph", at: B.graph }, { label: "Report", at: B.score },
] as const;

export const Hud = ({ frame }: { frame: number }) => {
  const opacity = windowed(frame, 12, DURATION - 12, 10, 10);
  const railOpacity = windowed(frame, B.parse[0] - 12, B.logo[0], 12, 12);
  const current = stages.findIndex((stage) => frame >= stage.at[0] && frame < stage.at[1]);
  const active = Math.max(0, current);
  return <AbsoluteFill style={{ pointerEvents: "none", fontFamily: F.mono }}>
    <div style={{ position: "absolute", left: 112, top: 101, opacity, fontSize: 22, color: C.lilacSoft, letterSpacing: ".13em", display: "flex", gap: 16, alignItems: "center" }}>
      <span style={{ width: 18, height: 18, border: "1px solid " + C.yellow + "88", padding: 4, boxSizing: "border-box", transform: "rotate(45deg)" }}><span style={{ display:"block",width:"100%",height:"100%",background:C.yellow }} /></span>
      FILINGGUARD AI <span style={{ opacity: .5 }}>/ PREFLIGHT</span>
    </div>
    <div style={{ position: "absolute", right: 112, top: 101, opacity, fontSize: 22, letterSpacing: ".1em", color: C.lilacSoft }}>DOCUMENT → EVIDENCE</div>
    <div style={{ position: "absolute", left: 120, top: 952, right: 120, display: "flex", justifyContent: "space-between", opacity: railOpacity }}>
      <div style={{ position: "absolute", left: 0, right: 0, top: 10, height: 1, background: C.lilac + "33" }} />
      <div style={{ position: "absolute", left: 0, top: 10, height: 2, width: (active / (stages.length - 1)) * 100 + "%", background: "linear-gradient(90deg," + C.lilac + "," + C.yellow + ")", opacity:.7 }} />
      {stages.map((stage, i) => <div key={stage.label} style={{ position: "relative", width: 150, textAlign: i === 0 ? "left" : i === stages.length - 1 ? "right" : "center", color: i === active ? C.paper : C.lilacSoft + "99" }}>
        <span style={{ display: "inline-block", width: 18, height: 18, borderRadius: "50%", background: i < active ? C.lilac : C.ink, border: "2px solid " + (i === active ? C.yellow : C.lilac + "66"), boxShadow: i === active ? "0 0 0 7px #E4DA7214,0 0 20px #E4DA7255" : undefined }} />
        <div style={{ marginTop: 18, fontSize: 20, letterSpacing: ".09em", textTransform: "uppercase" }}>{stage.label}</div>
      </div>)}
    </div>
  </AbsoluteFill>;
};

export const Caption: React.FC<{
  frame: number; start: number; end: number; eyebrow: string; title: string; sub: string; top?: number;
}> = ({ frame, start, end, eyebrow, title, sub, top = 325 }) => {
  if (frame < start || frame >= end) return null;
  const opacity = windowed(frame, Math.max(12, start), end, 10, 6);
  const rise = tween(frame, [start + 5, start + 21], [28, 0]);
  return <div style={{ position: "absolute", left: 120, top, width: 640, opacity, transform: "translateY(" + rise + "px)", fontFamily: F.sans }}>
    <div style={{ fontFamily: F.mono, fontSize: 23, color: C.yellow, letterSpacing: ".13em", textTransform: "uppercase", display:"flex",alignItems:"center",gap:17 }}><span style={{width:26,height:2,background:C.yellow}} />{eyebrow}</div>
    <div style={{ fontSize: 80, fontWeight: 750, lineHeight: 1.06, marginTop: 26, color: C.paper, letterSpacing: 0, textShadow:"0 5px 28px #06020F33" }}>{title}</div>
    <div style={{ fontSize: 30, lineHeight: 1.45, maxWidth: 570, marginTop: 28, color: "#CFC6E4" }}>{sub}</div>
    <div style={{ display:"flex",alignItems:"center",gap:10,marginTop:38 }}><div style={{ width: 88, height: 3, background: "linear-gradient(90deg,"+C.lilac+","+C.lilacSoft+")" }} /><span style={{width:4,height:4,background:C.lilac,borderRadius:"50%"}} /></div>
  </div>;
};

export type Status = "resolved" | "review" | "partial" | "unknown";
const statusStyles = {
  resolved: { color: C.resolved, icon: "✓" }, review: { color: C.review, icon: "!" },
  partial: { color: C.partial, icon: "~" }, unknown: { color: C.unknown, icon: "?" },
};
export const StatusPill: React.FC<{ status: Status; label: string; size?: number; style?: React.CSSProperties }> = ({ status, label, size = 22, style }) => {
  const state = statusStyles[status];
  return <span style={{ display: "inline-flex", gap: 9, alignItems: "center", padding: "8px 12px", borderRadius: 8,
    fontFamily: F.sans, fontWeight: 600, whiteSpace: "nowrap", fontSize: size, color: state.color, background: state.color + "18", border: "1px solid " + state.color + "55", ...style }}>
    <span style={{ width: size, height: size, borderRadius: "50%", color: C.ink, background: state.color, display: "inline-grid", placeItems: "center", fontSize: size * .7 }}>{state.icon}</span>{label}
  </span>;
};
