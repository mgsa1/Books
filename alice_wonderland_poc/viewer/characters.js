// Character styles for the iso engine. Each maker returns a THREE.Group with feet at y=0, facing +z,
// and userData { height, legs?, update?(t, camera) }.
//   makeBlocky(c)   — the original look (coat cylinder + sphere head)
//   makeChibi(spec) — big-head Pokémon-style low poly with real costume details (spec per character)
//   makePaper(url)  — HD-2D paper cut-out: the Tenniel-style full-body painting on a camera-facing card
import * as THREE from "three";

const lam = (color, extra = {}) => new THREE.MeshLambertMaterial({ color, flatShading: true, ...extra });
const smooth = (color, extra = {}) => new THREE.MeshLambertMaterial({ color, ...extra });
const shadowAll = (g) => { g.traverse((m) => { if (m.isMesh) m.castShadow = true; }); return g; };

export function makeBlocky(c) {
  const k = { tall: 1.05, average: 0.95, small: 0.85, child: 0.62 }[c.build] ?? 0.95;
  const g = new THREE.Group(), col = c.colors || {};
  const legs = [];
  for (const s of [-1, 1]) {
    const leg = new THREE.Mesh(new THREE.BoxGeometry(0.13, 0.42, 0.14), lam(col.trousers || "#3A342C"));
    leg.geometry.translate(0, -0.21, 0); leg.position.set(s * 0.09, 0.42, 0); g.add(leg); legs.push(leg);
  }
  const coat = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.27, 0.62, 7), lam(col.coat || "#5A4A3A")); coat.position.y = 0.72; g.add(coat);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.15, 8, 6), lam(col.skin || "#D9B48F")); head.position.y = 1.17; g.add(head);
  const hair = new THREE.Mesh(new THREE.SphereGeometry(0.158, 8, 4, 0, Math.PI * 2, 0, Math.PI / 2), lam(col.hair || "#3A2A1E")); hair.position.y = 1.19; hair.rotation.x = -0.25; g.add(hair);
  g.scale.setScalar(k);
  g.userData = { legs, height: 1.5 * k };
  return shadowAll(g);
}

// ---------- chibi ----------
function eyes(g, y, z, spread = 0.085, size = 0.035, color = "#1E1B18") {
  for (const s of [-1, 1]) {
    const e = new THREE.Mesh(new THREE.SphereGeometry(size, 10, 8), smooth(color)); e.scale.set(0.8, 1.15, 0.5); e.position.set(s * spread, y, z); g.add(e);
    const hl = new THREE.Mesh(new THREE.SphereGeometry(size * 0.35, 6, 4), new THREE.MeshBasicMaterial({ color: "#FFFFFF" })); hl.position.set(s * spread + size * 0.25, y + size * 0.35, z + size * 0.35); g.add(hl);
  }
}

