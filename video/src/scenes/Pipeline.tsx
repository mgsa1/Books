import React from 'react';
import {AbsoluteFill, interpolate, useVideoConfig} from 'remotion';
import {Frame} from '../components/Frame';
import {clamp, rise} from '../components/anim';
import {Rule} from '../components/Rule';
import {script} from '../script';
import {theme} from '../theme';
import {useSceneFrame} from '../time';

const {inputs, core, coreSub, output, reasons, label} = script.pipeline;

const Item: React.FC<{title: string; sub: string; start: number; frame: number; accent?: boolean; big?: boolean}> = ({title, sub, start, frame, accent, big}) => (
  <div style={{...rise(frame, start, 20, 16)}}>
    <div style={{fontFamily: theme.display, fontSize: big ? 84 : 72, lineHeight: 1.05, color: accent ? theme.accent : theme.ink, whiteSpace: 'nowrap'}}>{title}</div>
    <div style={{fontSize: 24, color: theme.muted, marginTop: 10, maxWidth: 360, lineHeight: 1.4}}>{sub}</div>
  </div>
);

export const Pipeline: React.FC = () => {
  const frame = useSceneFrame();
  const {fps} = useVideoConfig();
  const inputStart = fps * 1.2;
  const lineStart = fps * 4.2;
  const coreStart = fps * 5;
  const reasonsStart = fps * 6.4;
  const outStart = fps * 10.6;

  return (
    <Frame label={label}>
      <AbsoluteFill style={{padding: '0 120px', justifyContent: 'center'}}>
        {/* Inputs */}
        <div style={{display: 'flex', gap: 120}}>
          {inputs.map((inp, i) => (
            <Item key={inp.label} title={inp.label} sub={inp.sub} start={inputStart + i * 12} frame={frame} />
          ))}
        </div>

        <div style={{margin: '56px 0'}}>
          <Rule progress={interpolate(frame, [lineStart, lineStart + 24], [0, 1], clamp)} color={theme.ink} />
        </div>

        {/* Core and output */}
        <div style={{display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between'}}>
          <Item title={core} sub={coreSub} start={coreStart} frame={frame} big />
          <div style={{flex: 1, margin: '0 60px 36px', ...rise(frame, outStart - 10, 20, 0)}}>
            <Rule progress={interpolate(frame, [outStart - 10, outStart + 14], [0, 1], clamp)} color={theme.accent} />
          </div>
          <Item title={output.label} sub={output.sub} start={outStart} frame={frame} accent big />
        </div>

        {/* Why Argon: three reasons under it */}
        <div style={{display: 'flex', gap: 64, marginTop: 64}}>
          {reasons.map((r, i) => (
            <div key={r.title} style={{flex: 1, display: 'flex', gap: 20, alignItems: 'baseline', ...rise(frame, reasonsStart + i * fps * 0.7, 18, 12)}}>
              <span style={{fontSize: 22, color: theme.accent, letterSpacing: '0.1em'}}>{String(i + 1).padStart(2, '0')}</span>
              <div>
                <div style={{fontFamily: theme.display, fontSize: 40, lineHeight: 1.1}}>{r.title}</div>
                <div style={{fontSize: 22, color: theme.muted, marginTop: 6, lineHeight: 1.4}}>{r.body}</div>
              </div>
            </div>
          ))}
        </div>
      </AbsoluteFill>
    </Frame>
  );
};
