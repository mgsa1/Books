import React from 'react';
import {AbsoluteFill, Audio, Sequence, staticFile} from 'remotion';
import {TransitionSeries, linearTiming} from '@remotion/transitions';
import {fade} from '@remotion/transitions/fade';
import {Subtitles} from './components/Subtitles';
import {order, sceneFrames, script, transitionFrames, SHOW_NARRATION_SUBTITLES, VOICEOVER_FILE} from './script';
import {Title} from './scenes/Title';
import {Friend} from './scenes/Friend';
import {Pipeline} from './scenes/Pipeline';
import {Watch} from './scenes/Watch';
import {Outro} from './scenes/Outro';
import {theme} from './theme';
import {SPEED, SpeedContext} from './time';

const components = {
  title: Title,
  friend: Friend,
  pipeline: Pipeline,
  watch: Watch,
  outro: Outro,
} as const;

export const ExpLit: React.FC = () => {
  // Subtitles are laid over the whole series so they survive transitions.
  let cursor = 0;
  const subtitleTracks = order.map((id, i) => {
    const from = cursor;
    const len = sceneFrames(id);
    cursor += len - transitionFrames;
    return {id, from, len, lines: script[id].narration, key: i};
  });

  return (
    <AbsoluteFill style={{background: theme.bg}}>
      <SpeedContext.Provider value={SPEED}>
      <TransitionSeries>
        {order.map((id, i) => {
          const Scene = components[id];
          const nodes: React.ReactNode[] = [
            <TransitionSeries.Sequence key={id} durationInFrames={sceneFrames(id)}>
              <Scene />
            </TransitionSeries.Sequence>,
          ];
          if (i < order.length - 1) {
            nodes.push(
              <TransitionSeries.Transition
                key={`${id}-t`}
                presentation={fade()}
                timing={linearTiming({durationInFrames: transitionFrames})}
              />,
            );
          }
          return nodes;
        })}
      </TransitionSeries>
      </SpeedContext.Provider>

      {SHOW_NARRATION_SUBTITLES
        ? subtitleTracks.map((t) => (
            <Sequence key={t.key} from={t.from} durationInFrames={t.len - transitionFrames} layout="none">
              <Subtitles lines={t.lines} durationInFrames={t.len - transitionFrames} />
            </Sequence>
          ))
        : null}

      {VOICEOVER_FILE ? <Audio src={staticFile(VOICEOVER_FILE)} /> : null}
    </AbsoluteFill>
  );
};