export function makeChibiAlice() {
  const g = new THREE.Group(), legs = [];
  const BLUE = "#8DB6DE", WHITE = "#F7F4EC", SKIN = "#F3D6BF", HAIR = "#E8C46A", BLACK = "#1E1B18";
  for (const s of [-1, 1]) {  // legs swing from the hip
    const leg = new THREE.Group(); leg.position.set(s * 0.07, 0.28, 0);
    const stocking = new THREE.Mesh(new THREE.CylinderGeometry(0.042, 0.038, 0.24, 8), smooth(WHITE)); stocking.position.y = -0.13; leg.add(stocking);
    const shoe = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.05, 0.13), smooth(BLACK)); shoe.position.set(0, -0.255, 0.025); leg.add(shoe);
    g.add(leg); legs.push(leg);
  }
  const skirt = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.31, 0.34, 18, 1, true), smooth(BLUE, { side: THREE.DoubleSide })); skirt.position.y = 0.43; g.add(skirt);
  const hem = new THREE.Mesh(new THREE.TorusGeometry(0.31, 0.012, 6, 24), smooth(WHITE)); hem.rotation.x = Math.PI / 2; hem.position.y = 0.265; g.add(hem);
  // pinafore: a white panel wrapping the front of the skirt, plus bib and shoulder frills
  const apron = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.325, 0.3, 18, 1, true, -1.0, 2.0), smooth(WHITE, { side: THREE.DoubleSide })); apron.position.y = 0.44; g.add(apron);
  const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.105, 0.13, 0.2, 14), smooth(BLUE)); torso.position.y = 0.69; g.add(torso);
  const bib = new THREE.Mesh(new THREE.BoxGeometry(0.15, 0.17, 0.02), smooth(WHITE)); bib.position.set(0, 0.69, 0.115); g.add(bib);
  const sash = new THREE.Mesh(new THREE.TorusGeometry(0.125, 0.018, 6, 20), smooth(WHITE)); sash.rotation.x = Math.PI / 2; sash.position.y = 0.6; g.add(sash);
  const bow = new THREE.Mesh(new THREE.SphereGeometry(0.045, 8, 6), smooth(WHITE)); bow.scale.set(1.8, 1, 0.6); bow.position.set(0, 0.6, -0.13); g.add(bow);
  for (const s of [-1, 1]) {
    const puff = new THREE.Mesh(new THREE.SphereGeometry(0.07, 12, 8), smooth(BLUE)); puff.position.set(s * 0.13, 0.75, 0); g.add(puff);
    const frill = new THREE.Mesh(new THREE.SphereGeometry(0.05, 10, 6, 0, Math.PI * 2, 0, Math.PI / 2), smooth(WHITE)); frill.position.set(s * 0.09, 0.79, 0.04); frill.rotation.z = s * 0.6; g.add(frill);
    const arm = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.028, 0.2, 8), smooth(SKIN)); arm.position.set(s * 0.15, 0.62, 0.02); arm.rotation.z = s * 0.18; g.add(arm);
    const hand = new THREE.Mesh(new THREE.SphereGeometry(0.035, 8, 6), smooth(SKIN)); hand.position.set(s * 0.165, 0.51, 0.03); g.add(hand);
  }
  const collar = new THREE.Mesh(new THREE.TorusGeometry(0.06, 0.02, 6, 16), smooth(WHITE)); collar.rotation.x = Math.PI / 2; collar.position.y = 0.8; g.add(collar);
  // big head
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.25, 24, 18), smooth(SKIN)); head.position.y = 1.03; g.add(head);
  eyes(g, 1.01, 0.225);
  for (const s of [-1, 1]) { const cheek = new THREE.Mesh(new THREE.CircleGeometry(0.03, 12), new THREE.MeshBasicMaterial({ color: "#F2A7A0", transparent: true, opacity: 0.7 })); cheek.position.set(s * 0.13, 0.95, 0.215); cheek.rotation.y = s * 0.5; g.add(cheek); }
  const mouth = new THREE.Mesh(new THREE.TorusGeometry(0.02, 0.005, 4, 10, Math.PI), smooth("#B5504A")); mouth.rotation.z = Math.PI; mouth.position.set(0, 0.93, 0.245); g.add(mouth);
  // hair: cap + fringe + long fall down the back, black ribbon
  const cap = new THREE.Mesh(new THREE.SphereGeometry(0.265, 24, 14, 0, Math.PI * 2, 0, Math.PI * 0.55), smooth(HAIR)); cap.position.set(0, 1.05, -0.03); cap.rotation.x = 0.45; g.add(cap);  // tilted back so the face shows
  const fringe = new THREE.Mesh(new THREE.SphereGeometry(0.258, 20, 8, -1.1, 2.2, 0.25, 0.33), smooth(HAIR)); fringe.position.y = 1.05; g.add(fringe);
  const fall = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.27, 0.55, 18, 1, true, Math.PI * 0.62, Math.PI * 0.76), smooth(HAIR, { side: THREE.DoubleSide })); fall.position.set(0, 0.86, -0.02); g.add(fall);
  for (const s of [-1, 1]) { const lock = new THREE.Mesh(new THREE.CapsuleGeometry(0.05, 0.3, 4, 8), smooth(HAIR)); lock.position.set(s * 0.21, 0.86, 0.03); lock.rotation.z = s * 0.12; g.add(lock); }
  const ribbon = new THREE.Mesh(new THREE.TorusGeometry(0.255, 0.018, 6, 30, Math.PI * 1.1), smooth(BLACK)); ribbon.position.set(0, 1.13, 0.02); ribbon.rotation.set(-0.5, 0, Math.PI * -0.05); g.add(ribbon);
  g.userData = { legs, height: 1.3 };
  return shadowAll(g);
}

