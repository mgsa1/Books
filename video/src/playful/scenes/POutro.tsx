import React from 'react';
import {AbsoluteFill, interpolate, useVideoConfig} from 'remotion';
import {Actor, Cutout, PFrame, Wordmark, clamp, fadeIn} from '../ui';
import {p, pastels} from '../theme';
import {art} from '../art';
import {brand} from '../../script';
import {useSceneFrame} from '../../time';

const row = [art.tinWoodman, art.whiteRabbit, art.alice, art.pooh, art.peterRabbit];

export const POutro: React.FC = () => {
  const frame = useSceneFrame();
  const {fps} = useVideoConfig();
  const tagline = interpolate(frame, [30, 46], [0, 1], clamp);
  return (
    <PFrame>
      <AbsoluteFill style={{alignItems: 'center', paddingTop: 150}}>
        <Wordmark start={4} size={240} />
        <div style={{fontFamily: p.hand, fontSize: 76, fontWeight: 700, marginTop: 6, opacity: tagline, transform: `rotate(-2deg) translateY(${(1 - tagline) * 20}px)`}}>{brand.closing}</div>
        <div style={{fontSize: 24, color: p.muted, marginTop: 36, textAlign: 'center', lineHeight: 1.6, maxWidth: 1200, opacity: fadeIn(frame, 60, 16)}}>
          {brand.builtWith}
          <br />
          {brand.link}
        </div>
      </AbsoluteFill>
      {row.map((src, i) => (
        <Actor key={src} x={235 + i * 290} y={760} size={240} start={fps * 1.2 + i * 6} blob={pastels[i]} seed={i}>
          <Cutout src={src} width={240} height={240} tilt={(i % 2 ? 1 : -1) * 4} />
        </Actor>
      ))}
    </PFrame>
  );
};
