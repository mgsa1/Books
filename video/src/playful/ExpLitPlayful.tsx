import React from 'react';
import {AbsoluteFill, Audio, Sequence, staticFile} from 'remotion';
import {TransitionSeries, linearTiming} from '@remotion/transitions';
import {fade} from '@remotion/transitions/fade';
import {PSubtitles} from './ui';
import {p} from './theme';
import {order, sceneFrames, script, transitionFrames, SHOW_NARRATION_SUBTITLES, VOICEOVER_FILE} from '../script';
import {PFriend} from './scenes/PFriend';
import {PTitle} from './scenes/PTitle';
import {PPipeline} from './scenes/PPipeline';
import {PWatch} from './scenes/PWatch';
import {POutro} from './scenes/POutro';
import {SPEED, SpeedContext} from '../time';

/** Same scenes, same script, same timing as ExpLit, in the playful style. */
const components = {
  friend: PFriend,
  title: PTitle,
  pipeline: PPipeline,
  watch: PWatch,
  outro: POutro,
} as const;

export const ExpLitPlayful: React.FC = () => {
  let cursor = 0;
  const tracks = order.map((id, i) => {
    const from = cursor;
    const len = sceneFrames(id);
    cursor += len - transitionFrames;
    return {id, from, len, lines: script[id].narration, key: i};
  });

  return (
    <AbsoluteFill style={{background: p.paper}}>
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
            nodes.push(<TransitionSeries.Transition key={`${id}-t`} presentation={fade()} timing={linearTiming({durationInFrames: transitionFrames})} />);
          }
          return nodes;
        })}
      </TransitionSeries>
      </SpeedContext.Provider>
      {SHOW_NARRATION_SUBTITLES
        ? tracks.map((t) => (
            <Sequence key={t.key} from={t.from} durationInFrames={t.len - transitionFrames} layout="none">
              <PSubtitles lines={t.lines} durationInFrames={t.len - transitionFrames} />
            </Sequence>
          ))
        : null}
      {VOICEOVER_FILE ? <Audio src={staticFile(VOICEOVER_FILE)} /> : null}
    </AbsoluteFill>
  );
};