export function makeChibiRabbit() {
  const g = new THREE.Group(), legs = [];
  const FUR = "#F6F3EE", PINK = "#E9A7A7", RED = "#C2423A", GOLD = "#D9A441", YELLOW = "#E9D27A";
  for (const s of [-1, 1]) {
    const leg = new THREE.Group(); leg.position.set(s * 0.08, 0.22, 0);
    const thigh = new THREE.Mesh(new THREE.SphereGeometry(0.075, 10, 8), smooth(FUR)); thigh.scale.set(1, 1.4, 1); thigh.position.y = -0.08; leg.add(thigh);
    const foot = new THREE.Mesh(new THREE.SphereGeometry(0.06, 10, 6), smooth(FUR)); foot.scale.set(0.9, 0.45, 1.9); foot.position.set(0, -0.2, 0.06); leg.add(foot);
    g.add(leg); legs.push(leg);
  }
  const belly = new THREE.Mesh(new THREE.SphereGeometry(0.17, 18, 14), smooth(FUR)); belly.scale.set(1, 1.15, 0.95); belly.position.y = 0.42; g.add(belly);
  // red jacket (open at the front) over a yellow waistcoat, with tails at the back
  const jacket = new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.2, 0.3, 18, 1, true, 0.7, Math.PI * 2 - 1.4), smooth(RED, { side: THREE.DoubleSide })); jacket.position.y = 0.52; g.add(jacket);
  const vest = new THREE.Mesh(new THREE.CylinderGeometry(0.135, 0.17, 0.26, 16, 1, false, -0.75, 1.5), smooth(YELLOW)); vest.position.y = 0.53; g.add(vest);
  for (let i = 0; i < 3; i++) { const btn = new THREE.Mesh(new THREE.SphereGeometry(0.012, 6, 4), smooth(GOLD)); btn.position.set(0, 0.6 - i * 0.07, 0.165 - i * 0.008); g.add(btn); }
  for (const s of [-1, 1]) { const tail = new THREE.Mesh(new THREE.BoxGeometry(0.09, 0.2, 0.02), smooth(RED)); tail.position.set(s * 0.06, 0.32, -0.18); tail.rotation.x = 0.2; g.add(tail); }
  const cravat = new THREE.Mesh(new THREE.SphereGeometry(0.04, 8, 6), smooth("#FFFFFF")); cravat.scale.set(1.6, 0.8, 0.8); cravat.position.set(0, 0.67, 0.12); g.add(cravat);
  for (const s of [-1, 1]) {
    const sleeve = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.04, 0.2, 8), smooth(RED)); sleeve.position.set(s * 0.17, 0.55, 0.05); sleeve.rotation.set(-0.6, 0, s * 0.3); g.add(sleeve);
    const paw = new THREE.Mesh(new THREE.SphereGeometry(0.035, 8, 6), smooth(FUR)); paw.position.set(s * 0.13, 0.48, 0.15); g.add(paw);
  }
  // pocket watch held up, gold, with a chain to the waistcoat
  const watch = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 0.015, 16), smooth(GOLD, { emissive: "#5A3A10", emissiveIntensity: 0.3 })); watch.rotation.x = Math.PI / 2 - 0.4; watch.position.set(0.12, 0.52, 0.2); g.add(watch);
  const face = new THREE.Mesh(new THREE.CircleGeometry(0.036, 16), smooth("#FBF7EE")); face.position.set(0.12, 0.525, 0.21); face.rotation.x = -0.4; g.add(face);
  const chain = new THREE.Mesh(new THREE.TorusGeometry(0.06, 0.004, 4, 16, Math.PI), smooth(GOLD)); chain.position.set(0.06, 0.5, 0.17); chain.rotation.set(0.3, 0.2, Math.PI); g.add(chain);
  const tailPuff = new THREE.Mesh(new THREE.SphereGeometry(0.06, 10, 8), smooth(FUR)); tailPuff.position.set(0, 0.3, -0.19); g.add(tailPuff);
  // head: big, with muzzle, pink nose, spectacles, long ears with pink insides
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.21, 22, 16), smooth(FUR)); head.scale.set(1, 0.95, 1); head.position.y = 0.88; g.add(head);
  for (const s of [-1, 1]) { const m = new THREE.Mesh(new THREE.SphereGeometry(0.06, 12, 8), smooth(FUR)); m.position.set(s * 0.04, 0.82, 0.17); g.add(m); }
  const nose = new THREE.Mesh(new THREE.SphereGeometry(0.022, 8, 6), smooth(PINK)); nose.position.set(0, 0.85, 0.215); g.add(nose);
  eyes(g, 0.9, 0.18, 0.09, 0.03, "#7A2A2A");
  for (const s of [-1, 1]) { const lens = new THREE.Mesh(new THREE.TorusGeometry(0.04, 0.006, 6, 18), smooth(GOLD)); lens.position.set(s * 0.09, 0.9, 0.2); g.add(lens); }
  const bridge = new THREE.Mesh(new THREE.CylinderGeometry(0.004, 0.004, 0.06, 4), smooth(GOLD)); bridge.rotation.z = Math.PI / 2; bridge.position.set(0, 0.905, 0.21); g.add(bridge);
  const ears = [];
  for (const s of [-1, 1]) {
    const ear = new THREE.Group(); ear.position.set(s * 0.08, 1.04, -0.02); ear.rotation.set(-0.15, 0, s * -0.18);
    const outer = new THREE.Mesh(new THREE.CapsuleGeometry(0.05, 0.32, 4, 10), smooth(FUR)); outer.scale.set(1, 1, 0.55); outer.position.y = 0.2; ear.add(outer);
    const inner = new THREE.Mesh(new THREE.CapsuleGeometry(0.03, 0.26, 4, 8), smooth(PINK)); inner.scale.set(1, 1, 0.3); inner.position.set(0, 0.2, 0.02); ear.add(inner);
    g.add(ear); ears.push(ear);
  }
  g.userData = { legs, height: 1.45, update: (t) => ears.forEach((e, i) => (e.rotation.x = -0.15 + Math.sin(t * 3 + i) * 0.06)) };
  return shadowAll(g);
}

