import React from 'react';
import {AbsoluteFill, interpolate, useVideoConfig} from 'remotion';
import {Actor, Cutout, PFrame, Wordmark, clamp} from '../ui';
import {p} from '../theme';
import {art} from '../art';
import {brand} from '../../script';
import {useSceneFrame} from '../../time';

type Cast = {src: string; x: number; y: number; w: number; tilt: number; delay: number; line: string; blob: string; side: 'left' | 'right'; top?: number};

const cast: Cast[] = [
  {src: art.whiteRabbit, x: 110, y: 400, w: 320, tilt: -6, delay: 0.5, line: "I'm late!", blob: p.rose, side: 'right', top: -40},
  {src: art.pooh, x: 1440, y: 600, w: 380, tilt: 5, delay: 0.8, line: 'Honey?', blob: p.butter, side: 'left', top: -50},
  {src: art.tinWoodman, x: 420, y: 60, w: 300, tilt: -5, delay: 1.4, line: 'Oil can.', blob: p.mint, side: 'right', top: -40},
  {src: art.peterRabbit, x: 1150, y: 750, w: 200, tilt: 3, delay: 1.7, line: 'Radishes!', blob: p.sky, side: 'right', top: 10},
];

export const PTitle: React.FC = () => {
  const frame = useSceneFrame();
  const {fps} = useVideoConfig();
  const titleStart = fps * 1.6;
  const tagline = interpolate(frame, [titleStart + 24, titleStart + 40], [0, 1], clamp);

  return (
    <PFrame>
      {cast.map((c, i) => (
          <Actor key={c.line} x={c.x} y={c.y} size={c.w} start={c.delay * fps} blob={c.blob} seed={i}>
            <Cutout src={c.src} width={c.w} height={c.w} tilt={c.tilt} />
          </Actor>
      ))}

      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
        <Wordmark start={titleStart} />
        <div style={{textAlign: 'center', opacity: tagline, transform: `rotate(-2deg) translateY(${(1 - tagline) * 20}px)`}}>
          <div style={{fontFamily: p.hand, fontSize: 72, fontWeight: 700, color: p.ink, marginTop: 6}}>{brand.tagline}</div>
          <div style={{fontFamily: p.display, fontSize: 36, fontWeight: 500, color: p.ink, marginTop: 2}}>{brand.oneLiner}</div>
        </div>
      </AbsoluteFill>

    </PFrame>
  );
};
