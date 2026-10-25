import React, {CSSProperties, PropsWithChildren} from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile, useVideoConfig} from 'remotion';
import {p, pastels} from './theme';
import {useSubtitleLine} from '../components/Subtitles';
import {useSceneFrame} from '../time';

export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

/** A bouncy entrance. 0 before `start`, overshoots a little, settles at 1. */
export const bounce = (frame: number, fps: number, start: number, damping = 9) =>
  spring({frame: frame - start, fps, config: {damping, stiffness: 120, mass: 0.9}});

export const fadeIn = (frame: number, start: number, dur = 12) => interpolate(frame, [start, start + dur], [0, 1], clamp);

/** Scale + slight drop-in, for use as a style spread. */
export const popIn = (frame: number, fps: number, start: number, damping = 9) => {
  const s = bounce(frame, fps, start, damping);
  return {opacity: Math.min(1, s * 2), transform: `scale(${s})`};
};

const noise = (i: number, k: number) => ((Math.sin(i * k) * 10000) % 1 + 1) % 1;

export const Confetti: React.FC<{count?: number}> = ({count = 24}) => {
  const frame = useSceneFrame();
  const {fps} = useVideoConfig();
  return (
    <>
      {Array.from({length: count}).map((_, i) => {
        const s = spring({frame: frame - i * 2, fps, config: {damping: 10}});
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: noise(i, 7.31) * 1920,
              top: noise(i, 3.17) * 1080 + Math.sin(frame / 20 + i) * 8,
              width: 12 + (i % 3) * 8,
              height: 12 + (i % 3) * 8,
              borderRadius: i % 2 ? '50%' : 4,
              background: pastels[i % pastels.length],
              transform: `scale(${s}) rotate(${frame * 2 + i * 30}deg)`,
              opacity: 0.7,
            }}
          />
        );
      })}
    </>
  );
};

