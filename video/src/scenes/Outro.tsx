import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Frame} from '../components/Frame';
import {fadeIn, rise} from '../components/anim';
import {Rule} from '../components/Rule';
import {brand} from '../script';
import {theme} from '../theme';
import {useSceneFrame} from '../time';

export const Outro: React.FC = () => {
  const frame = useSceneFrame();
  return (
    <Frame>
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
        <div style={{fontFamily: theme.display, fontSize: 220, lineHeight: 1, ...rise(frame, 4, 24, 24)}}>ExpLit</div>
        <div style={{width: 160, marginTop: 32}}>
          <Rule progress={fadeIn(frame, 22, 20)} color={theme.accent} />
        </div>
        <div style={{fontFamily: theme.display, fontSize: 64, marginTop: 36, ...rise(frame, 32, 18, 10)}}>{brand.closing}</div>
        <div style={{fontSize: 24, color: theme.muted, marginTop: 72, textAlign: 'center', lineHeight: 1.7, maxWidth: 1200, opacity: fadeIn(frame, 60, 16)}}>
          {brand.builtWith}
          <br />
          {brand.link}
        </div>
      </AbsoluteFill>
    </Frame>
  );
};
