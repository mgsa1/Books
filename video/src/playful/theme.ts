import {loadFont as loadFredoka} from '@remotion/google-fonts/Fredoka';
import {loadFont as loadCaveat} from '@remotion/google-fonts/Caveat';
import {loadFont as loadAtkinson} from '@remotion/google-fonts/AtkinsonHyperlegible';

const fredoka = loadFredoka('normal', {weights: ['500', '700'], subsets: ['latin']});
const caveat = loadCaveat('normal', {weights: ['700'], subsets: ['latin']});
const atkinson = loadAtkinson();

/** The playful look: cream paper, thick ink outlines, pastel stickers. */
export const p = {
  display: fredoka.fontFamily,
  hand: caveat.fontFamily,
  body: atkinson.fontFamily,
  paper: '#FFF7E8',
  ink: '#1C1A17',
  white: '#FFFFFF',
  clay: '#E2714A',
  sky: '#9FD3F2',
  mint: '#B8E3C2',
  butter: '#FFD66B',
  rose: '#F7B9C9',
  lilac: '#CDBDF2',
  muted: '#6E675E',
};

export const pastels = [p.clay, p.sky, p.mint, p.butter, p.rose, p.lilac];
