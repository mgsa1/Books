import React from 'react';
import {AbsoluteFill, useVideoConfig} from 'remotion';
import {Frame} from '../components/Frame';
import {fadeIn, rise} from '../components/anim';
import {Rule} from '../components/Rule';
import {script} from '../script';
import {theme} from '../theme';
import {useSceneFrame} from '../time';

const {heading, checklist, label} = script.rules;

export const Rules: React.FC = () => {
  const frame = useSceneFrame();
  const {fps} = useVideoConfig();
  const listStart = fps * 1.6;
  const gap = fps * 0.8;

  return (
    <Frame label={label}>
      <AbsoluteFill style={{padding: '0 120px', justifyContent: 'center'}}>
        <div style={{display: 'flex', gap: 120, alignItems: 'flex-start'}}>
          <div style={{width: 640, fontFamily: theme.display, fontSize: 112, lineHeight: 1.02, ...rise(frame, 6, 22, 20)}}>{heading}</div>
          <div style={{flex: 1, paddingTop: 16}}>
            {checklist.map((item, i) => {
              const start = listStart + i * gap;
              return (
                <div key={item}>
                  <div style={{display: 'flex', alignItems: 'baseline', gap: 28, padding: '22px 0', ...rise(frame, start, 18, 12)}}>
                    <span style={{fontSize: 22, color: theme.accent, letterSpacing: '0.1em', width: 44}}>{String(i + 1).padStart(2, '0')}</span>
                    <span style={{fontSize: 40, lineHeight: 1.3}}>{item}</span>
                  </div>
                  <Rule progress={fadeIn(frame, start + 6, 20)} />
                </div>
              );
            })}
          </div>
        </div>
      </AbsoluteFill>
    </Frame>
  );
};
