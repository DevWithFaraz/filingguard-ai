import type { CSSProperties, ReactNode } from "react";
import { Img, staticFile } from "remotion";
import { B, C, F, tween, windowed } from "./brand";
import { QUOTE_DRAFT, QUOTE_SOURCE } from "./components/FilingSheet";

const BEATS = [
  { key: "intake", title: "Upload brief", span: B.intake },
  { key: "parse", title: "Text deconstruction", span: B.parse },
  { key: "authorities", title: "Authority lookup", span: B.authorities },
  { key: "quotes", title: "Quote forensics", span: B.quotes },
  { key: "claims", title: "Proposition review", span: B.claims },
  { key: "privacy", title: "Privacy & court rules", span: B.privacy },
  { key: "graph", title: "Risk mapping", span: B.graph },
  { key: "score", title: "Evidence report", span: B.score },
  { key: "logo", title: "CI/CD for court filings", span: B.logo },
] as const;

const glass: CSSProperties = {
  border: "2px solid rgba(201,179,242,0.48)", borderRadius: 26,
  background: "linear-gradient(135deg, #301454F5, #190D32FA 65%)",
  boxShadow: "0 22px 48px #06020F77, inset 0 2px 0 #D4BEFF40, inset 0 -2px 0 #10051B",
  boxSizing: "border-box",
};

const Paper = ({ children, style }: { children: ReactNode; style?: CSSProperties }) => (
  <div style={{ position: "absolute", left: 120, top: 370, width: 1680, height: 520, ...style }}>
    {[2, 1].map(layer => <div key={layer} style={{ position: "absolute", inset: 0, borderRadius: 26,
      transform: `translate(${layer * 9}px, ${layer * 11}px) rotate(${layer * .25}deg)`,
      background: layer === 2 ? "#756094" : "#BFB0D5", border: "2px solid #D8C7EC99",
      boxShadow: layer === 2 ? "0 34px 64px #06020F88" : undefined }} />)}
    <div style={{ position: "relative", width: "100%", height: "100%", borderRadius: 26,
      background: "linear-gradient(135deg, #FBF8FF, #F4F0FB 58%, #E7DFF2)", color: C.charcoal,
      padding: "34px 44px", boxSizing: "border-box", overflow: "hidden",
      border: "2px solid #EEE4FF", boxShadow: "inset 0 3px 0 #FFFFFF, inset -3px -3px 0 #CCBBDC88" }}>
      {children}
    </div>
    <div style={{ position: "absolute", left: 30, right: 30, top: -1, height: 3,
      background: "linear-gradient(90deg, transparent, #FFFFFF 20%, #E4DA72 78%, transparent)" }} />
  </div>
);

const IntakePanel = ({ frame }: { frame: number }) => {
  const land = tween(frame, [12, 44], [0, 1]);
  return <>
    <div style={{ ...glass, position: "absolute", left: 140, top: 802, width: 1640, height: 128,
      transform: "perspective(1600px) rotateX(44deg)", borderColor: C.lilac,
      boxShadow: "0 20px 50px #06020F, inset 0 0 38px #9564DD35" }} />
    <div style={{ position: "absolute", left: 230, top: 874, width: 1460, height: 5,
      background: C.yellow, boxShadow: "0 0 24px #E4DA7299", opacity: land }} />
    <Paper style={{ transform: `perspective(1600px) translateY(${110 * (1 - land)}px) rotateX(${16 * (1 - land)}deg) rotateZ(${-2 * (1 - land)}deg)` }}>
      <div style={{ fontSize: 62, fontFamily: F.mono, color: "#756987" }}>DRAFT MEMORANDUM</div>
      <div style={{ fontSize: 102, lineHeight: 1.08, fontWeight: 600, marginTop: 30 }}>Alex Example v. Demo Agency</div>
      <div style={{ marginTop: 44, display: "flex", gap: 20 }}>{[1, .82, .65].map((width, i) =>
        <div key={i} style={{ height: 72, width: `${width * 30}%`, borderRadius: 8,
          background: i === 1 ? "#D5C2EF" : "#E6DDEF", transform: `scaleX(${tween(frame, [28 + i * 5, 46 + i * 5], [.7, 1])})`, transformOrigin: "left" }} />)}</div>
      <div style={{ fontSize: 60, color: C.purple, marginTop: 28,
        opacity: tween(frame, [38, 53], [0, 1]) }}>Document → evidence</div>
      <svg width={130} height={130} style={{ position: "absolute", right: 48, top: 32, opacity: .35 }}>
        <path d="M26 16H78L106 44V112H26Z M78 16V44H106 M42 65H89 M42 82H78 M42 99H67"
          stroke={C.purple} strokeWidth={5} fill="none" strokeLinejoin="round" />
      </svg>
    </Paper>
  </>;
};

