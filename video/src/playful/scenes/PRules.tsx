import React from 'react';
import {AbsoluteFill, interpolate, useVideoConfig} from 'remotion';
import {Actor, Badge, Bubble, Cutout, PFrame, Sticker, clamp, popIn} from '../ui';
import {p, pastels} from '../theme';
import {art} from '../art';
import {script} from '../../script';
import {useSceneFrame} from '../../time';

const {heading, checklist, label} = script.rules;

export const PRules: React.FC = () => {
  const frame = useSceneFrame();
  const {fps} = useVideoConfig();
  const listStart = fps * 1.6;
  const gap = fps * 0.8;
  const bubble = interpolate(frame, [fps * 7, fps * 7.3], [0, 1], clamp);

  return (
    <PFrame label={label}>
      <AbsoluteFill style={{padding: '0 120px', justifyContent: 'center'}}>
        <div style={{display: 'flex', gap: 100, alignItems: 'flex-start'}}>
          <div style={{width: 640}}>
            <div style={{...popIn(frame, fps, 6), transformOrigin: 'left center', width: 'fit-content'}}>
              <Sticker tilt={-2} color={p.butter} style={{padding: '24px 40px 30px'}}>
                <div style={{fontFamily: p.display, fontWeight: 700, fontSize: 92, lineHeight: 1.02}}>{heading}</div>
              </Sticker>
            </div>
          </div>
          <div style={{flex: 1, display: 'flex', flexDirection: 'column', gap: 22, paddingTop: 10}}>
            {checklist.map((item, i) => (
              <div key={item} style={{...popIn(frame, fps, listStart + i * gap), transformOrigin: 'left center', width: 'fit-content'}}>
                <Sticker tilt={i % 2 ? 1 : -1} shadow={6} style={{display: 'flex', alignItems: 'center', gap: 22, padding: '14px 30px 14px 16px', borderRadius: 999}}>
                  <Badge color={pastels[(i + 2) % pastels.length]} size={58}>✓</Badge>
                  <span style={{fontFamily: p.display, fontWeight: 500, fontSize: 40}}>{item}</span>
                </Sticker>
              </div>
            ))}
          </div>
        </div>
      </AbsoluteFill>

      <Actor x={150} y={560} size={420} start={fps * 5.5} blob={p.mint} seed={3}>
        <Cutout src={art.pooh} width={420} height={420} tilt={-4} />
        <Bubble side="right" opacity={bubble} top={-10}>
          No timers. Time for honey.
        </Bubble>
      </Actor>
    </PFrame>
  );
};
