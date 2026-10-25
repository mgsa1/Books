import React from 'react';
import {AbsoluteFill, interpolate, useVideoConfig} from 'remotion';
import {Frame} from '../components/Frame';
import {clamp, fadeIn, rise} from '../components/anim';
import {script} from '../script';
import {theme} from '../theme';
import {useSceneFrame} from '../time';

const {on, wall, quote, quoteBy, label} = script.friend;

// Enough text to overflow the frame many times over, so it reads as endless.
const words = Array.from({length: 14}, () => wall).join('').split(' ');
const noise = (i: number) => ((Math.sin(i * 12.9898) * 43758.5453) % 1 + 1) % 1;

export const Friend: React.FC = () => {
  const frame = useSceneFrame();
  const {fps} = useVideoConfig();

  const lineStarts = [fps * 0.6, fps * 2.6, fps * 4.4];
  const fadeStart = fps * 6.6;
  const quoteStart = fps * 7.3;

  // The wall: slow, constant scroll; the strain builds, then it all dissolves.
  const scroll = frame * 1.1;
  const wallIn = fadeIn(frame, 0, 20);
  const strain = interpolate(frame, [fps * 1, fps * 6.5], [0, 1], clamp);
  const wallOut = interpolate(frame, [fadeStart, fadeStart + fps * 1.4], [1, 0], clamp);
  const blur = interpolate(frame, [fadeStart, fadeStart + fps * 1.4], [0, 8], clamp);
  const headOut = interpolate(frame, [fadeStart, fadeStart + fps * 0.6], [1, 0], clamp);

  return (
    <Frame label={label}>
      {/* Wall of text */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            top: 0,
            padding: '0 28px',
            transform: `translateY(${-scroll}px)`,
            fontFamily: theme.display,
            fontSize: 22,
            lineHeight: 1.4,
            color: theme.ink,
            opacity: wallIn * wallOut * 0.62,
            filter: `blur(${blur}px)`,
            textAlign: 'justify',
          }}
        >
          {words.map((w, i) => {
            const n = noise(i);
            const wobble = Math.sin(frame / (6 + n * 6) + i) * 2.5 * strain;
            const slip = n > 0.85 ? Math.sin(frame / 9 + i) * 5 * strain : 0;
            return (
              <span key={i} style={{display: 'inline-block', marginRight: '0.28em', transform: `translate(${slip}px, ${wobble}px)`, opacity: 1 - strain * 0.45 * n}}>
                {w}
              </span>
            );
          })}
        </div>
      </AbsoluteFill>

      {/* Headline cutting through the wall on a band of paper */}
      <AbsoluteFill style={{justifyContent: 'center', padding: '0 120px', opacity: headOut}}>
        <div
          style={{
            width: 'fit-content',
            padding: '12px 36px 12px 24px',
            margin: '0 0 0 -24px',
            background: theme.bg,
            boxShadow: `0 0 48px 36px ${theme.bg}`,
            opacity: fadeIn(frame, lineStarts[0], 22),
          }}
        >
        <div style={{maxWidth: 1500}}>
          {on.map((line, i) => (
            <div
              key={line}
              style={{
                fontFamily: theme.display,
                fontSize: i === 0 ? 120 : 88,
                lineHeight: 1.05,
                color: i === 2 ? theme.accent : theme.ink,
                marginTop: i === 0 ? 0 : 6,
                ...rise(frame, lineStarts[i], 22, 20),
              }}
            >
              {line}
            </div>
          ))}
        </div>
        </div>
      </AbsoluteFill>

      {/* The quote */}
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', padding: '0 200px'}}>
        <div style={{textAlign: 'center', ...rise(frame, quoteStart, 26, 20)}}>
          <div style={{fontFamily: theme.display, fontSize: 92, lineHeight: 1.15, color: theme.ink}}>{quote}</div>
          <div style={{fontSize: 24, letterSpacing: '0.18em', textTransform: 'uppercase', color: theme.muted, marginTop: 32}}>{quoteBy}</div>
        </div>
      </AbsoluteFill>
    </Frame>
  );
};
