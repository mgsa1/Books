import React from 'react';
import {Composition} from 'remotion';
import {ExpLit} from './ExpLit';
import {ExpLitPlayful} from './playful/ExpLitPlayful';
import {Architecture} from './playful/scenes/PArchitecture';
import {FPS, HEIGHT, WIDTH, script, totalFrames} from './script';

export const Root: React.FC = () => (
  <>
    {/* Lean cut */}
    <Composition id="ExpLit" component={ExpLit} durationInFrames={totalFrames} fps={FPS} width={WIDTH} height={HEIGHT} />
    {/* Playful cut: same script and timing, public-domain illustrations */}
    <Composition id="ExpLitPlayful" component={ExpLitPlayful} durationInFrames={totalFrames} fps={FPS} width={WIDTH} height={HEIGHT} />
    {/* Standalone: the four architecture decisions, left to right (playful style) */}
    <Composition id="Architecture" component={Architecture} durationInFrames={Math.round(script.architecture.seconds * FPS)} fps={FPS} width={WIDTH} height={HEIGHT} />
  </>
);
