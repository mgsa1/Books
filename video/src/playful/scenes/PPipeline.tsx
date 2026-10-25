import React from 'react';
import {AbsoluteFill, interpolate, useVideoConfig} from 'remotion';
import {Actor, Badge, Cutout, PFrame, Squiggle, Sticker, bounce, clamp, fadeIn, popIn} from '../ui';
import {BookIcon, GamepadIcon, PaletteIcon, SparkIcon} from '../icons';
import {p} from '../theme';
import {art} from '../art';
import {script} from '../../script';
import {useSceneFrame} from '../../time';

const {inputs, core, coreSub, output, reasons, label} = script.pipeline;
const icons = [BookIcon, PaletteIcon, GamepadIcon];
const colors = [p.sky, p.rose, p.mint];
const inputX = 130;
const inputYs = [180, 420, 660];
const cardW = 460;
const cardH = 170;
const coreX = 960;
const coreY = 400;
const coreR = 180;
const reasonColors = [p.sky, p.mint, p.lilac];

export const PPipeline: React.FC = () => {
  const frame = useSceneFrame();
  const {fps} = useVideoConfig();
  const inputStart = fps * 1.2;
  const arrowStart = fps * 4.2;
  const coreStart = fps * 5;
  const reasonsStart = fps * 6.4;
  const outStart = fps * 10.6;
  const coreS = bounce(frame, fps, coreStart, 8);
  const wobble = Math.sin(frame / 9) * 2;

  return (
    <PFrame label={label}>
      {inputYs.map((y, i) => (
        <Squiggle key={i} from={[inputX + cardW + 10, y + cardH / 2]} to={[coreX - coreR - 6, coreY + (i - 1) * 40]} progress={interpolate(frame, [arrowStart + i * 6, arrowStart + 22 + i * 6], [0, 1], clamp)} bend={(1 - i) * 90} />
      ))}
      <Squiggle from={[coreX + coreR + 6, coreY]} to={[1330, coreY]} progress={interpolate(frame, [outStart - 12, outStart + 8], [0, 1], clamp)} color={p.clay} bend={30} />

      {inputs.map((inp, i) => {
        const Icon = icons[i];
        return (
          <div key={inp.label} style={{position: 'absolute', left: inputX, top: inputYs[i], width: cardW, ...popIn(frame, fps, inputStart + i * 12), transformOrigin: 'left center'}}>
            <Sticker tilt={i === 1 ? 1.5 : -1.5} style={{display: 'flex', alignItems: 'center', gap: 24, padding: '20px 28px', height: cardH}}>
              <div style={{width: 96, height: 96, flexShrink: 0}}>
                <Icon />
              </div>
              <div>
                <div style={{fontFamily: p.display, fontWeight: 700, fontSize: 54, lineHeight: 1}}>{inp.label}</div>
                <div style={{fontSize: 24, color: p.muted, marginTop: 8}}>{inp.sub}</div>
              </div>
            </Sticker>
          </div>
        );
      })}

      {/* Argon badge */}
      <div style={{position: 'absolute', left: coreX - coreR, top: coreY - coreR, width: coreR * 2, height: coreR * 2, transform: `scale(${coreS}) rotate(${wobble}deg)`}}>
        <div style={{position: 'absolute', inset: 0, borderRadius: '50%', background: p.butter, border: `6px solid ${p.ink}`, boxShadow: `10px 10px 0 ${p.ink}`, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: 30}}>
          <div style={{width: 70, height: 70, marginBottom: 6}}>
            <SparkIcon />
          </div>
          <div style={{fontFamily: p.display, fontWeight: 700, fontSize: 42, lineHeight: 1}}>{core}</div>
          <div style={{fontFamily: p.hand, fontWeight: 700, fontSize: 27, lineHeight: 1.15, marginTop: 10, opacity: fadeIn(frame, coreStart + 14, 12)}}>{coreSub}</div>
        </div>
      </div>

      {/* Output */}
      <div style={{position: 'absolute', left: 1340, top: coreY - 110, width: 470, ...popIn(frame, fps, outStart), transformOrigin: 'left center'}}>
        <Sticker tilt={2} color={p.clay} style={{padding: '26px 30px'}}>
          <div style={{fontFamily: p.display, fontWeight: 700, fontSize: 58, lineHeight: 1, color: p.white, textShadow: `3px 3px 0 ${p.ink}`}}>{output.label}</div>
          <div style={{fontSize: 26, color: p.ink, marginTop: 10}}>{output.sub}</div>
        </Sticker>
      </div>
      <Actor x={1500} y={500} size={300} start={outStart + 10} blob={p.sky} seed={2}>
        <Cutout src={art.whiteRabbit} width={300} height={300} tilt={6} />
      </Actor>

      {/* Why Argon: three reasons under the badge */}
      <div style={{position: 'absolute', left: 700, top: coreY + coreR + 50, width: 620, display: 'flex', flexDirection: 'column', gap: 18}}>
        {reasons.map((r, i) => (
          <div key={r.title} style={{...popIn(frame, fps, reasonsStart + i * fps * 0.7), transformOrigin: 'center'}}>
            <Sticker tilt={(i - 1) * 1.2} shadow={6} style={{display: 'flex', alignItems: 'center', gap: 18, padding: '12px 24px 12px 14px', borderRadius: 999}}>
              <Badge color={reasonColors[i]} size={52}>{i + 1}</Badge>
              <div>
                <div style={{fontFamily: p.display, fontWeight: 700, fontSize: 32, lineHeight: 1}}>{r.title}</div>
                <div style={{fontSize: 22, color: p.muted, marginTop: 4}}>{r.body}</div>
              </div>
            </Sticker>
          </div>
        ))}
      </div>
    </PFrame>
  );
};