const ParsePanel = ({ frame }: { frame: number }) => {
  const start = B.parse[0];
  const scan = tween(frame, [start + 8, B.parse[1] - 12], [54, 500], value => value);
  return <Paper style={{ transform: `perspective(1600px) rotateX(${tween(frame, [start, start + 20], [5, 0])}deg)` }}>
    <div style={{ fontSize: 52, fontFamily: F.mono, color: "#756987" }}>PARAGRAPH / CITATION / QUOTATION</div>
    <div style={{ fontSize: 90, color: C.purple, fontWeight: 600, marginTop: 20,
      background: `rgba(149,100,221,${tween(frame, [start + 12, start + 28], [0, .12])})`, display: "inline-block" }}>Brown · 347 U.S. 483</div>
    <div style={{ fontSize: 70, lineHeight: 1.12, marginTop: 18 }}>Separate educational facilities are inherently equal.</div>
    <div style={{ display: "flex", gap: 22, marginTop: 14 }}>{["¶4", "347 U.S. 483", "“equal.”"].map((label, i) => {
      const lift = tween(frame, [start + 18 + i * 7, start + 32 + i * 7], [0, 1]);
      return <span key={label} style={{ fontFamily: F.mono, fontSize: 48, color: C.purple,
        padding: "8px 22px", background: "#E6DCF3", border: "2px solid #B8A0D7", borderRadius: 12,
        opacity: lift, transform: `translateY(${38 * (1 - lift)}px)`, boxShadow: "0 7px 12px #B8A0D744" }}>{label}</span>;
    })}</div>
    <div style={{ position: "absolute", left: 0, right: 0, top: scan - 36, height: 40,
      background: "linear-gradient(transparent, #9564DD33)", borderBottom: "4px solid #9564DD",
      boxShadow: "0 6px 14px #9564DD44" }} />
  </Paper>;
};

const AuthorityRows = ({ frame }: { frame: number }) => {
  const rows = [
    ["Brown", "347 U.S. 483", "✓ Cached", C.resolved],
    ["Miranda", "384 U.S. 436", "✓ Cached", C.resolved],
    ["Obergefell", "576 U.S. 644", "✓ Cached", C.resolved],
    ["Reference", "999 U.S. 999", "? Unresolved", C.unknown],
  ];
  return <>
    {rows.map(([name, cite, status, color], i) => {
      const enter = tween(frame, [B.authorities[0] + 6 + i * 7, B.authorities[0] + 24 + i * 7], [0, 1]);
      const travel = tween(frame, [B.authorities[0] + 26 + i * 7, B.authorities[0] + 50 + i * 7], [0, 1], value => value);
      const focus = i === 0 ? tween(frame, [B.authorities[0] + 36, B.authorities[0] + 54], [0, 1]) : 0;
      return <div key={cite} style={{ ...glass, position: "absolute", left: 120, top: 370 + i * 125,
        width: 1680, height: 112, padding: "16px 34px", display: "grid", gridTemplateColumns: "480px 660px 1fr", alignItems: "center",
        opacity: enter, transform: `perspective(1600px) translateX(${(i % 2 ? 44 : -44) * (1 - enter)}px) rotateX(${8 * (1 - enter)}deg)`,
        borderColor: i === 0 && focus > 0 ? `rgba(228,218,114,${.45 + .4 * focus})` : "#C9B3F266",
        boxShadow: `0 18px 32px #06020F88, inset 0 2px 0 #D4BEFF44, 0 0 ${26 * focus}px #E4DA7222` }}>
        <span style={{ fontSize: 72, fontWeight: 600, color: C.paper }}>{name}</span>
        <span style={{ fontFamily: F.mono, fontSize: 76, color: C.lilacSoft }}>{cite}</span>
        <span style={{ fontSize: 58, color, whiteSpace: "nowrap" }}>{status}</span>
        <div style={{ position: "absolute", left: 34, right: 34, bottom: 6, height: 2, background: "#9564DD44" }} />
        <div style={{ position: "absolute", left: 34 + travel * 1598, bottom: 2, width: 9, height: 9, borderRadius: "50%",
          background: i === 3 ? C.unknown : C.yellow, opacity: windowed(frame, B.authorities[0] + 26 + i * 7, B.authorities[0] + 57 + i * 7, 4, 7),
          boxShadow: "0 0 14px #E4DA72AA" }} />
      </div>;
    })}
    <div style={{ position: "absolute", left: 120, top: 925, fontSize: 54, color: C.lilacSoft }}>
      CourtListener / cached opinions
    </div>
  </>;
};

