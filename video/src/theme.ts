import {loadFont as loadBody} from '@remotion/google-fonts/AtkinsonHyperlegible';
import {loadFont as loadDisplay} from '@remotion/google-fonts/InstrumentSerif';

// Body: the product's own dyslexia-friendly typeface. Display: a quiet serif.
const body = loadBody();
const display = loadDisplay('normal', {weights: ['400'], subsets: ['latin']});

export const theme = {
  body: body.fontFamily,
  display: display.fontFamily,
  bg: '#F2EEE6',
  ink: '#1C1A17',
  muted: '#7A746B',
  accent: '#D4714E',
  line: 'rgba(28,26,23,0.14)',
  soft: 'rgba(28,26,23,0.05)',
};
