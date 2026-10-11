import type { CSSProperties, ReactNode } from "react";
import { B, C, F, keys, tween, windowed } from "../brand";

/** Shared source glass: a back plane, luminous edges and a quiet reading surface. */
export const EvidencePanel = ({ children, style, frame }: { children: ReactNode; style: CSSProperties; frame: number }) => (
  <div style={{ position: "absolute", ...style }}>
    <div style={{ position: "absolute", inset: 0, borderRadius: 18, transform: "translate(8px,10px)",
      background: "#21103B", border: "1px solid #9564DD66", boxShadow: "0 26px 45px #06020F66", opacity: .75 }} />
    <div style={{ position: "absolute", inset: 0, borderRadius: 18, overflow: "hidden", boxSizing: "border-box",
      background: "linear-gradient(135deg,#2D1850 0%,#1B0D35 42%,#130923 100%)", border: "1.5px solid #C9B3F25C",
      boxShadow: "inset 0 1px 0 #F4F0FB33,inset 0 -1px 0 #9564DD33,0 14px 40px #06020F55" }}>
      <div style={{ position: "absolute", left: 0, top: 0, right: 0, height: 54,
        background: "linear-gradient(90deg,#9564DD22,#C9B3F209,transparent)", borderBottom: "1px solid #C9B3F21A" }} />
      <div style={{ position: "absolute", left: 0, top: 20, bottom: 20, width: 3,
        background: `linear-gradient(180deg,transparent,${C.lilacSoft},${C.lilac},transparent)`, opacity: .7 }} />
      <div style={{ position: "absolute", right: 16, top: 10, width: 32, height: 2, background: C.yellow,
        opacity: .35 + Math.sin(frame / 36) * .1 }} />
      <div style={{ position: "relative", height: "100%", boxSizing: "border-box" }}>{children}</div>
    </div>
  </div>
);

// Native geometry shared with the source connectors. No 820px document scaling.
export const AUTHORITY_ROW_CENTERS = [416, 516, 616, 716] as const;
const AUTHORITY_ANCHORS = [
  { name: "Brown", cite: "347 U.S. 483", number: "01" },
  { name: "Miranda", cite: "384 U.S. 436", number: "02" },
  { name: "Obergefell", cite: "576 U.S. 644", number: "03" },
  { name: "Reference", cite: "999 U.S. 999", number: "04" },
] as const;