const QuotePanel = ({ frame, source, claim = false }: { frame: number; source: boolean; claim?: boolean }) => {
  const words = source ? QUOTE_SOURCE : QUOTE_DRAFT;
  const start = claim ? B.claims[0] : B.quotes[0];
  const enter = tween(frame, [start + (source ? 4 : 0), start + 19 + (source ? 4 : 0)], [0, 1]);
  const reveal = tween(frame, [start + 19, start + 37], [0, 1]);
  const color = source ? C.yellow : "#AE3E3A";
  return <div style={{ ...glass, position: "absolute", left: source ? 1010 : 140, top: 370, width: 770, height: 500,
    padding: "20px 14px", color: source ? C.paper : C.charcoal,
    background: source ? "linear-gradient(135deg, #39205B, #170A33 75%)" : "linear-gradient(135deg, #FBF8FF, #EEE5F8)",
    transform: `perspective(1500px) translateX(${(source ? 55 : -55) * (1 - enter)}px) rotateY(${(source ? -7 : 7) * (1 - enter)}deg)`,
    boxShadow: source ? "0 25px 55px #06020F99, inset 0 3px 0 #C9B3F255" : "0 25px 55px #06020F99, inset 0 3px 0 #FFFFFF" }}>
    <div style={{ fontSize: 54, fontWeight: 600, textAlign: "center", color: source ? C.lilacSoft : "#756987" }}>
      {source ? "Brown · 347 U.S. 483" : claim ? "Draft claim · ¶4" : "Draft filing · ¶4"}
    </div>
    {!source && claim ? <div style={{ padding: "20px 24px", fontSize: 100, lineHeight: 1.1, fontWeight: 600 }}>
      Segregation permitted
      <div style={{ marginTop: 20, fontSize: 60, color: "#AE3E3A", opacity: reveal }}>! Reversed claim</div>
    </div> : <div style={{ marginTop: 12, fontSize: 76, fontWeight: 600, lineHeight: 1.06, padding: "0 14px" }}>
      <div>{words[0]}</div><div>{words[1]}</div><div>{words[2]} {words[3]}</div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 12, whiteSpace: "nowrap" }}>
        <span style={{ fontSize: 64 }}>{words[4]}</span>
        <span style={{ fontSize: 92, color, position: "relative", transform: `translateY(${16 * (1 - reveal)}px)`,
          background: source ? `rgba(149,100,221,${.24 * reveal})` : `rgba(240,114,107,${.2 * reveal})`,
          boxShadow: `inset 0 -${6 * reveal}px 0 ${source ? C.lilac : C.review}` }}>
          {source ? <><span style={{ background: `rgba(228,218,114,${.18 * reveal})` }}>un</span>equal.</> : words[5]}
        </span>
      </div>
    </div>}
    <div style={{ position: "absolute", left: 22, right: 22, bottom: 17, height: 3,
      background: source ? C.lilac : "#D4B8DE", transform: `scaleX(${reveal})`, transformOrigin: source ? "right" : "left" }} />
  </div>;
};

const ComparePanels = ({ frame, claim = false }: { frame: number; claim?: boolean }) => {
  const start = claim ? B.claims[0] : B.quotes[0];
  const reveal = tween(frame, [start + 22, start + 39], [0, 1]);
  return <>
    <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
      <path d="M890 667H1010 M890 682H1010" stroke={C.lilacSoft} strokeWidth={3} fill="none"
        pathLength={1} strokeDasharray={1} strokeDashoffset={1 - reveal} />
    </svg>
    <QuotePanel frame={frame} source={false} claim={claim} /><QuotePanel frame={frame} source claim={claim} />
    <div style={{ position: "absolute", left: 890, top: 570, width: 120, textAlign: "center", fontSize: 105,
      color: C.yellow, opacity: reveal, transform: `scale(${.8 + .2 * reveal})`, textShadow: "0 0 24px #E4DA7244" }}>≠</div>
  </>;
};

