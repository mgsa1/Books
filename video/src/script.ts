import {SPEED} from './time';

/**
 * Every word that appears on screen or in the voiceover lives here.
 * Edit this file, not the scenes. Scene durations are in seconds.
 *
 * `narration` is what the voice says. It is also shown as subtitles at the
 * bottom of the frame, 12 words max per line, like the product itself does.
 * `on` is text drawn inside the scene.
 */

export const FPS = 30;
export const WIDTH = 1920;
export const HEIGHT = 1080;
export const TRANSITION_SECONDS = 0.5;

/** Set to 'voiceover.mp3' once a narration file exists in video/public/. */
export const VOICEOVER_FILE: string | null = null;
/** Draw the narration as subtitles at the bottom of the frame. */
export const SHOW_NARRATION_SUBTITLES = false;

export const brand = {
  name: 'ExpLit',
  tagline: 'Explore Litterature',
  oneLiner: 'A book becomes a game you can hear and play.',
  event: 'Gemini 4 Argon SF Hackathon · October 2026',
  closing: 'Every story, for everyone.',
  builtWith: 'Built with Gemini 4 Argon, Antigravity Managed Agents, Nano Banana and Flash TTS',
  link: 'github.com/your-handle/explit',
};

export const script = {
  title: {
    seconds: 5,
    narration: ['ExpLit. Explore literature.', 'A book becomes a game you can hear and play.'],
  },

  friend: {
    seconds: 11,
    narration: [
      'My best friend is dyslexic.',
      'A page is a wall. A story is not.',
      'What is the use of a book without pictures or conversations?',
    ],
    label: '01 / The friend',
    on: ['My best friend is dyslexic.', 'A page is a wall.', 'A story is not.'],
    // Public domain. Alice's Adventures in Wonderland, chapter 1. Repeated to fill the frame.
    wall:
      'Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to do: once or twice she had peeped into the book her sister was reading, but it had no pictures or conversations in it, "and what is the use of a book," thought Alice "without pictures or conversations?" So she was considering in her own mind (as well as she could, for the hot day made her feel very sleepy and stupid), whether the pleasure of making a daisy-chain would be worth the trouble of getting up and picking the daisies, when suddenly a White Rabbit with pink eyes ran close by her. There was nothing so very remarkable in that; nor did Alice think it so very much out of the way to hear the Rabbit say to itself, "Oh dear! Oh dear! I shall be late!" (when she thought it over afterwards, it occurred to her that she ought to have wondered at this, but at the time it all seemed quite natural); but when the Rabbit actually took a watch out of its waistcoat-pocket, and looked at it, and then hurried on, Alice started to her feet, for it flashed across her mind that she had never before seen a rabbit with either a waistcoat-pocket, or a watch to take out of it, and burning with curiosity, she ran across the field after it, and fortunately was just in time to see it pop down a large rabbit-hole under the hedge. ',
    quote: '"What is the use of a book without pictures or conversations?"',
    quoteBy: 'Alice, chapter 1',
  },

  pipeline: {
    seconds: 15,
    narration: [
      'ExpLit takes three things.',
      'A book. A look. And an open-source game.',
      'Gemini 4 Argon reads the whole book and the whole game repository.',
      'A Managed Agent rewrites the game in a sandbox.',
      'Then it rewrites that game into one that tells the book.',
    ],
    // Why Argon, listed under the Argon badge.
    reasons: [
      {title: '1M-token context', body: 'the whole book and the whole game in one pass'},
      {title: 'Managed Agents', body: 'rewrites and builds the game in a sandbox'},
      {title: 'One model family', body: 'Nano Banana art, Flash TTS voices, Argon review'},
    ],
    label: '02 / How it works',
    inputs: [
      {label: 'Book', sub: 'any EPUB'},
      {label: 'Look', sub: 'one to three style images'},
      {label: 'Game', sub: 'an open-source repository'},
    ],
    core: 'Gemini 4 Argon',
    coreSub: 'reads the whole book and the whole repository',
    output: {label: 'A new game', sub: 'that tells the book'},
    produces: ['story.json · every beat cited', 'original characters & backdrops', 'a voice for every line', 'rewritten source code'],
  },

  rules: {
    seconds: 16,
    narration: [
      'Every line is spoken aloud and shown as a subtitle. Twelve words, no more.',
      'No timers. No lives. No failing. You explore and you talk.',
      'Nobody spoils the ending. And every scene cites the paragraph it comes from.',
    ],
    label: '03 / The rules',
    heading: 'Built for my friend',
    checklist: [
      'Every line is spoken aloud',
      'Subtitle, 12 words max',
      'Dyslexia-friendly type',
      'No timers, no lives, no fail',
      'No spoilers ahead of you',
      'Every beat cites its paragraph',
    ],
  },

  watch: {
    seconds: 12,
    narration: [
      'And the game watches itself.',
      'It records how it was played. Argon reviews the session.',
      'It finds where it broke and where my friend got stuck.',
      'The fix is in before the next launch.',
    ],
    label: '03 / The loop',
    heading: 'The game watches itself',
    loop: [
      {label: 'Play', sub: 'session recorded'},
      {label: 'Evidence', sub: 'screens, actions, errors'},
      {label: 'Review', sub: 'broke, stuck, confused'},
      {label: 'Patch', sub: 'small diff, replayed'},
      {label: 'Next launch', sub: 'the fix is in'},
    ],
    footer: 'Offline, between sessions. No AI calls while playing.',
  },

  why: {
    seconds: 17,
    narration: [
      'Why Gemini 4 Argon?',
      'The whole book goes in.',
      'Then every source file of the game.',
      'Then every piece of artwork we generated for it.',
      'It all fits in one context, with room to spare.',
      'One pass rewrites the game. No chunks, no drift.',
      'Managed Agents do the rewrite in a sandbox and hand back the repo.',
    ],
    label: '04 / Why Argon',
    heading: 'Why Gemini 4 Argon',
    intro: 'One million tokens. The whole book, the whole game, and all its artwork in a single context.',
    window: {
      total: 1_000_000,
      totalLabel: '1,000,000 tokens',
      spare: 'room to spare',
      // Each segment fills in order. `files` tick past at the fill head while it fills.
      segments: [
        {
          title: 'The book',
          detail: 'alice.epub · 12 chapters',
          tokens: 35_000,
          files: ['ch01 Down the Rabbit-Hole', 'ch02 The Pool of Tears', 'ch03 A Caucus-Race', 'ch04 The Rabbit Sends in a Little Bill', 'ch05 Advice from a Caterpillar', 'ch06 Pig and Pepper', 'ch07 A Mad Tea-Party', 'ch08 The Queen\'s Croquet-Ground', 'ch09 The Mock Turtle\'s Story', 'ch10 The Lobster Quadrille', 'ch11 Who Stole the Tarts?', 'ch12 Alice\'s Evidence'],
        },
        {
          title: 'The game',
          detail: '412 source files',
          tokens: 180_000,
          files: ['package.json', 'index.html', 'src/main.js', 'src/scenes/Boot.js', 'src/scenes/Preload.js', 'src/scenes/Level.js', 'src/scenes/HUD.js', 'src/objects/Player.js', 'src/objects/Enemy.js', 'src/objects/Block.js', 'src/objects/Item.js', 'src/physics/collisions.js', 'src/audio/sfx.js', 'src/maps/level-1.json', 'src/maps/level-2.json', 'src/utils/input.js', 'src/utils/camera.js', 'src/utils/state.js', 'src/ui/dialogue.js', 'src/ui/menu.js'],
        },
        {
          title: 'The artwork',
          detail: '64 generated images',
          tokens: 90_000,
          files: ['characters/alice.png', 'characters/white-rabbit.png', 'characters/caterpillar.png', 'characters/cheshire-cat.png', 'characters/queen-of-hearts.png', 'backdrops/ch01-riverbank.png', 'backdrops/ch04-rabbit-house.png', 'backdrops/ch07-tea-party.png', 'tiles/wonderland-ground.png', 'items/golden-key.png', 'items/drink-me.png', 'items/pocket-watch.png'],
        },
        {
          title: 'Story and style',
          detail: 'story.json · style.json',
          tokens: 15_000,
          files: ['story.json', 'style.json'],
        },
      ],
    },
    points: [
      {title: 'One pass', body: 'No chunking, no retrieval, no drift. The game is rewritten whole, consistent with the book.'},
      {title: 'Managed Agents', body: 'Antigravity rewrites the game in a sandbox, builds it, and returns the repo.'},
      {title: 'One model family', body: 'Nano Banana draws the world. Flash TTS voices every line. Argon reviews play sessions as video.'},
    ],
  },

  /** Standalone scene (composition "Architecture"): the four decisions, left to right. */
  architecture: {
    seconds: 15,
    narration: [
      'Argon reads the whole book and the whole game at once.',
      'The game\'s own code says which assets to make, and how.',
      'A Managed Agent rewires the game in a sandbox. Nothing redrawn.',
      'Then the game plays itself and keeps only fixes that pass.',
    ],
    label: 'Under the hood',
    heading: 'Four decisions',
    steps: [
      {title: 'Read it all', sub: 'the whole book and the whole game repository, in one context', note: 'no chunks, no drift'},
      {title: 'Fill the slots', sub: 'the code sets the format, the book the subject, the look the style', note: 'checked against real files'},
      {title: 'Rewire, not redraw', sub: 'a Managed Agent rewrites the game in a sandbox', note: 'engine and controls stay'},
      {title: 'Watch and fix', sub: 'plays itself, patches with evidence, keeps what passes', note: 'no AI while she plays'},
    ],
  },

  outro: {
    seconds: 5,
    narration: ['ExpLit.', 'Every story, for everyone.'],
  },
} as const;

export const order = ['friend', 'title', 'pipeline', 'watch', 'outro'] as const;
export type SceneId = (typeof order)[number];

// Scene seconds are story time; the video plays them SPEED times faster (see time.ts).
export const sceneFrames = (id: SceneId) => Math.round((script[id].seconds * FPS) / SPEED);
export const transitionFrames = Math.round(TRANSITION_SECONDS * FPS);
export const totalFrames =
  order.reduce((sum, id) => sum + sceneFrames(id), 0) - transitionFrames * (order.length - 1);
