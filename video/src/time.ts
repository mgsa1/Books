import {createContext, useContext} from 'react';
import {useCurrentFrame} from 'remotion';

/**
 * Global playback speed for the main video. Scene timings in script.ts and inside
 * each scene are authored in "story seconds"; the video plays them SPEED times faster.
 * Raise it to tighten everything at once.
 */
export const SPEED = 1.5;

/** Compositions that should play sped-up provide their speed here. Default 1 (unchanged). */
export const SpeedContext = createContext(1);

/** The current frame in story time: use it instead of useCurrentFrame for animation. */
export const useSceneFrame = () => useCurrentFrame() * useContext(SpeedContext);