const PrivacyPanel = ({ frame }: { frame: number }) => <Paper>
  {[["SSN", "•••-••-3456"], ["Birth date", "••/••/2000"], ["Account", "••••••••6789"]].map(([label, value], i) => {
    const reveal = tween(frame, [B.privacy[0] + 8 + i * 8, B.privacy[0] + 23 + i * 8], [0, 1]);
    return <div key={label} style={{ display: "grid", gridTemplateColumns: "410px 720px 1fr", alignItems: "center", height: 105,
      borderBottom: "2px solid #DDD1EC", opacity: reveal, transform: `translateX(${24 * (1 - reveal)}px)` }}>
      <span style={{ fontSize: 70, fontWeight: 500 }}>{label}</span>
      <span style={{ fontFamily: F.mono, fontSize: 80, color: C.purple, position: "relative" }}>{value}
        <svg width={678} height={94} style={{ position: "absolute", left: -10, top: 0, opacity: reveal }}>
          <path d="M0 24V0H28 M650 0H678V24 M0 70V94H28 M650 94H678V70" fill="none" stroke="#AE3E3A" strokeWidth={4}
            pathLength={1} strokeDasharray={1} strokeDashoffset={1 - reveal} />
        </svg>
      </span>
      <span style={{ fontSize: 58, color: "#AE3E3A" }}>! Detected</span>
    </div>;
  })}
  <div style={{ marginTop: 26, display: "flex", justifyContent: "space-between", fontSize: 76,
    opacity: tween(frame, [B.privacy[0] + 36, B.privacy[0] + 50], [0, 1]) }}>
    <span>AI-use heading</span><span style={{ color: "#AE3E3A" }}>! Missing</span>
  </div>
</Paper>;

const GraphPanel = ({ frame }: { frame: number }) => {
  const appear = tween(frame, [B.graph[0] + 6, B.graph[0] + 25], [0, 1]);
  const nodes = [
    { x: 140, y: 390, label: "Claim", status: "! Review", color: C.review },
    { x: 1330, y: 390, label: "Brown", status: "✓ Source", color: C.lilacSoft },
    { x: 140, y: 690, label: "Quote", status: "! Word change", color: C.review },
    { x: 1330, y: 690, label: "Privacy", status: "~ Detected", color: C.partial },
  ];
  return <div style={{ opacity: appear }}>
    <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
      {nodes.map((node, i) => {
        const route = tween(frame, [B.graph[0] + 18 + i * 5, B.graph[0] + 51 + i * 5], [0, 1], value => value);
        const x = 960 * (1 - route) ** 2 + 1920 * (1 - route) * route + (node.x + 225) * route ** 2;
        const y = 560 * (1 - route) ** 2 + 2 * (node.y + 80) * (1 - route) * route + (node.y + 80) * route ** 2;
        const path = `M960 560 Q960 ${node.y + 80} ${node.x + 225} ${node.y + 80}`;
        return <g key={node.label}>
          <path d={path} stroke={C.lilac} strokeWidth={17} strokeOpacity={.14} fill="none" />
          <path d={path} stroke={C.lilacSoft} strokeWidth={4} fill="none" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - appear} />
          <circle cx={x} cy={y} r={11} fill={C.yellow} opacity={windowed(frame, B.graph[0] + 18 + i * 5, B.graph[0] + 58 + i * 5, 4, 7)} />
        </g>;
      })}
      <path d="M590 470 Q960 305 1330 470" stroke={C.yellow} strokeWidth={5} fill="none" pathLength={1}
        strokeDasharray={1} strokeDashoffset={1 - tween(frame, [B.graph[0] + 30, B.graph[0] + 59], [0, 1])} />
    </svg>
    {nodes.map((node, i) => <div key={node.label} style={{ ...glass, position: "absolute", left: node.x, top: node.y,
      width: 450, height: 200, padding: "16px", lineHeight: 1.05, textAlign: "center", color: C.paper,
      transform: `perspective(1400px) translateX(${(i % 2 ? -50 : 50) * (1 - appear)}px) rotateY(${(i % 2 ? -8 : 8) * (1 - appear)}deg)` }}>
      <div style={{ fontSize: 76, fontWeight: 600 }}>{node.label}</div>
      <div style={{ fontSize: 58, color: node.color, marginTop: 4 }}>{node.status}</div>
    </div>)}
    <div style={{ ...glass, position: "absolute", left: 778, top: 495, width: 390, height: 150, background: "#C8B8E2" }} />
    <div style={{ ...glass, position: "absolute", left: 770, top: 485, width: 390, height: 150,
      display: "grid", placeItems: "center", background: "linear-gradient(135deg,#FFFFFF,#E9DFF6)", color: C.purple, fontSize: 90, fontWeight: 600 }}>Filing</div>
    <div style={{ position: "absolute", left: 650, top: 720, width: 620, textAlign: "center", color: C.paper,
      opacity: tween(frame, [B.graph[0] + 45, B.graph[0] + 63], [0, 1]) }}>
      <div style={{ fontSize: 64, color: C.lilacSoft }}>¶4 → Brown</div>
      <div style={{ fontSize: 100, color: C.yellow, fontWeight: 600, marginTop: 6 }}>“unequal.”</div>
    </div>
  </div>;
};

