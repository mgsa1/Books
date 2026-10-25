import React from 'react';
import {AbsoluteFill, interpolate, useVideoConfig} from 'remotion';
import {Actor, PFrame, Sticker, clamp, fadeIn, popIn, Cutout} from '../ui';
import {p} from '../theme';
import {art} from '../art';
import {script} from '../../script';
import {useSceneFrame} from '../../time';

const {on, wall, quote, quoteBy, label} = script.friend;
const words = Array.from({length: 14}, () => wall).join('').split(' ');
const noise = (i: number) => ((Math.sin(i * 12.9898) * 43758.5453) % 1 + 1) % 1;

export const PFriend: React.FC = () => {
  const frame = useSceneFrame();
  const {fps} = useVideoConfig();
  const lineStarts = [fps * 0.6, fps * 2.6, fps * 4.4];
  const fadeStart = fps * 6.6;
  const quoteStart = fps * 7.3;

  const scroll = frame * 1.1;
  const wallIn = fadeIn(frame, 0, 20);
  const strain = interpolate(frame, [fps * 1, fps * 6.5], [0, 1], clamp);
  const wallOut = interpolate(frame, [fadeStart, fadeStart + fps * 1.2], [1, 0], clamp);
  const headOut = interpolate(frame, [fadeStart, fadeStart + fps * 0.6], [1, 0], clamp);

  return (
    <PFrame label={label} confetti={false}>
      {/* Wall of text, with a few words mirrored the way letters can flip */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <div style={{position: 'absolute', left: 0, right: 0, top: 0, padding: '0 28px', transform: `translateY(${-scroll}px)`, fontFamily: p.body, fontSize: 22, lineHeight: 1.45, color: p.ink, opacity: wallIn * wallOut * 0.6, textAlign: 'justify'}}>
          {words.map((w, i) => {
            const n = noise(i);
            const wobble = Math.sin(frame / (6 + n * 6) + i) * 2.5 * strain;
            const flip = n > 0.94 && strain > 0.5 ? ' scaleX(-1)' : '';
            return (
              <span key={i} style={{display: 'inline-block', marginRight: '0.28em', transform: `translateY(${wobble}px)${flip}`, opacity: 1 - strain * 0.4 * n}}>
                {w}
              </span>
            );
          })}
        </div>
      </AbsoluteFill>

      {/* Headline sticker */}
      <AbsoluteFill style={{justifyContent: 'center', padding: '0 120px', opacity: headOut}}>
        <div style={{...popIn(frame, fps, lineStarts[0] - 6), transformOrigin: 'left center', width: 'fit-content'}}>
          <Sticker tilt={-2} style={{padding: '30px 48px 34px'}}>
            {on.map((line, i) => (
              <div key={line} style={{fontFamily: p.display, fontWeight: 700, fontSize: i === 0 ? 112 : 84, lineHeight: 1.05, color: i === 2 ? p.clay : p.ink, ...popIn(frame, fps, lineStarts[i], 11), transformOrigin: 'left center'}}>
                {line}
              </div>
            ))}
          </Sticker>
        </div>
      </AbsoluteFill>

      {/* Alice says it */}
      <Actor x={160} y={300} size={520} start={quoteStart} seed={1}>
        <Cutout src={art.alice} width={520} tilt={-3} />
      </Actor>
      <div style={{position: 'absolute', left: 720, top: 330, width: 1000, ...popIn(frame, fps, quoteStart + 8), transformOrigin: 'left bottom'}}>
        <Sticker tilt={1.5} style={{padding: '36px 44px'}}>
          <div style={{fontFamily: p.hand, fontWeight: 700, fontSize: 84, lineHeight: 1.12}}>{quote}</div>
          <div style={{fontFamily: p.display, fontWeight: 500, fontSize: 28, color: p.muted, marginTop: 18}}>— {quoteBy}</div>
        </Sticker>
      </div>
    </PFrame>
  );
};
