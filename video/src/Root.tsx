import React from 'react';
import {Composition} from 'remotion';
import {ExpLit} from './ExpLit';
import {ExpLitPlayful} from './playful/ExpLitPlayful';
import {Architecture} from './playful/scenes/PArchitecture';
import {README_FRAMES, README_HEIGHT, README_WIDTH, ReadmeBanner} from './playful/scenes/PReadme';
import {FPS, HEIGHT, WIDTH, script, totalFrames} from './script';

export const Root: React.FC = () => (
  <>
    {/* Lean cut */}
    <Composition id="ExpLit" component={ExpLit} durationInFrames={totalFrames} fps={FPS} width={WIDTH} height={HEIGHT} />
    {/* Playful cut: same script and timing, public-domain illustrations */}
    <Composition id="ExpLitPlayful" component={ExpLitPlayful} durationInFrames={totalFrames} fps={FPS} width={WIDTH} height={HEIGHT} />
    {/* Standalone: the four architecture decisions, left to right (playful style) */}
    <Composition id="Architecture" component={Architecture} durationInFrames={Math.round(script.architecture.seconds * FPS)} fps={FPS} width={WIDTH} height={HEIGHT} />
    {/* GitHub README banner (playful style), rendered as a still */}
    <Composition id="ReadmeBanner" component={ReadmeBanner} durationInFrames={README_FRAMES} fps={FPS} width={README_WIDTH} height={README_HEIGHT} />
  </>
);