/** Paper background, confetti, and a tilted chapter sticker. */
export const PFrame: React.FC<PropsWithChildren<{label?: string; confetti?: boolean}>> = ({children, label, confetti = true}) => {
  const frame = useSceneFrame();
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill style={{background: p.paper, fontFamily: p.body, color: p.ink, overflow: 'hidden'}}>
      {confetti ? <Confetti /> : null}
      {children}
      {label ? (
        <div
          style={{
            position: 'absolute',
            top: 56,
            left: 72,
            padding: '6px 22px',
            borderRadius: 999,
            background: p.white,
            border: `4px solid ${p.ink}`,
            boxShadow: `5px 5px 0 ${p.ink}`,
            fontFamily: p.hand,
            fontSize: 34,
            fontWeight: 700,
            transform: `rotate(-3deg) scale(${bounce(frame, fps, 2)})`,
            transformOrigin: 'left center',
          }}
        >
          {label}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

/** A white card with a thick outline and a hard shadow. */
export const Sticker: React.FC<PropsWithChildren<{tilt?: number; color?: string; style?: CSSProperties; shadow?: number}>> = ({
  children,
  tilt = 0,
  color = p.white,
  style,
  shadow = 8,
}) => (
  <div
    style={{
      background: color,
      border: `5px solid ${p.ink}`,
      borderRadius: 30,
      boxShadow: `${shadow}px ${shadow}px 0 ${p.ink}`,
      padding: '26px 34px',
      transform: `rotate(${tilt}deg)`,
      ...style,
    }}
  >
    {children}
  </div>
);

/** A small rounded label. */
export const Pill: React.FC<PropsWithChildren<{color?: string; style?: CSSProperties}>> = ({children, color = p.white, style}) => (
  <div
    style={{
      display: 'inline-block',
      background: color,
      border: `4px solid ${p.ink}`,
      borderRadius: 999,
      boxShadow: `4px 4px 0 ${p.ink}`,
      padding: '8px 22px',
      fontFamily: p.display,
      fontWeight: 500,
      fontSize: 26,
      whiteSpace: 'nowrap',
      ...style,
    }}
  >
    {children}
  </div>
);

/** A round badge with a number or a check mark. */
export const Badge: React.FC<{color: string; children: React.ReactNode; size?: number}> = ({color, children, size = 64}) => (
  <div
    style={{
      width: size,
      height: size,
      borderRadius: '50%',
      background: color,
      border: `4px solid ${p.ink}`,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: p.display,
      fontWeight: 700,
      fontSize: size * 0.5,
      flexShrink: 0,
    }}
  >
    {children}
  </div>
);

/** A handwritten speech bubble with a tail. */
export const Bubble: React.FC<PropsWithChildren<{side?: 'left' | 'right'; opacity?: number; top?: number; size?: number; style?: CSSProperties}>> = ({
  children,
  side = 'right',
  opacity = 1,
  top = -70,
  size = 40,
  style,
}) => (
  <div
    style={{
      position: 'absolute',
      top,
      [side === 'right' ? 'left' : 'right']: '70%',
      padding: '10px 22px',
      borderRadius: 28,
      background: p.white,
      border: `4px solid ${p.ink}`,
      fontFamily: p.hand,
      fontSize: size,
      fontWeight: 700,
      color: p.ink,
      whiteSpace: 'nowrap',
      opacity,
      transform: `rotate(${side === 'right' ? -4 : 4}deg)`,
      ...style,
    }}
  >
    {children}
    <div
      style={{
        position: 'absolute',
        bottom: -18,
        [side === 'right' ? 'left' : 'right']: 24,
        width: 22,
        height: 22,
        background: p.white,
        borderRight: `4px solid ${p.ink}`,
        borderBottom: `4px solid ${p.ink}`,
        transform: 'rotate(45deg)',
      }}
    />
  </div>
);

/** A character on a pastel blob, bouncing in, bobbing gently. */
export const Actor: React.FC<PropsWithChildren<{x: number; y: number; size: number; tilt?: number; start: number; blob?: string; seed?: number}>> = ({
  children,
  x,
  y,
  size,
  tilt = 0,
  start,
  blob,
  seed = 0,
}) => {
  const frame = useSceneFrame();
  const {fps} = useVideoConfig();
  const s = bounce(frame, fps, start);
  const bob = Math.sin(frame / 14 + seed * 1.3) * 10;
  return (
    <div style={{position: 'absolute', left: x, top: y + bob, width: size, height: size, transform: `scale(${s}) rotate(${tilt}deg)`, transformOrigin: '50% 100%'}}>
      {blob ? <div style={{position: 'absolute', inset: '12%', borderRadius: '50%', background: blob}} /> : null}
      <div style={{position: 'absolute', inset: 0}}>{children}</div>
    </div>
  );
};

/** Narration as a subtitle pill. Same timing as the lean version. */
export const PSubtitles: React.FC<{lines: readonly string[]; durationInFrames: number}> = ({lines, durationInFrames}) => {
  const current = useSubtitleLine(lines, durationInFrames);
  if (!current) return null;
  return (
    <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', pointerEvents: 'none'}}>
      <div
        style={{
          marginBottom: 48,
          maxWidth: 1560,
          padding: '12px 36px',
          borderRadius: 999,
          background: p.white,
          border: `4px solid ${p.ink}`,
          boxShadow: `6px 6px 0 ${p.ink}`,
          fontFamily: p.body,
          fontSize: 34,
          lineHeight: 1.35,
          letterSpacing: '0.01em',
          wordSpacing: '0.08em',
          color: p.ink,
          textAlign: 'center',
        }}
      >
        {current}
      </div>
    </AbsoluteFill>
  );
};

/** ExpLit wordmark with letters that drop in and wiggle. */
export const Wordmark: React.FC<{start: number; size?: number}> = ({start, size = 300}) => {
  const frame = useSceneFrame();
  const {fps} = useVideoConfig();
  return (
    <div style={{display: 'flex', fontFamily: p.display, fontWeight: 700, fontSize: size, color: p.ink, lineHeight: 1}}>
      {'ExpLit'.split('').map((ch, i) => {
        const s = spring({frame: frame - start - i * 4, fps, config: {damping: 8, stiffness: 140}});
        const wiggle = Math.sin(frame / 10 + i) * 3;
        return (
          <span
            key={i}
            style={{
              display: 'inline-block',
              transform: `translateY(${(1 - s) * 200}px) rotate(${wiggle + (i % 2 ? 3 : -3)}deg) scale(${s})`,
              color: i < 3 ? p.clay : p.ink,
              textShadow: `${size * 0.027}px ${size * 0.027}px 0 ${i < 3 ? p.butter : p.sky}`,
            }}
          >
            {ch}
          </span>
        );
      })}
    </div>
  );
};

/** A hand-drawn arrow between two points, drawing itself. Coordinates in the 1920x1080 frame. */
export const Squiggle: React.FC<{from: [number, number]; to: [number, number]; progress: number; color?: string; bend?: number}> = ({
  from,
  to,
  progress,
  color = p.ink,
  bend = 60,
}) => {
  const [x0, y0] = from;
  const [x1, y1] = to;
  const mx = (x0 + x1) / 2;
  const my = (y0 + y1) / 2 - bend;
  const pr = Math.max(0, Math.min(1, progress));
  const ang = Math.atan2(y1 - my, x1 - mx);
  const head = 18;
  return (
    <svg style={{position: 'absolute', inset: 0, pointerEvents: 'none'}} viewBox="0 0 1920 1080" width="100%" height="100%">
      <path d={`M ${x0} ${y0} Q ${mx} ${my} ${x1} ${y1}`} fill="none" stroke={color} strokeWidth={7} strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - pr} />
      {pr > 0.98 ? (
        <polygon
          points={`${x1},${y1} ${x1 - head * Math.cos(ang - 0.5)},${y1 - head * Math.sin(ang - 0.5)} ${x1 - head * Math.cos(ang + 0.5)},${y1 - head * Math.sin(ang + 0.5)}`}
          fill={color}
        />
      ) : null}
    </svg>
  );
};

/**
 * A public-domain illustration as a cut-out. Multiply blending drops the
 * scan's white paper so the drawing sits straight on our cream page.
 */
export const Cutout: React.FC<{src: string; width: number; height?: number; tilt?: number; style?: CSSProperties}> = ({src, width, height, tilt = 0, style}) => (
  <Img
    src={staticFile(src)}
    style={{
      width,
      height: height ?? 'auto',
      maxHeight: height ? undefined : width * 1.6,
      objectFit: 'contain',
      transform: `rotate(${tilt}deg)`,
      ...style,
    }}
  />
);

/** A cut-out framed like a photo in a scrapbook: white card, tilt, hard shadow. */
export const Polaroid: React.FC<{src: string; width: number; height: number; tilt?: number; caption?: string; style?: CSSProperties}> = ({src, width, height, tilt = 0, caption, style}) => (
  <div
    style={{
      width,
      background: p.white,
      border: `5px solid ${p.ink}`,
      borderRadius: 18,
      boxShadow: `8px 8px 0 ${p.ink}`,
      padding: 12,
      transform: `rotate(${tilt}deg)`,
      ...style,
    }}
  >
    <div style={{width: '100%', height, overflow: 'hidden', borderRadius: 8, background: p.white, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
      <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
    </div>
    {caption ? <div style={{fontFamily: p.hand, fontSize: 30, fontWeight: 700, textAlign: 'center', marginTop: 8}}>{caption}</div> : null}
  </div>
);
