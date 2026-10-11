import { Easing, interpolate } from "remotion";

// Values are owned by brief/BRAND.md (derived from docs/product/UI direction).
export const C = {
  ink: "#0E0620",
  night: "#170A33",
  purple: "#3E0F8D",
  logoPurple: "#2D0A6A",
  lilac: "#9564DD",
  lilacSoft: "#C9B3F2",
  yellow: "#E4DA72",
  paper: "#F4F0FB",
  gray: "#EEEEEE",
  charcoal: "#24292B",
  muted: "#8F86A8",
  line: "rgba(201, 179, 242, 0.16)",
  resolved: "#3DBE8B",
  review: "#F0726B",
  partial: "#F2A65A",
  unknown: "#9A94AE",
} as const;

export const F = {
  sans: "Film Inter, sans-serif",
  mono: "Film Mono, monospace",
};

export const FPS = 30;
export const WIDTH = 1920;
export const HEIGHT = 1080;

/** Beat boundaries in frames. brief/BEATS.md mirrors this table. */
export const B = {
  intake: [0, 84],
  parse: [84, 168],
  authorities: [168, 270],
  quotes: [270, 366],
  claims: [366, 444],
  privacy: [444, 540],
  graph: [540, 642],
  score: [642, 714],
  logo: [714, 780],
} as const;

export const DURATION = 780;

export const easeIn = Easing.bezier(0.16, 1, 0.3, 1);
export const easeOut = Easing.bezier(0.7, 0, 0.84, 0);
export const easeInOut = Easing.bezier(0.65, 0, 0.35, 1);

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** Eased clamped interpolation (default: expressive ease-in). */
export const tween = (
  frame: number,
  input: [number, number],
  output: [number, number],
  easing: (t: number) => number = easeIn,
) => interpolate(frame, input, output, { ...clamp, easing });

/** Opacity window: fades in at `start`, out before `end`. */
export const windowed = (frame: number, start: number, end: number, fadeIn = 10, fadeOut = 8) =>
  Math.min(
    tween(frame, [start, start + fadeIn], [0, 1]),
    tween(frame, [end - fadeOut, end], [1, 0], easeOut),
  );

/** Multi-keyframe interpolation with per-segment easing. */
export const keys = (frame: number, input: number[], output: number[], easing = easeInOut) =>
  interpolate(frame, input, output, { ...clamp, easing });
