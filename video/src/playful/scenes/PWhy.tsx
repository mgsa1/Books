import React from 'react';
import {AbsoluteFill, interpolate, useVideoConfig} from 'remotion';
import {Actor, Badge, Bubble, Cutout, PFrame, Pill, Sticker, clamp, fadeIn, popIn} from '../ui';
import {p} from '../theme';
import {art} from '../art';
import {script} from '../../script';
import {useSceneFrame} from '../../time';

const {heading, intro, window: win, points, label} = script.why;

const segTimes: [number, number][] = [
  [1.6, 4.2],
  [4.4, 8.6],
  [8.8, 11.6],
  [11.8, 12.6],
];
const spareAt = 12.9;
const pointsAt = 13.8;
const fills = [p.clay, p.sky, p.mint, p.lilac];

// The jar
const jarX = 1250;
const jarY = 250;
const jarW = 520;
const jarH = 560;

const fmt = (n: number) => `~${n.toLocaleString('en-US')} tokens`;

export const PWhy: React.FC = () => {
  const frame = useSceneFrame();
  const {fps} = useVideoConfig();
  const progress = segTimes.map(([a, b]) => interpolate(frame, [a * fps, b * fps], [0, 1], clamp));
  const heights = win.segments.map((s, i) => (progress[i] * s.tokens * jarH) / win.total);
  const bottoms = heights.reduce<number[]>((acc, h, i) => [...acc, i === 0 ? 0 : acc[i - 1] + heights[i - 1]], []);
  const level = heights.reduce((a, b) => a + b, 0);
  const activeIndex = progress.findIndex((q) => q > 0 && q < 1);
  const active = activeIndex >= 0 ? win.segments[activeIndex] : null;
  const activeFile = active ? active.files[Math.min(active.files.length - 1, Math.floor(progress[activeIndex] * active.files.length))] : null;
  const spare = win.total - win.segments.reduce((a, s) => a + s.tokens, 0);
  const jarIn = popIn(frame, fps, fps * 1);

  return (
    <PFrame label={label}>
      <AbsoluteFill style={{padding: '140px 120px 0'}}>
        <div style={{...popIn(frame, fps, 6), transformOrigin: 'left center', width: 'fit-content'}}>
          <Sticker tilt={-1.5} color={p.sky} style={{padding: '18px 36px 24px'}}>
            <div style={{fontFamily: p.display, fontWeight: 700, fontSize: 80, lineHeight: 1}}>{heading}</div>
          </Sticker>
        </div>
        <div style={{fontSize: 28, color: p.muted, marginTop: 24, maxWidth: 980, lineHeight: 1.45, opacity: fadeIn(frame, 18, 16)}}>{intro}</div>

        {/* legend */}
        <div style={{display: 'flex', flexDirection: 'column', gap: 16, marginTop: 36, width: 'fit-content'}}>
          {win.segments.map((s, i) => (
            <div key={s.title} style={{...popIn(frame, fps, segTimes[i][0] * fps), transformOrigin: 'left center'}}>
              <Pill style={{display: 'flex', alignItems: 'center', gap: 16, fontSize: 30}}>
                <span style={{width: 18, height: 18, borderRadius: 4, background: fills[i], border: `3px solid ${p.ink}`, display: 'inline-block'}} />
                <span style={{fontWeight: 700}}>{s.title}</span>
                <span style={{color: p.muted, fontFamily: p.body, fontSize: 22}}>
                  {s.detail}
                  <span style={{opacity: fadeIn(frame, segTimes[i][1] * fps, 10)}}> · {fmt(s.tokens)}</span>
                </span>
              </Pill>
            </div>
          ))}
        </div>

        {/* points */}
        <div style={{display: 'flex', gap: 24, marginTop: 40, width: 1080}}>
          {points.map((pt, i) => (
            <div key={pt.title} style={{flex: 1, ...popIn(frame, fps, (pointsAt + 0.3 + i * 0.7) * fps), transformOrigin: 'bottom center'}}>
              <Sticker tilt={(i - 1) * 1.5} shadow={6} style={{padding: '14px 20px', minHeight: 170, display: 'flex', flexDirection: 'column', gap: 6}}>
                <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                  <Badge color={fills[i]} size={40}>{i + 1}</Badge>
                  <div style={{fontFamily: p.display, fontWeight: 700, fontSize: 27, lineHeight: 1, whiteSpace: 'nowrap'}}>{pt.title}</div>
                </div>
                <div style={{fontSize: 17, color: p.muted, lineHeight: 1.35}}>{pt.body}</div>
              </Sticker>
            </div>
          ))}
        </div>
      </AbsoluteFill>

      {/* The jar */}
      <div style={{position: 'absolute', left: jarX, top: jarY, width: jarW, height: jarH, ...jarIn, transformOrigin: 'bottom center'}}>
        <div style={{position: 'absolute', left: 60, top: -46, width: jarW - 120, height: 54, background: p.butter, border: `6px solid ${p.ink}`, borderRadius: 16, boxShadow: `6px 6px 0 ${p.ink}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: p.display, fontWeight: 700, fontSize: 26}}>
          {win.totalLabel}
        </div>
        <div style={{position: 'absolute', inset: 0, background: p.white, border: `6px solid ${p.ink}`, borderRadius: '28px 28px 60px 60px', boxShadow: `10px 10px 0 ${p.ink}`, overflow: 'hidden'}}>
          {win.segments.map((s, i) => (
            <div key={s.title} style={{position: 'absolute', left: 0, right: 0, bottom: bottoms[i], height: heights[i], background: fills[i], borderTop: heights[i] > 2 ? `4px solid ${p.ink}` : 'none'}} />
          ))}
          <div style={{position: 'absolute', left: 0, right: 0, top: 40, textAlign: 'center', fontFamily: p.hand, fontWeight: 700, fontSize: 40, lineHeight: 1.1, opacity: fadeIn(frame, spareAt * fps, 16)}}>
            {spare.toLocaleString('en-US')} tokens
            <br />
            {win.spare}
          </div>
        </div>
        {/* ticker at the fill level */}
        {active ? (
          <div style={{position: 'absolute', right: jarW + 24, top: jarH - level - 30, whiteSpace: 'nowrap'}}>
            <Pill color={fills[activeIndex]} style={{fontSize: 22}}>
              {active.title} · <span style={{fontFamily: p.body, fontWeight: 400}}>{activeFile}</span>
            </Pill>
          </div>
        ) : null}
      </div>

      <Actor x={1560} y={20} size={200} start={fps * 1.4} seed={4}>
        <Cutout src={art.pooh} width={200} height={200} tilt={-4} />
        <Bubble side="left" opacity={fadeIn(frame, spareAt * fps + 6, 10)} top={-30} size={34}>
          Room for more!
        </Bubble>
      </Actor>
    </PFrame>
  );
};
