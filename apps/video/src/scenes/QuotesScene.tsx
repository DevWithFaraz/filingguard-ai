import React from "react";
import { B, C, F, tween, windowed } from "../brand";
import { Caption, StatusPill } from "../components/chrome";
import { EvidencePanel, QuoteWords, QUOTE_SOURCE } from "../components/FilingSheet";

export const QuotesScene: React.FC<{ frame: number }> = ({ frame }) => {
  const [start, end] = B.quotes;
  if (frame < start || frame >= end) return null;
  const opacity = windowed(frame, start + 20, end, 8, 8);
  const align = tween(frame, [start + 32, start + 46], [0, 1]);
  return (
    <>
      <Caption frame={frame} start={start} end={end} eyebrow="04 / TEXT COMPARISON" title="Quote forensics"
        sub="Align the quotation with the source. Isolate the changed word." />
      <div style={{ position: "absolute", inset: 0, opacity, fontFamily: F.sans }}>
        <EvidencePanel frame={frame} style={{ left: 1312, top: 300, width: 440, height: 430,
          transform: `translateX(${tween(frame, [start + 20, start + 32], [12, 0])}px)` }}>
          <div style={{ padding: "30px" }}>
          <div style={{ fontFamily: F.mono, fontSize: 24, color: C.lilacSoft }}>SOURCE OPINION</div>
          <div style={{ marginTop: 10, fontSize: 24, color: "#CFC6E4" }}>Brown · 347 U.S. 483</div>
          <div style={{ color: C.paper }}>
            <QuoteWords frame={frame} words={QUOTE_SOURCE} diffIndex={5} dark />
          </div>
          <div style={{ position: "absolute", left: 30, right: 30, bottom: 30, paddingTop: 14,
            borderTop: `1px solid ${C.line}`, fontFamily: F.mono, fontSize: 24, color: "#B9ACD0" }}>
            CourtListener #105221
          </div>
          </div>
        </EvidencePanel>
        <svg width={1920} height={1080} style={{ position: "absolute", inset: 0, opacity: align }}>
          <path d="M 1060 730 V 782 H 1280" fill="none" stroke={C.review} strokeWidth={2} />
          <path d="M 1532 730 V 782 H 1320" fill="none" stroke={C.lilac} strokeWidth={2} />
          <circle cx={1060} cy={730} r={4} fill={C.review} />
          <circle cx={1532} cy={730} r={4} fill={C.lilacSoft} />
        </svg>
        <EvidencePanel frame={frame} style={{ left: 974, top: 758, width: 668, height: 100,
          opacity: align, transform: `translateY(${(1 - align) * 10}px)` }}>
          <div style={{ height: "100%", padding: "18px 24px", boxSizing: "border-box", display: "flex",
            alignItems: "center", justifyContent: "space-between", gap: 20 }}>
          <StatusPill status="partial" label="Word changed" size={24} />
          <div style={{ fontSize: 40, fontWeight: 650, whiteSpace: "nowrap" }}>
            <span style={{ color: "#FFB3AE" }}>equal.</span>
            <span style={{ color: C.paper, margin: "0 20px" }}>≠</span>
            <span style={{ color: C.lilacSoft }}>unequal.</span>
          </div>
          </div>
        </EvidencePanel>
      </div>
    </>
  );
};
