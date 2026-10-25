import React from 'react';
import {AbsoluteFill, interpolate, useVideoConfig} from 'remotion';
import {Badge, Cutout, PFrame, Pill, Sticker, clamp, fadeIn, popIn} from '../ui';
import {p, pastels} from '../theme';
import {art} from '../art';
import {script} from '../../script';
import {useSceneFrame} from '../../time';

const {heading, loop, footer, label} = script.watch;
const cx = 960;
const cy = 600;
const rx = 640;
const ry = 230;
const angleAt = (t: number) => -Math.PI / 2 + t * Math.PI * 2;

export const PWatch: React.FC = () => {
  const frame = useSceneFrame();
  const {fps} = useVideoConfig();
  const nodeStart = fps * 1.2;
  const runStart = fps * 3.5;
  const lap = fps * 7.5;
  const t = interpolate(frame, [runStart, runStart + lap], [0, 1], clamp);
  const a = angleAt(t);
  const runner = {x: cx + Math.cos(a) * rx, y: cy + Math.sin(a) * ry};
  const active = frame >= runStart && t < 1 ? Math.floor(t * loop.length) : -1;
  const hop = Math.abs(Math.sin(frame / 4)) * 14;

  return (
    <PFrame label={label}>
      <AbsoluteFill style={{padding: '70px 120px 0'}}>
        <div style={{...popIn(frame, fps, 6), transformOrigin: 'left center', width: 'fit-content'}}>
          <Sticker tilt={-1.5} color={p.rose} style={{padding: '18px 36px 24px'}}>
            <div style={{fontFamily: p.display, fontWeight: 700, fontSize: 80, lineHeight: 1}}>{heading}</div>
          </Sticker>
        </div>
        <div style={{marginTop: 22, marginLeft: 8, fontFamily: p.hand, fontWeight: 700, fontSize: 36, color: p.muted, opacity: fadeIn(frame, 24, 14)}}>{footer}</div>
      </AbsoluteFill>

      <svg style={{position: 'absolute', inset: 0}} viewBox="0 0 1920 1080">
        <ellipse cx={cx} cy={cy} rx={rx} ry={ry} fill="none" stroke={p.ink} strokeWidth={6} strokeDasharray="4 22" strokeLinecap="round" opacity={fadeIn(frame, nodeStart, 20)} />
      </svg>

      {loop.map((n, i) => {
        const ang = angleAt(i / loop.length);
        const x = cx + Math.cos(ang) * rx;
        const y = cy + Math.sin(ang) * ry;
        const isActive = active === i;
        return (
          <div key={n.label} style={{position: 'absolute', left: x - 170, top: y - 70, width: 340, ...popIn(frame, fps, nodeStart + i * 8), transformOrigin: 'center'}}>
            <Sticker tilt={(i % 2 ? 1 : -1) * 2} color={isActive ? pastels[i] : p.white} shadow={isActive ? 10 : 6} style={{display: 'flex', alignItems: 'center', gap: 16, padding: '14px 20px', transform: `rotate(${(i % 2 ? 1 : -1) * 2}deg) scale(${isActive ? 1.08 : 1})`}}>
              <Badge color={pastels[i]} size={52}>{i + 1}</Badge>
              <div>
                <div style={{fontFamily: p.display, fontWeight: 700, fontSize: 36, lineHeight: 1}}>{n.label}</div>
                <div style={{fontSize: 20, color: p.muted, marginTop: 4}}>{n.sub}</div>
              </div>
            </Sticker>
          </div>
        );
      })}

      {/* The White Rabbit runs the loop */}
      {frame >= runStart && t < 1 ? (
        <div style={{position: 'absolute', zIndex: 5, left: runner.x - 70, top: runner.y - 200 - hop, width: 140, height: 150, transform: `scaleX(${Math.sin(a) < 0 ? -1 : 1})`}}>
          <Cutout src={art.whiteRabbit} width={140} height={150} />
        </div>
      ) : null}
      <div style={{position: 'absolute', left: 1500, top: 110, opacity: fadeIn(frame, runStart + lap, 12)}}>
        <Pill color={p.butter} style={{transform: 'rotate(3deg)'}}>Next launch: fixed.</Pill>
      </div>
    </PFrame>
  );
};
