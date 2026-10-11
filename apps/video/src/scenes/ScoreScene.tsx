import { B } from "../brand";
import { Caption } from "../components/chrome";
export const ScoreScene = ({ frame }: { frame: number }) => {
  const [start,end] = B.score;
  return <Caption frame={frame} start={start} end={end} eyebrow="08 / EVIDENCE REPORT"
    title="Evidence report" sub="Findings, source passages and document locations. Together in one view." />;
};
