import { Composition } from "remotion";
import { DURATION, FPS, HEIGHT, WIDTH } from "./brand";
import { PipelineFilm } from "./PipelineFilm";

export const Root = () => <><Composition
  id="PipelineFilm"
  component={PipelineFilm}
  durationInFrames={DURATION}
  fps={FPS}
  width={WIDTH}
  height={HEIGHT}
/><Composition
  id="PipelineFilmMobile"
  component={PipelineFilm}
  defaultProps={{ mobile: true }}
  durationInFrames={DURATION}
  fps={FPS}
  width={WIDTH}
  height={HEIGHT}
/></>;
