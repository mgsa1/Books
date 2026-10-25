import React from 'react';
import {AbsoluteFill, interpolate, useVideoConfig} from 'remotion';
import {Frame} from '../components/Frame';
import {clamp, fadeIn, rise} from '../components/anim';
import {Rule} from '../components/Rule';
import {script} from '../script';
import {theme} from '../theme';
import {useSceneFrame} from '../time';

const {heading, intro, window: win, points, label} = script.why;

// When each segment fills, in seconds.
const segTimes: [number, number][] = [
  [1.6, 4.2],
  [4.4, 8.6],
  [8.8, 11.6],
  [11.8, 12.6],
];
const spareAt = 12.9;
const pointsAt = 13.8;

const fills = [theme.accent, theme.ink, 'rgba(28,26,23,0.55)', 'rgba(28,26,23,0.3)'];
const W = 1680;
const H = 64;

const fmt = (n: number) => `~${n.toLocaleString('en-US')} tokens`;

export const Why: React.FC = () => {
  const frame = useSceneFrame();
  const {fps} = useVideoConfig();

  const progress = segTimes.map(([a, b]) => interpolate(frame, [a * fps, b * fps], [0, 1], clamp));
  const widths = win.segments.map((s, i) => (progress[i] * s.tokens * W) / win.total);
  const lefts = widths.reduce<number[]>((acc, w, i) => [...acc, (acc[i - 1] ?? 0) + (i === 0 ? 0 : widths[i - 1])], []);
  const head = widths.reduce((a, b) => a + b, 0);

  // Which segment is filling right now, and which of its files is at the head.
  const activeIndex = progress.findIndex((p) => p > 0 && p < 1);
  const active = activeIndex >= 0 ? win.segments[activeIndex] : null;
  const activeFile = active ? active.files[Math.min(active.files.length - 1, Math.floor(progress[activeIndex] * active.files.length))] : null;

  const usedTokens = win.segments.reduce((a, s) => a + s.tokens, 0);
  const spare = win.total - usedTokens;

  return (
    <Frame label={label}>
      <AbsoluteFill style={{padding: '150px 120px 0'}}>
        <div style={{fontFamily: theme.display, fontSize: 96, lineHeight: 1.02, ...rise(frame, 6, 22, 20)}}>{heading}</div>
        <div style={{fontSize: 28, color: theme.muted, marginTop: 16, maxWidth: 1400, lineHeight: 1.45, ...rise(frame, 18, 18, 10)}}>{intro}</div>

        {/* The context window */}
        <div style={{position: 'relative', marginTop: 96, width: W, opacity: fadeIn(frame, fps * 1, 16)}}>
          {/* ticker at the fill head */}
          <div style={{position: 'absolute', left: head, top: -52, transform: 'translateX(-1px)', whiteSpace: 'nowrap', opacity: active ? 1 : 0}}>
            <span style={{fontSize: 22, color: theme.ink}}>{active?.title}</span>
            <span style={{fontSize: 22, color: theme.muted}}> · {activeFile}</span>
          </div>
          <div style={{position: 'absolute', left: head, top: -22, width: 1, height: 22, background: theme.ink, opacity: active ? 1 : 0}} />

          <div style={{position: 'relative', width: W, height: H, border: `1px solid ${theme.ink}`, background: theme.soft}}>
            {win.segments.map((s, i) => (
              <div key={s.title} style={{position: 'absolute', left: lefts[i], top: 0, width: widths[i], height: H, background: fills[i]}} />
            ))}
            <div style={{position: 'absolute', right: 20, top: 0, height: H, display: 'flex', alignItems: 'center', fontSize: 22, color: theme.muted, letterSpacing: '0.06em', opacity: fadeIn(frame, spareAt * fps, 16)}}>
              {fmt(spare).replace('~', '')} {win.spare}
            </div>
          </div>
          <div style={{position: 'absolute', right: 0, top: H + 14, fontSize: 20, color: theme.muted, letterSpacing: '0.12em', textTransform: 'uppercase'}}>{win.totalLabel}</div>

          {/* legend */}
          <div style={{display: 'flex', gap: 56, marginTop: 60}}>
            {win.segments.map((s, i) => (
              <div key={s.title} style={{display: 'flex', gap: 14, alignItems: 'flex-start', opacity: fadeIn(frame, segTimes[i][0] * fps, 14)}}>
                <div style={{width: 12, height: 12, marginTop: 14, background: fills[i]}} />
                <div>
                  <div style={{fontFamily: theme.display, fontSize: 34, lineHeight: 1.1}}>{s.title}</div>
                  <div style={{fontSize: 20, color: theme.muted, marginTop: 6}}>
                    {s.detail}<span style={{opacity: fadeIn(frame, segTimes[i][1] * fps, 10)}}> · {fmt(s.tokens)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Points */}
        <div style={{marginTop: 72}}>
          <Rule progress={fadeIn(frame, pointsAt * fps, 24)} />
          <div style={{display: 'flex', gap: 72, marginTop: 36}}>
            {points.map((p, i) => (
              <div key={p.title} style={{flex: 1, ...rise(frame, (pointsAt + 0.2 + i * 0.6) * fps, 18, 12)}}>
                <div style={{fontFamily: theme.display, fontSize: 40, lineHeight: 1.1}}>{p.title}</div>
                <div style={{fontSize: 22, color: theme.muted, marginTop: 8, lineHeight: 1.45}}>{p.body}</div>
              </div>
            ))}
          </div>
        </div>
      </AbsoluteFill>
    </Frame>
  );
};
