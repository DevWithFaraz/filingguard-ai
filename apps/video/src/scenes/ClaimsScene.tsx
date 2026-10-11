import React from "react";
import { B, C, F, tween, windowed } from "../brand";
import { Caption, StatusPill } from "../components/chrome";
import { EvidencePanel } from "../components/FilingSheet";

// Exact majority passage selected by the brown-misrepresented fixture scenario.
// Combined opinion snapshots also contain dissents; this selection is deliberate.
export const ClaimsScene: React.FC<{ frame: number }> = ({ frame }) => {
  const [start, end] = B.claims;
  if (frame < start || frame >= end) return null;
  const opacity = windowed(frame, start + 20, end, 8, 8);
  const relation = tween(frame, [start + 28, start + 40], [0, 1]);
  return (
    <>
      <Caption frame={frame} start={start} end={end} eyebrow="05 / CLAIM AND EVIDENCE" title="Proposition review"
        sub="Compare the claim with the cited majority passage. Keep the evidence in view." />
      <div style={{ position: "absolute", inset: 0, opacity, fontFamily: F.sans }}>
        <svg width={1920} height={1080} style={{ position: "absolute", inset: 0, opacity: relation }}>
          <path d="M 1330 470 V 530" fill="none" stroke={C.lilac} strokeWidth={2.5} />
          <path d="M 1330 470 V 530" fill="none" stroke={C.lilac} strokeOpacity={.15} strokeWidth={10} />
          <circle cx={1330} cy={470} r={4} fill={C.yellow} />
          <path d="M 1322 520 L 1330 530 L 1338 520" fill="none" stroke={C.lilacSoft} strokeWidth={2.5} />
        </svg>
        <div style={{ position: "absolute", left: 900, top: 484, opacity: relation }}>
          <StatusPill status="review" label="Claim reverses source" size={24} />
        </div>
        <EvidencePanel frame={frame} style={{ left: 900, top: 530, width: 820, height: 260,
          transform: `translateY(${tween(frame, [start + 20, start + 32], [12, 0])}px)` }}>
          <div style={{ padding: "24px 30px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 20,
            fontFamily: F.mono, fontSize: 24, color: C.lilacSoft }}>
            <span>BROWN / MAJORITY PASSAGE</span>
            <span>347 U.S. 483</span>
          </div>
          <div style={{ marginTop: 16, paddingLeft: 18, borderLeft: "3px solid #9564DD88", fontSize: 30, lineHeight: 1.25, fontWeight: 500, color: C.paper }}>
            We conclude that in the field of public education the doctrine of “separate but equal”{" "}
            <span style={{ color: C.yellow }}>has no place.</span>{" "}
            Separate educational facilities are{" "}
            <span style={{ color: C.lilacSoft, textDecoration: "underline", textDecorationColor: C.lilac, textUnderlineOffset: 5 }}>
              inherently unequal.
            </span>
          </div>
          </div>
        </EvidencePanel>
        <div style={{ position: "absolute", left: 930, top: 814,
          fontFamily: F.mono, fontSize: 24, color: "#B9ACD0" }}>
          CourtListener #105221 · cited passage
        </div>
      </div>
    </>
  );
};