const AuthorityAnchors = ({ frame }: { frame: number }) => <div style={{ position: "absolute", inset: 0 }}>
  <div style={{ position: "absolute", left: 24, top: 27, fontFamily: F.mono, fontSize: 24, color: "#756987" }}>CITATION ANCHORS</div>
  <div style={{ position: "absolute", left: 24, top: 67, fontSize: 32, fontWeight: 700 }}>Draft filing</div>
  <div style={{ position: "absolute", left: 24, right: 24, top: 112, height: 2, background: "#D4C2EC" }} />
  {AUTHORITY_ANCHORS.map((item, index) => {
    const progress = tween(frame, [B.authorities[0] + 6 + index * 3, B.authorities[0] + 18 + index * 3], [0, 1]);
    return <div key={item.cite} style={{ position: "absolute", left: 18, right: 18, top: 126 + index * 100, height: 100,
      borderBottom: "1px solid #D8CBE8", boxSizing: "border-box", padding: "12px 10px",
      background: index === 3 ? "#9A94AE0D" : `rgba(149,100,221,${.09 * progress})`, opacity: progress }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span style={{ fontSize: 32, lineHeight: 1.1, fontWeight: 650 }}>{item.name}</span>
        <span style={{ fontFamily: F.mono, fontSize: 24, color: "#8B779E" }}>{item.number}</span>
      </div>
      <div style={{ fontFamily: F.mono, fontSize: 24, color: index === 3 ? "#756987" : C.purple, marginTop: 8 }}>{item.cite}</div>
    </div>;
  })}
  <div style={{ position: "absolute", left: 24, bottom: 18, fontSize: 24, color: "#756987" }}>Document → source</div>
</div>;

const K = [0,12,42,84,104,168,192,270,288,366,386,444,464,540,562,642,662,714,734];
const X = [1020,1020,1020,1020,900,900,840,840,840,840,900,900,900,900,1000,1000,1000,1000,1120];
const Y = [-650,-650,270,270,180,180,240,240,300,300,210,210,190,190,490,490,210,210,480];
const W = [650,650,650,650,820,820,330,330,440,440,820,820,820,820,150,150,720,720,100];
const H = [530,530,530,530,670,670,580,580,430,430,260,260,670,670,110,110,690,690,70];
const ROT = [-14,-14,-12,-12,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0];
export const SHEET_KEYS = { K, X, Y, W, H };

export const QUOTE_DRAFT = ["Separate","educational","facilities","are","inherently","equal."];
export const QUOTE_SOURCE = ["Separate","educational","facilities","are","inherently","unequal."];

export const QuoteWords = ({ frame, words, diffIndex, dark = false }: { frame: number; words: readonly string[]; diffIndex: number; dark?: boolean }) => (
  <div style={{ marginTop: 22, fontSize: 38, lineHeight: 1.28, fontWeight: 600 }}>
    “{words.map((word, i) => {
      const amount = tween(frame, [B.quotes[0] + 15 + i * 3, B.quotes[0] + 25 + i * 3], [0, 1]);
      return <span key={word}><span style={{ background: i === diffIndex ? (dark ? "rgba(149,100,221," : "rgba(240,114,107,") + .25 * amount + ")" : `rgba(149,100,221,${.06 * amount})`,
        boxShadow: i === diffIndex ? "inset 0 -" + 3 * amount + "px 0 " + (dark ? C.lilac : C.review) : undefined,
        color: i === diffIndex ? dark ? C.yellow : "#AE3E3A" : undefined }}>{word}</span>{i < words.length - 1 ? " " : ""}</span>;
    })}”
  </div>
);

const DocumentText = ({ frame }: { frame: number }) => {
  const rows = [
    ["01", "PUBLIC EDUCATION", "Brown v. Board of Education", "347 U.S. 483 (1954)"],
    ["02", "CUSTODIAL QUESTIONING", "Miranda v. Arizona", "384 U.S. 436 (1966)"],
    ["03", "MARRIAGE", "Obergefell v. Hodges", "576 U.S. 644 (2015)"],
    ["04", "QUOTATION COMPARISON", "Separate educational facilities", "are inherently equal."],
    ["05", "AUTHORITY REFERENCE", "Example v. Imaginary Agency", "999 U.S. 999 (2099)"],
  ];
  return <div style={{ width: 820, padding: "42px 50px", boxSizing: "border-box" }}>
    <div style={{ display: "flex", justifyContent: "space-between", fontFamily: F.mono, fontSize: 20, letterSpacing: ".12em", color: "#756987" }}><span>DRAFT MEMORANDUM</span><span>DEMO-001</span></div>
    <div style={{ fontSize: 36, fontWeight: 700, marginTop: 20 }}>Alex Example v. Demo Agency</div>
    <div style={{ marginTop: 12, fontSize: 22, color: "#756987" }}>Document / citations / source passages</div>
    <div style={{ height: 1, background: "#D8CDE8", margin: "26px 0" }} />
    {rows.map(([number, label, name, citation], i) => {
      const highlight = tween(frame, [B.parse[0] + 14 + i * 9, B.parse[0] + 23 + i * 9], [0,1]);
      return <div key={number} style={{ display: "flex", gap: 23, padding: "4px 0", lineHeight: 1.1, borderBottom: "1px solid #E2DAEC" }}>
        <span style={{ fontFamily: F.mono, fontSize: 22, paddingTop: 7, color: "#9E8CB7" }}>{number}</span>
        <div><div style={{ fontFamily: F.mono, fontSize: 17, color: "#756987", letterSpacing: ".1em" }}>{label}</div>
          <div style={{ fontSize: 25, fontWeight: 600, marginTop: 4 }}>{name}</div>
          <div style={{ fontSize: 23, marginTop: 3, background: "rgba(149,100,221," + .17 * highlight + ")", color: C.purple, display: "inline-block" }}>{citation}</div></div>
      </div>;
    })}
  </div>;
};

const PrivacyContent = ({ frame }: { frame: number }) => (
  <div style={{ padding: "42px 48px" }}>
    <div style={{ fontFamily: F.mono, fontSize: 21, color: "#756987", letterSpacing: ".1em" }}>IDENTIFIER PATTERNS</div>
    <div style={{ fontSize: 34, fontWeight: 700, marginTop: 16 }}>Details that need attention.</div>
    {[["SSN-shaped pattern","•••-••-3456"],["Date of birth","••/••/2000"],["Account number","••••••••6789"]].map(([label,value], i) =>
      <div key={label} style={{ marginTop: 20, padding: "14px 18px", display: "flex", alignItems: "center", justifyContent: "space-between", background: "#EDE6F6", borderRadius: 10,
        opacity: tween(frame, [B.privacy[0] + 16 + i * 7,B.privacy[0] + 27 + i * 7],[0,1]) }}>
        <div><div style={{ fontSize: 21, color: "#756987" }}>{label}</div><div style={{ fontFamily: F.mono, fontSize: 32, color: C.purple, marginTop: 5 }}>{value}</div></div>
        <span style={{ fontSize: 24, color: "#AE3E3A", border: "1px solid #AE3E3A", borderRadius: 6, padding: "7px 13px" }}>Detected</span>
      </div>)}
    <div style={{ marginTop: 28, paddingTop: 24, borderTop: "1px solid #D8CDE8", opacity: tween(frame,[B.privacy[0]+46,B.privacy[0]+60],[0,1]) }}>
      <div style={{ fontFamily: F.mono, fontSize: 20, color: "#756987", letterSpacing: ".1em" }}>DISCLOSURE CHECK</div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 14, fontSize: 27, fontWeight: 600 }}><span>AI-use heading</span><span style={{ color: "#AE3E3A" }}>Missing</span></div>
      <div style={{ marginTop: 12, fontSize: 23, color: "#756987" }}>Use of Generative AI</div>
    </div>
  </div>
);