const ReportPanel = ({ frame }: { frame: number }) => <Paper style={{ transform: `perspective(1600px) rotateX(${tween(frame, [B.score[0], B.score[0] + 22], [6, 0])}deg)` }}>
  {[["Quote", "¶4 → Brown", "equal ≠ unequal"], ["Claim", "¶4 → Source", "Reversed meaning"], ["Privacy", "¶6 → Identifiers", "Details detected"]]
    .map(([label, location, result], i) => {
      const enter = tween(frame, [B.score[0] + 5 + i * 5, B.score[0] + 21 + i * 5], [0, 1]);
      return <div key={label} style={{ display: "grid", gridTemplateColumns: "330px 600px 1fr", alignItems: "center",
        height: 145, borderBottom: "2px solid #DDD1EC", opacity: enter, transform: `translateX(${36 * (1 - enter)}px)` }}>
        <span style={{ fontSize: 80, fontWeight: 600 }}>{label}</span>
        <span style={{ fontSize: 66, color: "#756987" }}>{location}</span>
        <span style={{ fontSize: 64, fontWeight: 500, color: C.purple }}>{result}</span>
      </div>;
    })}
</Paper>;

const BrandPanel = ({ frame }: { frame: number }) => {
  const gather = tween(frame, [B.logo[0] + 2, B.logo[0] + 26], [0, 1]);
  return <>
    <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
      {[[100, 345], [1820, 345], [100, 960], [1820, 960]].map(([x, y], i) => {
        const path = `M${x} ${y} Q960 ${y} 960 620`;
        return <g key={i}>
          <path d={path} stroke={C.lilac} strokeWidth={17} strokeOpacity={.14} fill="none" />
          <path d={path} stroke={i % 2 ? C.lilacSoft : C.yellow} strokeWidth={5} fill="none" pathLength={1}
            strokeDasharray={1} strokeDashoffset={1 - gather} />
        </g>;
      })}
    </svg>
    <Paper style={{ transform: `perspective(1600px) translateY(${26 * (1 - gather)}px) rotateX(${7 * (1 - gather)}deg) scale(${.96 + .04 * gather})` }}>
      <Img src={staticFile("filingguard-logo.png")} style={{ position: "absolute", left: 88, top: 8, width: 1500, height: 500,
        objectFit: "contain", opacity: tween(frame, [B.logo[0] + 7, B.logo[0] + 25], [0, 1]) }} />
    </Paper>
  </>;
};

export const MobileFilm = ({ frame }: { frame: number }) => {
  const beat = BEATS.find(item => frame >= item.span[0] && frame < item.span[1]);
  if (!beat || frame < 12 || frame >= 768) return null;
  const [start, end] = beat.span;
  const opacity = windowed(frame, Math.max(start, 12), Math.min(end, 768), 6, 6);
  const rise = tween(frame, [Math.max(start, 12), Math.max(start, 12) + 16], [32, 0]);
  return <div style={{ position: "absolute", inset: 0, fontFamily: F.sans, opacity }}>
    <div style={{ position: "absolute", left: 120, top: 75, fontSize: 54, fontFamily: F.mono, color: C.lilacSoft }}>
      <span style={{ display: "inline-block", width: 23, height: 23, border: `3px solid ${C.yellow}`, transform: "rotate(45deg)", marginRight: 23 }} />
      FILINGGUARD AI / PREFLIGHT
    </div>
    <div style={{ position: "absolute", left: 120, top: 175, width: 1680, fontSize: 140, lineHeight: 1.08,
      fontWeight: 700, color: C.paper, transform: `translateY(${rise}px)` }}>{beat.title}</div>
    <div style={{ position: "absolute", left: 122, top: 334, height: 4, width: tween(frame, [start + 8, start + 25], [0, 190]), background: C.yellow }} />
    <div style={{ position: "absolute", inset: 0, transform: `translateY(${rise * .4}px)` }}>
      {beat.key === "intake" && <IntakePanel frame={frame} />}
      {beat.key === "parse" && <ParsePanel frame={frame} />}
      {beat.key === "authorities" && <AuthorityRows frame={frame} />}
      {beat.key === "quotes" && <ComparePanels frame={frame} />}
      {beat.key === "claims" && <ComparePanels frame={frame} claim />}
      {beat.key === "privacy" && <PrivacyPanel frame={frame} />}
      {beat.key === "graph" && <GraphPanel frame={frame} />}
      {beat.key === "score" && <ReportPanel frame={frame} />}
      {beat.key === "logo" && <BrandPanel frame={frame} />}
    </div>
  </div>;
};
