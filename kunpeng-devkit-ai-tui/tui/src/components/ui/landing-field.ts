const FIELD_GLYPHS = [" ", " ", " ", " ", " ", " ", "·", "·", "·", "-", "+", "+"] as const;

export interface LandingFieldFrame {
  readonly base: string;
  readonly halo: string;
  readonly core: string;
}

export function landingHash(x: number, y: number): number {
  let hash = (x * 374_761_393 + y * 668_265_263) >>> 0;
  hash = ((hash ^ (hash >> 13)) * 1_274_126_177) >>> 0;
  return ((hash >>> 8) & 65_535) / 65_535;
}

export function landingValueNoise(x: number, y: number, scale: number): number {
  const gx = x / scale;
  const gy = y / scale;
  const x0 = Math.floor(gx);
  const y0 = Math.floor(gy);
  const fx = gx - x0;
  const fy = gy - y0;
  const u = fx * fx * (3 - 2 * fx);
  const v = fy * fy * (3 - 2 * fy);
  return (
    landingHash(x0, y0) * (1 - u) * (1 - v) +
    landingHash(x0 + 1, y0) * u * (1 - v) +
    landingHash(x0, y0 + 1) * (1 - u) * v +
    landingHash(x0 + 1, y0 + 1) * u * v
  );
}

export function createLandingField(columns: number, rows: number): Float32Array {
  const width = Math.max(1, Math.floor(columns));
  const height = Math.max(1, Math.floor(rows));
  const centerX = width * 0.5;
  const centerY = height * 0.48;
  const field = new Float32Array(width * height);
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const dx = (x - centerX) / (width * 0.5);
      const dy = (y - centerY) / (height * 0.5);
      const radius = Math.sqrt(dx * dx * 1.02 + dy * dy * 0.96);
      let grainHash = (x * 374_761_393 + y * 668_265_263) >>> 0;
      grainHash = ((grainHash ^ (grainHash >> 13)) * 1_274_126_177) >>> 0;
      const grain = ((grainHash >>> 8) & 1_023) / 1_023;
      const organic =
        landingValueNoise(x, y, 6.5) * 0.88 + landingValueNoise(x, y, 2.4) * 0.44 - 0.56;
      field[y * width + x] = Math.max(
        0,
        Math.min(0.999, (radius - 0.6) * 1.5 + organic * 0.58 + grain * 0.16),
      );
    }
  }
  return field;
}

function renderLayer(
  columns: number,
  rows: number,
  characterAt: (x: number, y: number) => string,
): string {
  const lines: string[] = [];
  for (let y = 0; y < rows; y += 1) {
    let line = "";
    for (let x = 0; x < columns; x += 1) line += characterAt(x, y);
    lines.push(line.trimEnd());
  }
  return lines.join("\n");
}

export function renderLandingField(field: Float32Array, columns: number, rows: number): string {
  return renderLayer(columns, rows, (x, y) => {
    const density = field[y * columns + x] ?? 0;
    return (
      FIELD_GLYPHS[Math.min(FIELD_GLYPHS.length - 1, Math.floor(density * FIELD_GLYPHS.length))] ??
      " "
    );
  });
}

function seededUnit(seed: number): number {
  let value = seed >>> 0;
  value += 0x6d2b79f5;
  value = Math.imul(value ^ (value >>> 15), value | 1);
  value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
  return ((value ^ (value >>> 14)) >>> 0) / 4_294_967_296;
}

export function renderLandingWave(
  field: Float32Array,
  columns: number,
  rows: number,
  tick: number,
  seed = 0x4b554e50,
): Pick<LandingFieldFrame, "halo" | "core"> {
  const phase = Math.max(0, Math.floor(tick));
  const eligible: number[] = [];
  for (let index = 0; index < columns * rows; index += 1)
    if ((field[index] ?? 0) > 0.3) eligible.push(index);
  if (eligible.length === 0) return { halo: "", core: "" };
  const sparkCount = Math.max(24, Math.round(eligible.length * 0.016));
  const amplitude = new Float32Array(columns * rows);
  const put = (x: number, y: number, value: number) => {
    if (x < 0 || y < 0 || x >= columns || y >= rows) return;
    const cell = y * columns + x;
    if (value > (amplitude[cell] ?? 0)) amplitude[cell] = value;
  };
  for (let index = 0; index < sparkCount; index += 1) {
    let cycle = 0;
    let cycleStart = 0;
    let life = 1;
    while (cycleStart + life <= phase) {
      cycleStart += life;
      life = 7 + Math.floor(seededUnit(seed ^ Math.imul(index + 1, 97) ^ cycle) * 22);
      cycle += 1;
    }
    const age = phase - cycleStart;
    const cell =
      eligible[
        Math.floor(
          seededUnit(seed ^ Math.imul(index + 1, 65_537) ^ Math.imul(cycle + 1, 17)) *
            eligible.length,
        )
      ];
    if (cell === undefined) continue;
    const glow = Math.sin((Math.PI * age) / life);
    if (glow <= 0.02) continue;
    const x = cell % columns;
    const y = Math.floor(cell / columns);
    put(x, y, glow);
    const big = seededUnit(seed ^ Math.imul(index + 1, 131_071) ^ Math.imul(cycle + 1, 29)) < 0.34;
    if (big) {
      put(x - 1, y, glow * 0.52);
      put(x + 1, y, glow * 0.52);
      put(x, y - 1, glow * 0.44);
      put(x, y + 1, glow * 0.44);
    }
  }
  const waveGlyphs = [" ", "·", "·", "-", "+", "*", "#"] as const;
  return {
    halo: renderLayer(columns, rows, (x, y) => {
      const cell = y * columns + x;
      const value = (amplitude[cell] ?? 0) * (0.8 + 0.28 * (field[cell] ?? 0));
      return value < 0.14
        ? " "
        : (waveGlyphs[Math.min(6, Math.floor(((value - 0.14) / 0.46) * 7))] ?? " ");
    }),
    core: renderLayer(columns, rows, (x, y) => {
      const cell = y * columns + x;
      const value = (amplitude[cell] ?? 0) * (0.8 + 0.28 * (field[cell] ?? 0));
      return value < 0.56
        ? " "
        : (waveGlyphs[Math.min(6, Math.floor(((value - 0.56) / 0.44) * 7))] ?? " ");
    }),
  };
}

export function createLandingFieldFrame(
  columns: number,
  rows: number,
  tick = 0,
): LandingFieldFrame {
  const field = createLandingField(columns, rows);
  return {
    base: renderLandingField(field, columns, rows),
    ...renderLandingWave(field, columns, rows, tick),
  };
}
