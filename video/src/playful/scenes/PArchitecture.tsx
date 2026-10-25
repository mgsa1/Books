import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {Badge, PFrame, PSubtitles, Squiggle, Sticker, clamp, fadeIn, popIn} from '../ui';
import {BookIcon, GamepadIcon, LoopIcon, PaletteIcon} from '../icons';
import {p, pastels} from '../theme';
import {SHOW_NARRATION_SUBTITLES, script} from '../../script';

/**
 * The architecture at a glance: four decisions, left to right, one line each.
 * Words live in script.architecture. Standalone composition "Architecture".
 */
const {heading, steps, label, narration, seconds} = script.architecture;
const icons = [BookIcon, PaletteIcon, GamepadIcon, LoopIcon];
const colors = [p.sky, p.rose, p.mint, p.butter];

const cardW = 380;
const cardH = 400;
const gap = 72;
const left = (1920 - (steps.length * cardW + (steps.length - 1) * gap)) / 2;
const top = 330;
const xs = steps.map((_, i) => left + i * (cardW + gap));

export const PArchitecture: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  // Cards follow the subtitle schedule (useSubtitleLine: 0.2 s lead, then time shared by
  // word count) and land a few frames before their line, after the heading has settled.
  const total = Math.round(seconds * fps);
  const lead = Math.round(fps * 0.2);
  const weights = narration.map((l) => l.split(' ').length + 2);
  const sum = weights.reduce((a, b) => a + b, 0);
  const starts: number[] = [];
  let cursor = lead;
  for (let i = 0; i < steps.length; i++) {
    starts.push(Math.max(i === 0 ? 22 : 0, cursor - 8));
    cursor += Math.round((weights[i] / sum) * (total - lead));
  }

  return (
    <PFrame label={label}>
      {/* heading */}
      <div style={{position: 'absolute', left: 120, top: 130, ...popIn(frame, fps, 8), transformOrigin: 'left center', width: 'fit-content'}}>
        <Sticker tilt={-1.5} color={p.white} style={{padding: '16px 34px 22px'}}>
          <div style={{fontFamily: p.display, fontWeight: 700, fontSize: 76, lineHeight: 1}}>{heading}</div>
        </Sticker>
      </div>

      {/* arrows between cards, drawn as the next card arrives */}
      {steps.slice(1).map((_, i) => (
        <Squiggle
          key={i}
          from={[xs[i] + cardW + 8, top + cardH / 2]}
          to={[xs[i + 1] - 8, top + cardH / 2]}
          progress={interpolate(frame, [starts[i + 1] - 14, starts[i + 1] + 2], [0, 1], clamp)}
          bend={36}
        />
      ))}

      {/* cards */}
      {steps.map((st, i) => {
        const Icon = icons[i];
        const tilt = (i % 2 ? 1 : -1) * 1.6;
        return (
          <div key={st.title} style={{position: 'absolute', left: xs[i], top, width: cardW, ...popIn(frame, fps, starts[i]), transformOrigin: 'center bottom'}}>
            <Sticker tilt={tilt} color={p.white} shadow={9} style={{height: cardH, padding: '34px 30px 28px', display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center'}}>
              <div style={{position: 'absolute', top: -26, left: -22}}>
                <Badge color={colors[i]} size={66}>{i + 1}</Badge>
              </div>
              <div style={{width: 110, height: 110, borderRadius: '50%', background: colors[i], border: `5px solid ${p.ink}`, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 14, flexShrink: 0}}>
                <Icon />
              </div>
              <div style={{fontFamily: p.display, fontWeight: 700, fontSize: 44, lineHeight: 1.05, marginTop: 26}}>{st.title}</div>
              <div style={{fontFamily: p.body, fontSize: 24, lineHeight: 1.35, color: p.muted, marginTop: 14}}>{st.sub}</div>
            </Sticker>
            {/* hand-written note under the card */}
            <div
              style={{
                marginTop: 34,
                textAlign: 'center',
                fontFamily: p.hand,
                fontWeight: 700,
                fontSize: 38,
                color: p.ink,
                transform: `rotate(${-tilt}deg)`,
                opacity: fadeIn(frame, starts[i] + 16, 12),
              }}
            >
              <span style={{background: pastels[(i + 3) % pastels.length], padding: '2px 16px', borderRadius: 12, boxDecorationBreak: 'clone'}}>{st.note}</span>
            </div>
          </div>
        );
      })}
    </PFrame>
  );
};

/** Drop-in composition: the scene plus its narration as subtitles. */
export const Architecture: React.FC = () => {
  const {fps} = useVideoConfig();
  const frames = Math.round(seconds * fps);
  return (
    <AbsoluteFill style={{background: p.paper}}>
      <PArchitecture />
      {SHOW_NARRATION_SUBTITLES ? <PSubtitles lines={narration} durationInFrames={frames} /> : null}
    </AbsoluteFill>
  );
};