// ---------- HD-2D paper cut-out ----------
const loader = new THREE.TextureLoader();
export function makePaper(url, height = 1.35) {
  const g = new THREE.Group();
  const card = new THREE.Group(); g.add(card);
  const tex = loader.load(url, (t) => {
    const w = height * t.image.width / t.image.height;
    const geo = new THREE.PlaneGeometry(w, height).translate(0, height / 2, 0);
    // front: the painting; a slightly larger dark copy behind reads as the cut paper's edge
    const front = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ map: t, alphaTest: 0.35, side: THREE.DoubleSide }));
    front.castShadow = true;
    front.customDepthMaterial = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, map: t, alphaTest: 0.35 });
    const edge = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ map: t, alphaTest: 0.35, color: "#3A2E24", side: THREE.DoubleSide }));
    edge.scale.set(1.025, 1.012, 1); edge.position.z = -0.012;
    card.add(edge, front);
  });
  tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
  // a soft contact shadow so the figure sits on the ground
  const blob = new THREE.Mesh(new THREE.CircleGeometry(0.22, 20), new THREE.MeshBasicMaterial({ color: "#000000", transparent: true, opacity: 0.22, depthWrite: false }));
  blob.rotation.x = -Math.PI / 2; blob.position.y = 0.01; blob.scale.set(1.3, 0.8, 1); g.add(blob);
  g.userData = {
    height,
    // always face the iso camera; walking = a little hop and sway, like a toy-theatre figure pushed on a stick
    update: (t, camera, moving) => {
      card.rotation.y = Math.atan2(camera.position.x - g.position.x, camera.position.z - g.position.z) - g.rotation.y;
      card.position.y = moving ? Math.abs(Math.sin(t * 14)) * 0.05 : 0;
      card.rotation.z = moving ? Math.sin(t * 14) * 0.05 : Math.sin(t * 1.5) * 0.01;
    },
  };
  return g;
}

