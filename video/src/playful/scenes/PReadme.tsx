import React from 'react';
import {AbsoluteFill, interpolate, useVideoConfig} from 'remotion';
import {Actor, Bubble, Cutout, PFrame, Pill, Wordmark, clamp, fadeIn} from '../ui';
import {p} from '../theme';
import {art} from '../art';
import {brand} from '../../script';
import {useSceneFrame} from '../../time';

export const README_WIDTH = 1920;
export const README_HEIGHT = 660;
export const README_FRAMES = 90;

// Tenniel only: public domain worldwide, so the banner is safe on GitHub.
const cast = [
  {src: art.whiteRabbit, x: 70, y: 190, w: 380, tilt: -6, delay: 4, line: "I'm late!", blob: p.rose, side: 'right' as const},
  {src: art.alice, x: 1500, y: 210, w: 360, tilt: 4, delay: 8, line: 'Drink me?', blob: p.mint, side: 'left' as const},
];

const pills = [
  {text: '1M-token context', color: p.butter},
  {text: 'Managed Agents', color: p.sky},
  {text: 'every line spoken', color: p.rose},
  {text: 'no fail states', color: p.mint},
];

/** GitHub README banner: render one still with `npm run readme`. */
export const ReadmeBanner: React.FC = () => {
  const frame = useSceneFrame();
  const {fps} = useVideoConfig();
  const tagline = interpolate(frame, [30, 46], [0, 1], clamp);
  return (
    <PFrame>
      {cast.map((c, i) => (
        <Actor key={c.line} x={c.x} y={c.y} size={c.w} start={c.delay} blob={c.blob} seed={i}>
          <Cutout src={c.src} width={c.w} height={c.w} tilt={c.tilt} />
          <Bubble side={c.side} top={-30} size={36} opacity={fadeIn(frame, c.delay + 20)}>
            {c.line}
          </Bubble>
        </Actor>
      ))}
      <AbsoluteFill style={{alignItems: 'center', paddingTop: 90}}>
        <Wordmark start={0} size={250} />
        <div style={{textAlign: 'center', opacity: tagline, transform: `rotate(-2deg) translateY(${(1 - tagline) * 20}px)`}}>
          <div style={{fontFamily: p.hand, fontSize: 68, fontWeight: 700, marginTop: 4}}>{brand.tagline}</div>
          <div style={{fontFamily: p.display, fontSize: 36, fontWeight: 500, marginTop: 2}}>{brand.oneLiner}</div>
        </div>
        <div style={{display: 'flex', gap: 22, marginTop: 44}}>
          {pills.map((pill, i) => (
            <Pill key={pill.text} color={pill.color} style={{opacity: fadeIn(frame, 44 + i * 4), transform: `rotate(${i % 2 ? 2 : -2}deg)`}}>
              {pill.text}
            </Pill>
          ))}
        </div>
      </AbsoluteFill>
    </PFrame>
  );
};
