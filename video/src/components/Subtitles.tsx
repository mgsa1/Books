import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {theme} from '../theme';

/**
 * Narration shown as a subtitle: 12 words max, high contrast, generous
 * spacing, in the product's own typeface. Lines share the scene's time in
 * proportion to their word count.
 */
/** Which narration line is on screen at this frame. Lines share the time by word count. */
export const useSubtitleLine = (lines: readonly string[], durationInFrames: number): string | null => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const lead = Math.round(fps * 0.2);
  const usable = durationInFrames - lead;
  const weights = lines.map((l) => l.split(' ').length + 2);
  const total = weights.reduce((a, b) => a + b, 0);
  let start = lead;
  for (let i = 0; i < lines.length; i++) {
    const len = Math.round((weights[i] / total) * usable);
    if (frame >= start && frame < start + len) return lines[i];
    start += len;
  }
  return null;
};

export const Subtitles: React.FC<{lines: readonly string[]; durationInFrames: number}> = ({
  lines,
  durationInFrames,
}) => {
  const current = useSubtitleLine(lines, durationInFrames);
  if (!current) return null;

  return (
    <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', pointerEvents: 'none'}}>
      <div
        style={{
          marginBottom: 64,
          maxWidth: 1500,
          padding: '6px 24px',
          background: theme.bg,
          boxShadow: `0 0 28px 22px ${theme.bg}`,
          fontFamily: theme.body,
          fontSize: 34,
          lineHeight: 1.4,
          letterSpacing: '0.01em',
          wordSpacing: '0.08em',
          color: theme.ink,
          textAlign: 'center',
        }}
      >
        {current}
      </div>
    </AbsoluteFill>
  );
};
