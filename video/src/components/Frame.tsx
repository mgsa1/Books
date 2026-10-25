import React, {PropsWithChildren} from 'react';
import {AbsoluteFill} from 'remotion';
import {theme} from '../theme';
import {fadeIn} from './anim';
import {useSceneFrame} from '../time';

/** Paper background and a small section label, like a chapter mark. */
export const Frame: React.FC<PropsWithChildren<{label?: string}>> = ({children, label}) => {
  const frame = useSceneFrame();
  return (
    <AbsoluteFill style={{background: theme.bg, fontFamily: theme.body, color: theme.ink}}>
      {children}
      {label ? (
        <div
          style={{
            position: 'absolute',
            top: 72,
            left: 120,
            fontSize: 22,
            letterSpacing: '0.18em',
            textTransform: 'uppercase',
            color: theme.muted,
            padding: '8px 20px',
            margin: '-8px -20px',
            background: theme.bg,
            boxShadow: `0 0 16px 20px ${theme.bg}`,
            opacity: fadeIn(frame, 0, 14),
          }}
        >
          {label}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
