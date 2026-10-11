import React from "react";
import { B, C, F, tween, windowed } from "../brand";
import { Caption, StatusPill } from "../components/chrome";
import { AUTHORITY_ROW_CENTERS, EvidencePanel } from "../components/FilingSheet";

// Identity comes from retained public snapshots, not a live lookup result.
// data/demo/curated-v1/sources.json
const AUTHORITIES = [
  { cite: "347 U.S. 483", name: "Brown v. Board of Education", opinion: "105221", y: 240 },
  { cite: "384 U.S. 436", name: "Miranda v. Arizona", opinion: "107252", y: 392 },
  { cite: "576 U.S. 644", name: "Obergefell v. Hodges", opinion: "2812209", y: 544 },
] as const;

export const AuthoritiesScene: React.FC<{ frame: number }> = ({ frame }) => {
  const [start, end] = B.authorities;
  if (frame < start || frame >= end) return null;
  // The filing settles at 192. No source surface enters while it covers them.
  const opacity = windowed(frame, start + 24, end, 8, 8);
  return (
    <>
      <Caption frame={frame} start={start} end={end} eyebrow="03 / SOURCES" title="Authority lookup"
        sub="Follow each citation to its source opinion. Keep unresolved references visible." />
      <div style={{ position: "absolute", inset: 0, opacity, fontFamily: F.sans }}>
        <div style={{ position: "absolute", left: 1230, top: 186, fontFamily: F.mono, fontSize: 24, color: C.lilacSoft }}>
          COURTLISTENER / SOURCE OPINIONS
        </div>
        <svg width={1920} height={1080} style={{ position: "absolute", inset: 0, overflow: "visible" }}>
          {AUTHORITIES.map((authority, index) => {
            const progress = tween(frame, [start + 27 + index * 3, start + 42 + index * 3], [0, 1]);
            const sourceY = AUTHORITY_ROW_CENTERS[index];
            const targetY = authority.y + 71;
            return (
              <g key={authority.cite} opacity={progress}>
                <path d={`M 1168 ${sourceY} C 1203 ${sourceY}, 1194 ${targetY}, 1230 ${targetY}`}
                  fill="none" stroke={C.lilac} strokeOpacity={.17} strokeWidth={9} />
                <path d={`M 1168 ${sourceY} C 1203 ${sourceY}, 1194 ${targetY}, 1230 ${targetY}`}
                  fill="none" stroke={C.lilac} strokeWidth={2.5} pathLength={1}
                  strokeDasharray={1} strokeDashoffset={1 - progress} />
                <circle cx={1168} cy={sourceY} r={5} fill={C.yellow} />
                <circle cx={1168} cy={sourceY} r={10} fill="none" stroke={C.yellow} strokeOpacity={.35} />
                <circle cx={1230} cy={targetY} r={4} fill={C.lilacSoft} />
              </g>
            );
          })}
          <g opacity={tween(frame, [start + 39, start + 52], [0, 1])}>
            <path d={`M 1168 ${AUTHORITY_ROW_CENTERS[3]} C 1200 ${AUTHORITY_ROW_CENTERS[3]}, 1200 763, 1230 763`} fill="none"
              stroke={C.unknown} strokeWidth={2.5} strokeDasharray="6 7" />
            <circle cx={1168} cy={AUTHORITY_ROW_CENTERS[3]} r={5} fill={C.unknown} />
          </g>
        </svg>
        {AUTHORITIES.map((authority, index) => {
          const reveal = tween(frame, [start + 27 + index * 3, start + 39 + index * 3], [0, 1]);
          return (
            <EvidencePanel key={authority.cite} frame={frame} style={{ left: 1230, top: authority.y,
              width: 516, height: 142, opacity: reveal, transform: `translateX(${(1 - reveal) * 12}px)` }}>
              <div style={{ padding: "12px 24px", lineHeight: 1.1 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16 }}>
                <span style={{ fontFamily: F.mono, fontSize: 26, color: C.lilacSoft }}>{authority.cite}</span>
                <StatusPill status="resolved" label="Cached opinion" size={24} />
              </div>
              <div style={{ marginTop: 8, fontSize: 26, fontWeight: 650, color: C.paper }}>{authority.name}</div>
              <div style={{ marginTop: 6, fontFamily: F.mono, fontSize: 24, color: "#B9ACD0" }}>
                CourtListener #{authority.opinion}
              </div>
              </div>
            </EvidencePanel>
          );
        })}
        <EvidencePanel frame={frame} style={{ left: 1230, top: 708, width: 516, height: 110,
          opacity: tween(frame, [start + 39, start + 52], [0, 1]) }}>
          <div style={{ height: "100%", boxSizing: "border-box", padding: "12px 24px", borderRadius: 18,
            border: "1px dashed #9A94AE88", background: "#0E062080" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontFamily: F.mono, fontSize: 26, color: C.paper }}>999 U.S. 999</span>
            <StatusPill status="unknown" label="Unresolved" size={24} />
          </div>
          <div style={{ marginTop: 10, fontSize: 24, color: "#B9ACD0" }}>Reference retained for review</div>
          </div>
        </EvidencePanel>
      </div>
    </>
  );
};