const ReportContent = ({ frame }: { frame: number }) => (
  <div style={{ padding: "42px 44px" }}>
    <div style={{ display: "flex", justifyContent: "space-between", color: "#756987", fontFamily: F.mono, fontSize: 20, letterSpacing: ".1em" }}><span>PREFLIGHT / REPORT</span><span>DEMO-001</span></div>
    <div style={{ fontSize: 41, fontWeight: 700, marginTop: 25 }}>Evidence in view.</div>
    <div style={{ height: 2, background: C.lilac, margin: "25px 0" }} />
    {[
      ["QUOTATION","¶4 → Brown, 347 U.S. 483","equal.  ≠  unequal."],
      ["PROPOSITION","¶4 → Source passage","Claim and source differ"],
      ["PRIVACY","¶6 → Identifier patterns","Sensitive details located"],
    ].map(([label,path,detail],i) => <div key={label} style={{ padding: "19px 0", borderBottom: "1px solid #D8CDE8", opacity: tween(frame,[B.score[0]+18+i*5,B.score[0]+29+i*5],[0,1]) }}>
      <div style={{ fontFamily: F.mono, fontSize: 19, color: "#756987", letterSpacing: ".12em" }}>{label}</div>
      <div style={{ fontSize: 25, fontWeight: 600, marginTop: 8 }}>{path}</div>
      <div style={{ fontSize: 23, color: C.purple, marginTop: 6 }}>{detail}</div>
    </div>)}
    <div style={{ display: "flex", gap: 15, marginTop: 28, fontSize: 22, color: C.purple }}><span>Findings</span><span>·</span><span>Sources</span><span>·</span><span>Coverage</span></div>
  </div>
);

