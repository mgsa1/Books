import React from 'react';
import {p} from './theme';

/** Simple 100x100 icons with the same thick-outline look as the characters. */

export const BookIcon: React.FC = () => (
  <svg viewBox="0 0 100 100" width="100%" height="100%">
    <path d="M14 22 q18 -6 36 6 v56 q-18 -10 -36 -6z" fill={p.sky} stroke={p.ink} strokeWidth="5" strokeLinejoin="round" />
    <path d="M86 22 q-18 -6 -36 6 v56 q18 -10 36 -6z" fill={p.white} stroke={p.ink} strokeWidth="5" strokeLinejoin="round" />
    <path d="M58 40 h20 M58 52 h20 M58 64 h14" stroke={p.ink} strokeWidth="4" strokeLinecap="round" />
  </svg>
);

export const PaletteIcon: React.FC = () => (
  <svg viewBox="0 0 100 100" width="100%" height="100%">
    <path d="M50 14 a36 36 0 1 0 0 72 c8 0 6 -10 12 -12 c8 -2 24 2 24 -14 a36 36 0 0 0 -36 -46z" fill={p.white} stroke={p.ink} strokeWidth="5" strokeLinejoin="round" />
    <circle cx="34" cy="38" r="7" fill={p.clay} stroke={p.ink} strokeWidth="3" />
    <circle cx="52" cy="28" r="7" fill={p.butter} stroke={p.ink} strokeWidth="3" />
    <circle cx="68" cy="40" r="7" fill={p.mint} stroke={p.ink} strokeWidth="3" />
    <circle cx="32" cy="60" r="7" fill={p.lilac} stroke={p.ink} strokeWidth="3" />
  </svg>
);

export const GamepadIcon: React.FC = () => (
  <svg viewBox="0 0 100 100" width="100%" height="100%">
    <path d="M28 30 h44 a22 22 0 0 1 20 30 l-6 18 a10 10 0 0 1 -18 2 l-6 -10 h-24 l-6 10 a10 10 0 0 1 -18 -2 l-6 -18 a22 22 0 0 1 20 -30z" fill={p.mint} stroke={p.ink} strokeWidth="5" strokeLinejoin="round" />
    <path d="M34 44 v16 M26 52 h16" stroke={p.ink} strokeWidth="5" strokeLinecap="round" />
    <circle cx="66" cy="48" r="4.5" fill={p.clay} stroke={p.ink} strokeWidth="2" />
    <circle cx="76" cy="56" r="4.5" fill={p.sky} stroke={p.ink} strokeWidth="2" />
  </svg>
);

export const SparkIcon: React.FC = () => (
  <svg viewBox="0 0 100 100" width="100%" height="100%">
    <path d="M50 10 l10 28 l30 12 l-30 12 l-10 28 l-10 -28 l-30 -12 l30 -12z" fill={p.butter} stroke={p.ink} strokeWidth="5" strokeLinejoin="round" />
    <circle cx="80" cy="20" r="6" fill={p.clay} stroke={p.ink} strokeWidth="3" />
  </svg>
);

export const JarLid: React.FC = () => (
  <svg viewBox="0 0 200 40" width="100%" height="100%" preserveAspectRatio="none">
    <rect x="4" y="4" width="192" height="32" rx="12" fill={p.butter} stroke={p.ink} strokeWidth="5" />
  </svg>
);

export const LoopIcon: React.FC = () => (
  <svg viewBox="0 0 100 100" width="100%" height="100%">
    <path d="M78 42 a30 30 0 1 0 2 22" fill="none" stroke={p.ink} strokeWidth="7" strokeLinecap="round" />
    <path d="M78 42 l4 -18 M78 42 l-18 -4" stroke={p.ink} strokeWidth="7" strokeLinecap="round" />
    <circle cx="50" cy="50" r="13" fill={p.rose} stroke={p.ink} strokeWidth="5" />
  </svg>
);