// ---------- pixel-art sprite (Pokémon-style): front / back / side views, nearest-neighbour ----------
export function makePixel(base, height = 1.25, tint = "#FFFFFF") {
  const g = new THREE.Group(), card = new THREE.Group(); g.add(card);
  const views = {};
  let mesh = null, aspect = 1;
  for (const v of ["front", "back", "side"]) {
    views[v] = loader.load(`${base}_${v}.png`, (t) => {
      t.magFilter = THREE.NearestFilter; t.minFilter = THREE.NearestFilter; t.generateMipmaps = false; t.colorSpace = THREE.SRGBColorSpace;
      if (v === "front") {
        aspect = t.image.width / t.image.height;
        const geo = new THREE.PlaneGeometry(height * aspect, height).translate(0, height / 2, 0);
        mesh = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ map: t, alphaTest: 0.5, side: THREE.DoubleSide, color: tint }));  // tint = moonlight at night
        mesh.castShadow = true;
        mesh.customDepthMaterial = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, map: t, alphaTest: 0.5 });
        card.add(mesh);
      }
    });
  }
  const blob = new THREE.Mesh(new THREE.CircleGeometry(0.22, 20), new THREE.MeshBasicMaterial({ color: "#000000", transparent: true, opacity: 0.25, depthWrite: false }));
  blob.rotation.x = -Math.PI / 2; blob.position.y = 0.01; blob.scale.set(1.2, 0.7, 1); g.add(blob);
  g.userData = {
    height,
    update: (t, camera, moving) => {
      if (!mesh) return;
      // which way is the character facing, relative to the camera? pick the sprite view (mirror for the left side)
      const toCam = Math.atan2(camera.position.x - g.position.x, camera.position.z - g.position.z);
      let rel = ((g.rotation.y - toCam) % (Math.PI * 2) + Math.PI * 3) % (Math.PI * 2) - Math.PI;  // -π..π, 0 = facing camera
      // iso grid: the four walking directions sit exactly on the 45° diagonals, so bin by quadrant, not by ±45°:
      //   down-right (rel  0..90°)  → side, facing right     down-left (rel -90..0°) → front
      //   up-left   (rel -180..-90°) → side, mirrored left   up-right  (rel 90..180°) → back
      const eps = 1e-3;
      const view = rel > eps && rel <= Math.PI / 2 + eps ? "side" : rel <= eps && rel > -Math.PI / 2 + eps ? "front" : rel <= -Math.PI / 2 + eps ? "side" : "back";
      const mirror = view === "side" && rel < 0;  // the painted side view faces right
      if (mesh.material.map !== views[view]) { mesh.material.map = views[view]; mesh.customDepthMaterial.map = views[view]; mesh.material.needsUpdate = true; }
      card.rotation.y = toCam - g.rotation.y;
      card.scale.x = mirror ? -1 : 1;
      card.position.y = moving ? (Math.floor(t * 8) % 2) * 0.04 : 0;  // two-frame bob, retro style
    },
  };
  return g;
}

// ---------- voxel model designed by Argon from the painting ----------
export function makeVoxel(model, height = 1.35) {
  const g = new THREE.Group(), body = new THREE.Group(); g.add(body);
  const { w, d, h, palette, layers } = model, s = height / h;
  const byColor = {};
  layers.forEach((layer, y) => layer.forEach((row, z) => [...row].forEach((c, x) => {
    if (c !== "." && palette[c]) (byColor[c] ||= []).push([(x - w / 2 + 0.5) * s, (y + 0.5) * s, (z - d / 2 + 0.5) * s]);
  })));
  const geo = new THREE.BoxGeometry(s, s, s), dummy = new THREE.Object3D();
  for (const [c, cells] of Object.entries(byColor)) {
    const im = new THREE.InstancedMesh(geo, new THREE.MeshLambertMaterial({ color: palette[c] }), cells.length);
    cells.forEach((p, i) => { dummy.position.set(...p); dummy.updateMatrix(); im.setMatrixAt(i, dummy.matrix); });
    im.castShadow = true; im.receiveShadow = true; body.add(im);
  }
  g.userData = { height, update: (t, camera, moving) => { body.position.y = moving ? Math.abs(Math.sin(t * 10)) * 0.05 : 0; body.rotation.z = moving ? Math.sin(t * 10) * 0.04 : 0; } };
  return g;
}