export const FilingSheet = ({ frame }: { frame: number }) => {
  if (frame < 12 || frame >= 734) return null;
  const w = keys(frame,K,W);
  const h = keys(frame,K,H);
  const isDocument = frame < B.authorities[0];
  const isAuthority = frame >= B.authorities[0] && frame < B.quotes[0];
  const isQuote = frame >= B.quotes[0] && frame < B.claims[0];
  const isClaim = frame >= B.claims[0] && frame < B.privacy[0];
  const isPrivacy = frame >= B.privacy[0] && frame < B.graph[0];
  const isNode = frame >= B.graph[0] && frame < B.score[0] + 12;
  const isReport = frame >= B.score[0] + 12;
  const contentOpacity = Math.min(...[B.authorities[0],B.quotes[0],B.claims[0],B.privacy[0],B.graph[0],B.score[0]+12].map(at => Math.abs(frame-at) < 5 ? Math.abs(frame-at)/5 : 1));
  return <div style={{ position: "absolute", left: keys(frame,K,X), top: keys(frame,K,Y), width: w, height: h, borderRadius: keys(frame,K,[14,14,14,14,14,14,12,12,18,18,18,18,18,18,28,28,18,18,30]),
    color: C.charcoal, fontFamily: F.sans,
    opacity: windowed(frame,12,734,9,12), transform: "perspective(1400px) rotateX(" + tween(frame,[42,104],[15,0]) + "deg) rotateZ(" + keys(frame,K,ROT) + "deg)",
    boxShadow: "0 38px 80px #06020F88,0 0 60px #9564DD26" }}>
    <div style={{ position: "absolute", inset: 0, borderRadius: "inherit", background: "#9564DD2B", border: "1px solid #C9B3F23D", transform: "translate(8px,12px)" }} />
    <div style={{ position: "absolute", inset: 0, borderRadius: "inherit", overflow: "hidden", background: "linear-gradient(135deg,#FFFFFF,#F4F0FB 44%,#E9E0F5)",
      border: "1px solid #FFFFFF99", boxShadow: "inset 0 1px 0 #FFFFFF,inset 0 -5px 0 #C9B3F22B" }}>
    <div style={{ position: "absolute", left: 10, top: 22, bottom: 22, width: 2, background: "linear-gradient(180deg,#9564DD00,#9564DD33,#9564DD00)" }} />
    <div style={{ position: "absolute", right: 0, top: 0, width: 55, height: 55, background: "linear-gradient(45deg,transparent 49%,#C9B3F21F 50%)", pointerEvents: "none" }} />
    <div style={{ opacity: contentOpacity * tween(frame, [B.logo[0], B.logo[0] + 6], [1, 0]) }}>
      {isDocument && <div style={{ transform: "scale(" + w/820 + ")", transformOrigin: "top left" }}><DocumentText frame={frame} /></div>}
      {isAuthority && <AuthorityAnchors frame={frame} />}
      {isQuote && <div style={{ padding: "30px 34px" }}><div style={{ fontFamily: F.mono, color: "#756987", fontSize: 24 }}>DRAFT FILING / ¶4</div><QuoteWords frame={frame} words={QUOTE_DRAFT} diffIndex={5} /><div style={{ fontSize: 24, color: "#AE3E3A", marginTop: 28, borderLeft: "3px solid #F0726B", paddingLeft: 14 }}>Changed word</div></div>}
      {isClaim && <div style={{ padding: "30px 40px" }}><div style={{ fontFamily: F.mono, color: "#756987", fontSize: 24 }}>DRAFT CLAIM / ¶4</div><div style={{ fontSize: 32, lineHeight: 1.35, marginTop: 18 }}><b style={{ color: C.purple }}>Brown, 347 U.S. 483</b>, permits racial segregation in public schools whenever funding is equal.</div></div>}
      {isPrivacy && <PrivacyContent frame={frame} />}
      {isNode && <div style={{ width: w, height: h, display: "grid", placeItems: "center", fontSize: 27, fontWeight: 700, color: C.purple }}>Filing</div>}
      {isReport && <ReportContent frame={frame} />}
    </div>
    {frame >= B.parse[0] && frame < B.parse[1] - 8 && <div style={{ position: "absolute", left: 0, right: 0, top: tween(frame,[B.parse[0]+8,B.parse[1]-12],[0,h]), height: 2, background: C.lilac, boxShadow: "0 0 30px 10px #9564DD55" }} />}
    </div>
  </div>;
};
