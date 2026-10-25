import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Frame} from '../components/Frame';
import {fadeIn, rise} from '../components/anim';
import {Rule} from '../components/Rule';
import {brand} from '../script';
import {theme} from '../theme';
import {useSceneFrame} from '../time';

export const Title: React.FC = () => {
  const frame = useSceneFrame();
  return (
    <Frame>
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
        <div style={{fontFamily: theme.display, fontSize: 260, lineHeight: 1, letterSpacing: '-0.01em', ...rise(frame, 4, 24, 24)}}>
          ExpLit
        </div>
        <div style={{width: 160, marginTop: 36}}>
          <Rule progress={fadeIn(frame, 22, 20)} color={theme.accent} />
        </div>
        <div style={{fontSize: 26, letterSpacing: '0.22em', textTransform: 'uppercase', color: theme.muted, marginTop: 36, ...rise(frame, 30, 18, 10)}}>
          {brand.tagline}
        </div>
        <div style={{fontSize: 40, color: theme.ink, marginTop: 56, ...rise(frame, 50, 18, 10)}}>{brand.oneLiner}</div>
      </AbsoluteFill>
      <div style={{position: 'absolute', top: 72, right: 120, fontSize: 22, letterSpacing: '0.18em', textTransform: 'uppercase', color: theme.muted, opacity: fadeIn(frame, 60, 14)}}>
        {brand.event}
      </div>
    </Frame>
  );
};
