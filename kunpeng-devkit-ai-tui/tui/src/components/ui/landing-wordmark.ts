/**
 * 启动页字标。
 *
 * 关键约束：**字标必须和鲲鹏鸟画在同一套像素网格上**。
 *
 * 鲲鹏鸟用 `▀ ▄ █` 半块字符，一个终端格装上下两个子像素，所以它的像素是方的。
 * 字标若改用「一个 `█` = 一个像素」，像素就变成 1:2 的竖矩形——字被拉高一倍，
 * 笔画粗细失衡，`A` 会读成 `H`。两者并排时网格不一致，一眼就能看出别扭。
 *
 * 所以这里同样走半块：字模是 5×7 子像素，渲染成 4 个终端行（7 子行，末行半用）。
 * 视觉比例 5:7，是正常字面比例；换算规则见 `UI-SPEC.md` COMP-SIZE-01
 * ——视觉纵横比 = 列 ÷ (2 × 行)。
 */

/** 5 宽 × 7 高子像素字模。只收字标用得到的字母。 */
const GLYPHS_5X7 = {
  A: [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
  D: ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
  E: ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
  G: [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."],
  I: ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
  K: ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
  N: ["#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"],
  P: ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
  T: ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
  U: ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
  V: ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
} as const;

type Glyph = keyof typeof GLYPHS_5X7;

const GLYPH_HEIGHT = 7;
/** 字母之间 1 列。 */
const LETTER_GAP = 1;
/** 词之间 4 列。2 列时 KUNPENG / DEVKIT / AI 会糊成一块。 */
const WORD_GAP = 4;

/** 把一串词展开成子像素位图，每行是 `#` / `.` 组成的字符串。 */
function bitmapFor(words: readonly string[]): readonly string[] {
  return Array.from({ length: GLYPH_HEIGHT }, (_, row) =>
    words
      .map((word) =>
        [...word]
          .map((character) => GLYPHS_5X7[character as Glyph]?.[row] ?? ".....")
          .join(".".repeat(LETTER_GAP)),
      )
      .join(".".repeat(WORD_GAP)),
  );
}

/**
 * 子像素位图 → 半块终端行。
 *
 * 每个终端格取上下两个子像素：上下都亮 `█`，只上亮 `▀`，只下亮 `▄`，都不亮空格。
 * 奇数行位图的最后一格下半永远为空。
 */
export function toHalfBlockRows(bitmap: readonly string[]): readonly string[] {
  const rows: string[] = [];
  for (let top = 0; top < bitmap.length; top += 2) {
    const upper = bitmap[top] ?? "";
    const lower = bitmap[top + 1] ?? "";
    const width = Math.max(upper.length, lower.length);
    let line = "";
    for (let column = 0; column < width; column += 1) {
      const hasUpper = upper[column] === "#";
      const hasLower = lower[column] === "#";
      line += hasUpper && hasLower ? "█" : hasUpper ? "▀" : hasLower ? "▄" : " ";
    }
    rows.push(line.trimEnd());
  }
  return rows;
}

/** ASCII 降级：无 Unicode 时不画点阵，交由调用方退成纯文本。 */
export const LANDING_WORDMARK: readonly string[] = toHalfBlockRows(
  bitmapFor(["KUNPENG", "DEVKIT", "AI"]),
);

/** 字标占用的列数与终端行数，供布局盒子使用，避免写死。 */
export const LANDING_WORDMARK_WIDTH = LANDING_WORDMARK.reduce(
  (widest, line) => Math.max(widest, [...line].length),
  0,
);
export const LANDING_WORDMARK_HEIGHT = LANDING_WORDMARK.length;
