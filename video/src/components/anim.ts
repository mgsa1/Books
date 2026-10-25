import {Easing, interpolate} from 'remotion';

export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const ease = Easing.out(Easing.cubic);

/** 0 → 1 over `dur` frames from `start`, eased out. */
export const fadeIn = (frame: number, start: number, dur = 18) =>
  interpolate(frame, [start, start + dur], [0, 1], {...clamp, easing: ease});

/** Opacity + a small upward settle. Spread onto a style object. */
export const rise = (frame: number, start: number, dur = 18, distance = 16) => {
  const p = fadeIn(frame, start, dur);
  return {opacity: p, transform: `translateY(${(1 - p) * distance}px)`};
};
