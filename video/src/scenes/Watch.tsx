import React from 'react';
import {AbsoluteFill, interpolate, useVideoConfig} from 'remotion';
import {Frame} from '../components/Frame';
import {clamp, fadeIn, rise} from '../components/anim';
import {script} from '../script';
import {theme} from '../theme';
import {useSceneFrame} from '../time';

const {heading, loop, footer, label} = script.watch;

export const Watch: React.FC = () => {
  const frame = useSceneFrame();
  const {fps} = useVideoConfig();
  const stepStart = fps * 1.6;
  const dotStart = fps * 4;
  const lap = fps * 7;
  const t = interpolate(frame, [dotStart, dotStart + lap], [0, 1], clamp);
  const active = frame >= dotStart && t < 1 ? Math.min(loop.length - 1, Math.floor(t * loop.length)) : -1;

  return (
    <Frame label={label}>
      <AbsoluteFill style={{padding: '0 120px', justifyContent: 'center'}}>
        <div style={{fontFamily: theme.display, fontSize: 112, lineHeight: 1.02, ...rise(frame, 6, 22, 20)}}>{heading}</div>
        <div style={{fontSize: 26, color: theme.muted, marginTop: 20, opacity: fadeIn(frame, 20, 16)}}>{footer}</div>

        {/* The loop as a line of steps */}
        <div style={{position: 'relative', marginTop: 110}}>
          <div style={{position: 'absolute', left: 0, right: 0, top: 10, height: 1, background: theme.soft}}>
            <div style={{width: `${interpolate(frame, [stepStart, stepStart + loop.length * 10], [0, 100], clamp)}%`, height: 1, background: theme.line}} />
            {frame >= dotStart ? (
              <div style={{position: 'absolute', left: `calc(${t * 100}% - 7px)`, top: -6, width: 13, height: 13, borderRadius: '50%', background: theme.accent}} />
            ) : null}
          </div>
          <div style={{display: 'flex', justifyContent: 'space-between'}}>
            {loop.map((n, i) => {
              const isActive = active === i;
              return (
                <div key={n.label} style={{width: 300, paddingTop: 42, ...rise(frame, stepStart + i * 10, 18, 12)}}>
                  <div style={{width: 9, height: 9, borderRadius: '50%', background: isActive ? theme.accent : theme.ink, position: 'absolute', top: 6, marginLeft: 0}} />
                  <div style={{fontFamily: theme.display, fontSize: 48, lineHeight: 1.1, color: isActive ? theme.accent : theme.ink}}>{n.label}</div>
                  <div style={{fontSize: 22, color: theme.muted, marginTop: 8}}>{n.sub}</div>
                </div>
              );
            })}
          </div>
        </div>
      </AbsoluteFill>
    </Frame>
  );
};
