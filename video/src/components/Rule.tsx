import React from 'react';
import {theme} from '../theme';

/** A hairline that draws from left to right. `progress` 0 → 1. */
export const Rule: React.FC<{progress: number; width?: number | string; color?: string}> = ({
  progress,
  width = '100%',
  color = theme.line,
}) => (
  <div style={{width, height: 1, background: theme.soft}}>
    <div style={{width: `${Math.max(0, Math.min(1, progress)) * 100}%`, height: 1, background: color}} />
  </div>
);
