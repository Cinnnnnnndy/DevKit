"""Kunpeng DevKit AI — Textual launch screen prototype."""

from __future__ import annotations

from dataclasses import dataclass
from math import floor, pi, sin, sqrt
from random import Random
from time import monotonic

from rich.text import Text
from textual.app import App, ComposeResult
from textual import events
from textual.containers import Grid, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Button, Input, Static, Tab, Tabs, TabbedContent, TabPane


KUNPENG_MARK_ROWS = (
    (("plain", "                               "), ("red", "▄▄")),
    (("plain", "                          "), ("red", "▄▄▄█▀▀"), ("pale", "▄")),
    (("plain", "                     "), ("red", "▄▄▄███▀"), ("plain", " "), ("pale", "▄█▀")),
    (("plain", "               "), ("red", "▄▄▄█████▀▀"), ("pale", "▄▄██▀")),
    (("plain", "          "), ("red", "▄▄▄███████▀"), ("plain", " "), ("pale", "▄████▀")),
    (("plain", "       "), ("red", "▄████████▀▀"), ("pale", "▄▄█████▀")),
    (("plain", " "), ("red", "▄▄▄▄▄▄██████▀▀"), ("pale", "▄▄██████▀")),
    (("plain", "   "), ("red", "▀▀████▀▀"), ("pale", "▄▄████████▀")),
    (("plain", "         "), ("pale", "▄█████████▀")),
    (("plain", "           "), ("pale", "▀▀███████▄")),
    (("plain", "               "), ("pale", "▀▀████▄")),
    (("plain", "                   "), ("pale", "▀▀██▄")),
    (("plain", "                       "), ("pale", "▀▀")),
)


def make_kunpeng_mark() -> Text:
    """Build the exact two-tone character mark from the reference demo."""
    mark = Text(no_wrap=True)
    colors = {"plain": None, "red": "#ed1c24", "pale": "#c9c9c9"}
    for row_index, row in enumerate(KUNPENG_MARK_ROWS):
        for tone, glyphs in row:
            mark.append(glyphs, style=colors[tone])
        if row_index < len(KUNPENG_MARK_ROWS) - 1:
            mark.append("\n")
    return mark


KUNPENG_MARK = make_kunpeng_mark()

FIVE_HIGH = {
    "A": (".###.", "#...#", "#####", "#...#", "#...#"),
    "D": ("####.", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "####.", "#....", "#####"),
    "G": (".####", "#....", "#..##", "#...#", ".####"),
    "I": ("#####", "..#..", "..#..", "..#..", "#####"),
    "K": ("#...#", "#..#.", "###..", "#..#.", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#"),
    "P": ("####.", "#...#", "####.", "#....", "#...."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", ".#.#.", "..#.."),
}


def block_word(word: str, stretch: int = 1) -> list[str]:
    """Render the five-row character font; stretch scales each glyph's width."""
    return [
        " ".join(
            "".join(cell * stretch for cell in FIVE_HIGH[letter][row])
            for letter in word
        )
        .replace("#", "█")
        .replace(".", " ")
        for row in range(5)
    ]


def make_wordmark() -> str:
    """Two-line wordmark: KUNPENG over DEVKIT AI, left-aligned, glyphs 2x wide."""
    kunpeng = block_word("KUNPENG", stretch=2)
    devkit = block_word("DEVKIT", stretch=2)
    ai = block_word("AI", stretch=2)
    lines = [kunpeng[row] for row in range(5)]
    lines.append("")  # blank row separating the two words
    lines.extend(f"{devkit[row]}   {ai[row]}" for row in range(5))
    return "\n".join(lines)


WORDMARK = make_wordmark()


@dataclass
class Spark:
    age: int = 0
    ttl: int = 1
    index: int = -1
    big: bool = False
    color: str = ""


class HalftoneField(Static):
    """Static organic halftone with small, fast sparks around its outer field."""

    phase = reactive(0)

    BASE_GLYPHS = (" ", " ", " ", " ", " ", " ", "·", "·", "·", "-", "+", "+")
    SPARK_GLYPHS = (" ", "·", "·", "-", "+", "*", "#")
    SPARK_COLORS = ("#01a7ba", "#5f3cff", "#ab43ab")

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self._field_size = (0, 0)
        self._density: list[float] = []
        self._eligible: list[int] = []
        self._sparks: list[Spark] = []
        self._rng = Random(2600)
        self._animation_timer = None

    def on_mount(self) -> None:
        self._animation_timer = self.set_interval(1 / 24, self.advance)

    def pause_animation(self) -> None:
        if self._animation_timer is not None:
            self._animation_timer.pause()

    def resume_animation(self) -> None:
        if self._animation_timer is not None:
            self._animation_timer.resume()

    def advance(self) -> None:
        self.phase += 1
        self.refresh()

    @staticmethod
    def _hash(x: int, y: int) -> float:
        value = (x * 374761393 + y * 668265263) & 0xFFFFFFFF
        value = ((value ^ (value >> 13)) * 1274126177) & 0xFFFFFFFF
        return ((value >> 8) & 65535) / 65535

    @classmethod
    def _noise(cls, x: int, y: int, scale: float) -> float:
        gx, gy = x / scale, y / scale
        x0, y0 = floor(gx), floor(gy)
        fx, fy = gx - x0, gy - y0
        u, v = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
        return (
            cls._hash(x0, y0) * (1 - u) * (1 - v)
            + cls._hash(x0 + 1, y0) * u * (1 - v)
            + cls._hash(x0, y0 + 1) * (1 - u) * v
            + cls._hash(x0 + 1, y0 + 1) * u * v
        )

    def _build_field(self, width: int, height: int) -> None:
        center_x, center_y = width * 0.5, height * 0.48
        # Textual widgets occupy terminal cells even with a transparent color.
        # Feather the field before it reaches the launch widget so the clear
        # center reads as part of the density map instead of a clipped rectangle.
        clear_half_width = min(66.0, width * 0.43)
        clear_half_height = min(15.5, height * 0.34)
        density: list[float] = []
        for row in range(height):
            for col in range(width):
                dx = (col - center_x) / max(1, width * 0.5)
                dy = (row - center_y) / max(1, height * 0.5)
                radius = sqrt(dx * dx * 1.02 + dy * dy * 0.96)
                noise = self._hash(col, row)
                organic = self._noise(col, row, 6.5) * 0.88
                organic += self._noise(col, row, 2.4) * 0.44 - 0.56
                value = (radius - 0.60) * 1.50 + organic * 0.58 + noise * 0.16
                outside_x = max(0.0, abs(col - center_x) - clear_half_width)
                outside_y = max(0.0, abs(row - center_y) - clear_half_height)
                distance_from_content = sqrt(outside_x * outside_x + (outside_y * 2) ** 2)
                feather = min(1.0, distance_from_content / 8.0)
                value *= feather
                density.append(max(0.0, min(0.999, value)))

        self._field_size = (width, height)
        self._density = density
        self._eligible = [index for index, value in enumerate(density) if value > 0.30]
        spark_count = max(12, round(len(self._eligible) * 0.008))
        self._sparks = [Spark() for _ in range(spark_count)] if self._eligible else []

    def render(self) -> Text:
        width = max(1, self.size.width)
        height = max(1, self.size.height)
        if self._field_size != (width, height):
            self._build_field(width, height)

        chars = [self.BASE_GLYPHS[min(11, int(value * 12))] for value in self._density]
        glow: dict[int, tuple[float, str]] = {}

        def light(index: int, strength: float, color: str) -> None:
            if 0 <= index < len(chars):
                current = glow.get(index)
                if current is None or strength > current[0]:
                    glow[index] = (strength, color)

        for spark in self._sparks:
            spark.age += 1
            if spark.age >= spark.ttl or spark.index < 0:
                spark.age = 0
                spark.ttl = self._rng.randint(7, 28)
                spark.index = self._rng.choice(self._eligible)
                spark.big = self._rng.random() < 0.34
                spark.color = self._rng.choice(self.SPARK_COLORS)
            strength = sin(pi * spark.age / spark.ttl)
            if strength <= 0.02:
                continue
            light(spark.index, strength, spark.color)
            if spark.big:
                light(spark.index - 1, strength * 0.52, spark.color)
                light(spark.index + 1, strength * 0.52, spark.color)
                light(spark.index - width, strength * 0.44, spark.color)
                light(spark.index + width, strength * 0.44, spark.color)

        for index, (strength, _color) in glow.items():
            value = strength * (0.80 + 0.28 * self._density[index])
            glyph_index = min(6, max(0, int((value - 0.14) / 0.46 * 7)))
            chars[index] = self.SPARK_GLYPHS[glyph_index]

        lines = ["".join(chars[row * width : (row + 1) * width]) for row in range(height)]
        result = Text("\n".join(lines), style="#26302f", no_wrap=True)
        for index, (_strength, color) in glow.items():
            row, col = divmod(index, width)
            offset = row * (width + 1) + col
            result.stylize(color, offset, offset + 1)
        return result


class Suggestion(Button):
    """A launch suggestion that fills the task input."""


@dataclass(frozen=True)
class ProfileEvent:
    sample: int
    label: str
    severity: str


@dataclass(frozen=True)
class OperatorMetric:
    name: str
    calls: int
    average_ms: float
    total_s: float
    memory_gb: float
    bound: str
    trend: tuple[int, ...]


@dataclass(frozen=True)
class FlameNode:
    name: str
    start: float
    percent: float
    depth: int
    self_ms: float


@dataclass(frozen=True)
class TraceLane:
    group: str
    name: str
    color: str
    segments: tuple[tuple[int, int, int], ...]
    peak: int


@dataclass(frozen=True)
class WorkerMetric:
    name: str
    cpu: int
    numa: int
    migrations: int
    run_queue_ms: float


@dataclass
class MockProfilerSession:
    """One coherent profiling capture shared by every chart tab."""

    timestamps: list[str]
    latency: list[float]
    throughput: list[float]
    cpu: list[float]
    cpu_user: list[float]
    cpu_system: list[float]
    cpu_iowait: list[float]
    remote_numa: list[float]
    core_utilization: list[list[int]]
    node_utilization: list[list[int]]
    events: list[ProfileEvent]
    operators: list[OperatorMetric]
    flame_nodes: list[FlameNode]
    trace_lanes: list[TraceLane]
    workers: list[WorkerMetric]
    cursor_index: int = 119
    cursor_locked: bool = False
    paused: bool = False
    selected_flame: int = 16
    selected_span: int = 15
    selected_operator: int = 0
    selected_worker: int = 27

    @classmethod
    def demo(cls) -> "MockProfilerSession":
        anchors = {
            "cpu": [48, 51, 49, 54, 57, 55, 59, 61, 58, 63, 65, 62, 66, 69, 73, 78, 82, 86, 84, 79, 76, 74, 72, 73],
            "remote": [4, 5, 4, 5, 6, 5, 5, 6, 5, 6, 7, 8, 9, 12, 16, 21, 23, 24, 22, 21, 20, 21, 21, 21],
            "latency": [126, 128, 124, 130, 132, 129, 134, 136, 131, 138, 141, 139, 146, 154, 166, 181, 193, 201, 197, 190, 187, 185, 184, 184],
            "throughput": [57, 58, 59, 57, 56, 58, 57, 55, 56, 54, 53, 54, 52, 50, 48, 45, 42, 40, 40, 41, 42, 42, 43, 43],
        }
        sample_count = 120

        def expand(values: list[int], wobble: float = 0.0) -> list[float]:
            expanded: list[float] = []
            for index in range(sample_count):
                position = index / (sample_count - 1) * (len(values) - 1)
                left = min(len(values) - 2, int(position))
                fraction = position - left
                value = values[left] * (1 - fraction) + values[left + 1] * fraction
                expanded.append(value + sin(index * 0.71) * wobble)
            return expanded

        timestamps = [f"14:{32 + (index * 3) // 60:02d}:{(index * 3) % 60:02d}" for index in range(sample_count)]
        cpu = expand(anchors["cpu"], 0.8)
        remote = expand(anchors["remote"], 0.25)
        latency = expand(anchors["latency"], 1.4)
        throughput = expand(anchors["throughput"], 0.35)
        core_rows: list[list[int]] = []
        node_rows: list[list[int]] = []
        for sample in range(sample_count):
            core_rows.append([
                max(18, min(98, int(cpu[sample] + ((core * 17 + sample * 7) % 29) - 14 + (18 if 34 <= core <= 38 and sample >= 72 else 0))))
                for core in range(64)
            ])
            node_rows.append([
                max(20, min(98, int(cpu[sample] + offset)))
                for offset in (-6, -13, 12 if sample >= 68 else 2, -18)
            ])
        return cls(
            timestamps=timestamps,
            latency=latency,
            throughput=throughput,
            cpu=cpu,
            cpu_user=[value * 0.73 for value in cpu],
            cpu_system=[value * 0.18 for value in cpu],
            cpu_iowait=[max(2, value * 0.09 + (remote[index] - 5) * 0.42) for index, value in enumerate(cpu)],
            remote_numa=remote,
            core_utilization=core_rows,
            node_utilization=node_rows,
            events=[
                ProfileEvent(57, "candidate-42 deployed", "info"),
                ProfileEvent(72, "worker-27 migrated N0 → N2", "warning"),
                ProfileEvent(78, "remote memory crossed 20%", "danger"),
                ProfileEvent(88, "P99 regression alert +37%", "danger"),
            ],
            operators=[
                OperatorMetric("attention_fwd", 1024, 18.2, 18.6, 2.1, "memory", (5, 6, 6, 7, 9, 12, 17, 18)),
                OperatorMetric("matmul_4096", 512, 12.4, 6.3, 1.4, "compute", (6, 6, 7, 7, 7, 8, 8, 8)),
                OperatorMetric("layernorm", 2048, 0.8, 1.6, 0.12, "memory", (3, 3, 3, 4, 4, 4, 5, 5)),
                OperatorMetric("softmax", 1024, 1.2, 1.2, 0.25, "compute", (2, 2, 3, 3, 4, 4, 4, 4)),
                OperatorMetric("kv_cache_update", 1024, 0.6, 0.6, 3.8, "memory", (2, 3, 3, 5, 7, 9, 11, 12)),
                OperatorMetric("load_qkv", 1024, 4.8, 4.9, 2.8, "memory", (4, 4, 5, 6, 8, 11, 14, 16)),
                OperatorMetric("rope_apply", 1024, 1.1, 1.1, 0.18, "compute", (2, 2, 2, 3, 3, 4, 4, 5)),
                OperatorMetric("flash_decode", 512, 6.7, 3.4, 1.1, "mixed", (4, 5, 5, 6, 6, 7, 8, 8)),
                OperatorMetric("rms_norm", 2048, 0.7, 1.4, 0.09, "memory", (3, 3, 4, 4, 5, 5, 5, 6)),
                OperatorMetric("gelu_fused", 1024, 1.3, 1.3, 0.21, "compute", (2, 3, 3, 3, 4, 4, 5, 5)),
                OperatorMetric("all_reduce", 256, 4.1, 1.0, 0.8, "network", (2, 2, 3, 4, 4, 5, 6, 7)),
                OperatorMetric("embedding", 128, 5.9, 0.8, 3.2, "memory", (5, 5, 5, 6, 6, 7, 7, 7)),
                OperatorMetric("topk", 512, 1.4, 0.7, 0.12, "compute", (2, 2, 3, 3, 3, 4, 4, 5)),
                OperatorMetric("sampling", 512, 1.1, 0.6, 0.06, "compute", (1, 2, 2, 2, 3, 3, 4, 4)),
                OperatorMetric("memcpy_async", 4096, 0.1, 0.5, 4.6, "memory", (3, 4, 4, 6, 7, 9, 10, 12)),
                OperatorMetric("logits_proj", 512, 0.9, 0.5, 0.7, "compute", (2, 2, 2, 3, 3, 3, 4, 4)),
            ],
            flame_nodes=[
                FlameNode("runtime.main", 0, 100, 0, 0.2),
                FlameNode("serve_loop", 1, 94, 1, 0.6), FlameNode("telemetry", 96, 3, 1, 0.3),
                FlameNode("batch_dispatch", 2, 84, 2, 1.4), FlameNode("idle_wait", 89, 6, 2, 0.2),
                FlameNode("inference.run", 4, 74, 3, 2.1), FlameNode("tokenize", 80, 5, 3, 0.9),
                FlameNode("response_flush", 89, 4, 3, 0.4),
                FlameNode("embedding", 5, 9, 4, 4.9), FlameNode("model.forward", 17, 58, 4, 3.2),
                FlameNode("sampling", 80, 4, 4, 0.8),
                FlameNode("decoder.layers", 18, 53, 5, 5.7), FlameNode("logits_proj", 72, 3, 5, 1.1),
                FlameNode("attention", 19, 28, 6, 8.4), FlameNode("mlp", 51, 14, 6, 6.1),
                FlameNode("rms_norm", 67, 4, 6, 1.7),
                FlameNode("attention_fwd", 20, 21, 7, 18.2), FlameNode("softmax", 43, 4, 7, 2.2),
                FlameNode("gelu_fused", 52, 7, 7, 2.7), FlameNode("matmul_4096", 61, 4, 7, 7.1),
                FlameNode("load_qkv", 21, 14, 8, 14.6), FlameNode("rope_apply", 37, 4, 8, 3.1),
                FlameNode("remote_page_read", 22, 10, 9, 12.8), FlameNode("memcpy_async", 33, 2, 9, 4.2),
                FlameNode("page_fault", 23, 5, 10, 7.9), FlameNode("numa_migrate", 29, 3, 10, 5.4),
            ],
            trace_lanes=_make_trace_lanes(),
            workers=[
                WorkerMetric(
                    f"worker-{worker:02d}",
                    36 if worker == 27 else (worker * 7 + 4) % 64,
                    2 if worker == 27 else ((worker * 7 + 4) % 64) // 16,
                    142 if worker == 27 else (worker * 13) % 34,
                    8.6 if worker == 27 else 0.8 + (worker % 7) * 0.4,
                )
                for worker in range(32)
            ],
        )


def _make_trace_lanes() -> list[TraceLane]:
    """Build a deterministic, instance-level 32-lane request trace."""
    lanes: list[TraceLane] = []
    definitions = (
        ("HOST", ["main", "scheduler"] + [f"worker-{index:02d}" for index in range(12)] + ["worker-18", "worker-27"], "#3c7cf6"),
        ("CPU/NUMA", [f"CPU {index:02d}" for index in (4, 11, 18, 25, 34, 36, 38, 45)] + ["NUMA migrate"], "#04d793"),
        ("NPU", [f"stream-{index}" for index in range(4)] + ["cube", "vector"], "#9b7bff"),
        ("MEMORY", ["HBM read", "HBM write", "DDR local", "DDR remote", "MTE DMA"], "#ffaa3b"),
    )
    for group, names, color in definitions:
        for lane_index, name in enumerate(names):
            seed = len(lanes) * 11 + 7
            segments = tuple(
                (
                    (seed + segment * 23) % 88,
                    4 + (seed + segment * 7) % 12,
                    min(99, 28 + (seed * 3 + segment * 19) % 72),
                )
                for segment in range(3 if group != "MEMORY" else 4)
            )
            if name in ("worker-27", "CPU 36", "DDR remote", "HBM read"):
                segments = segments + ((44, 31, 98),)
            lanes.append(TraceLane(group, name, color, segments, max(segment[2] for segment in segments)))
    return lanes


PROFILE = MockProfilerSession.demo()
SPARK_BLOCKS = "▁▂▃▄▅▆▇█"
HERO_DIGITS = {
    "0": ("█▀█", "█ █", "█▄█"), "1": (" ▄█", "  █", " ▄█"),
    "2": ("▀▀█", "█▀▀", "█▄▄"), "3": ("▀▀█", " ▀█", "▄▄█"),
    "4": ("█ █", "▀▀█", "  █"), "5": ("█▀▀", "▀▀█", "▄▄█"),
    "6": ("█▀▀", "█▀█", "█▄█"), "7": ("▀▀█", "  █", "  █"),
    "8": ("█▀█", "█▀█", "█▄█"), "9": ("█▀█", "▀▀█", "▄▄█"),
    ".": ("   ", "   ", " ▄ "),
}


def sparkline(values: list[float] | tuple[int, ...]) -> str:
    low, high = min(values), max(values)
    scale = max(1, high - low)
    return "".join(SPARK_BLOCKS[min(7, int((value - low) / scale * 7))] for value in values)


def hero_number(value: str) -> list[str]:
    return [" ".join(HERO_DIGITS[char][row] for char in value) for row in range(3)]


def braille_line(values: list[float], width: int, height: int, cursor_column: int) -> list[str]:
    """Render a compact 2×4-dot history line without per-cell Rich styling."""
    pixel_width, pixel_height = width * 2, height * 4
    low, high = min(values), max(values)
    scale = max(1.0, high - low)
    cells = [[0 for _ in range(width)] for _ in range(height)]
    dots = ((0x01, 0x02, 0x04, 0x40), (0x08, 0x10, 0x20, 0x80))
    previous: tuple[int, int] | None = None
    for pixel_x in range(pixel_width):
        index = round(pixel_x / max(1, pixel_width - 1) * (len(values) - 1))
        pixel_y = pixel_height - 1 - round((values[index] - low) / scale * (pixel_height - 1))
        points = [(pixel_x, pixel_y)]
        if previous is not None:
            _, previous_y = previous
            distance = max(1, abs(pixel_y - previous_y))
            points.extend((pixel_x, round(previous_y + (pixel_y - previous_y) * step / distance)) for step in range(distance))
        for point_x, point_y in points:
            cell_x, dot_x = divmod(point_x, 2)
            cell_y, dot_y = divmod(max(0, min(pixel_height - 1, point_y)), 4)
            cells[cell_y][cell_x] |= dots[dot_x][dot_y]
        previous = (pixel_x, pixel_y)
    lines = []
    for row in cells:
        chars = [chr(0x2800 + bits) if bits else " " for bits in row]
        if 0 <= cursor_column < width:
            chars[cursor_column] = "│"
        lines.append("".join(chars))
    return lines


def braille_area(values: list[float], width: int, height: int, cursor_column: int, *, invert: bool = False) -> list[str]:
    """Render a filled Braille area, optionally growing down from the top edge."""
    pixel_width, pixel_height = width * 2, height * 4
    low, high = min(values), max(values)
    scale = max(1.0, high - low)
    cells = [[0 for _ in range(width)] for _ in range(height)]
    dots = ((0x01, 0x02, 0x04, 0x40), (0x08, 0x10, 0x20, 0x80))
    for pixel_x in range(pixel_width):
        index = round(pixel_x / max(1, pixel_width - 1) * (len(values) - 1))
        extent = round((values[index] - low) / scale * (pixel_height - 1))
        pixels = range(0, extent + 1) if invert else range(pixel_height - 1 - extent, pixel_height)
        for pixel_y in pixels:
            cell_x, dot_x = divmod(pixel_x, 2)
            cell_y, dot_y = divmod(pixel_y, 4)
            cells[cell_y][cell_x] |= dots[dot_x][dot_y]
    lines: list[str] = []
    for row in cells:
        chars = [chr(0x2800 + bits) if bits else " " for bits in row]
        if 0 <= cursor_column < width:
            chars[cursor_column] = "│"
        lines.append("".join(chars))
    return lines


class SessionWidget(Static):
    """Base widget bound to the shared demo capture."""

    can_focus = True

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self._last_hover_at = 0.0

    @property
    def session(self) -> MockProfilerSession:
        return PROFILE

    def set_cursor_from_x(self, x: int) -> bool:
        width = max(1, self.size.width - 4)
        index = round(max(0, min(width - 1, x - 2)) / max(1, width - 1) * (len(self.session.timestamps) - 1))
        if index == self.session.cursor_index:
            return False
        workspace = self.app.query_one("#chart-workspace", ChartWorkspace)
        workspace.set_cursor(index)
        return True

    def on_mouse_move(self, event: events.MouseMove) -> None:
        now = monotonic()
        if not self.session.cursor_locked and now - self._last_hover_at >= 1 / 30:
            self._last_hover_at = now
            self.set_cursor_from_x(event.x)

    def on_click(self, event: events.Click) -> None:
        self.set_cursor_from_x(event.x)
        self.session.cursor_locked = not self.session.cursor_locked
        self.app.query_one("#chart-workspace", ChartWorkspace).refresh_session()


class MetricCard(Static):
    def __init__(self, label: str, value: str, unit: str, detail: str, tone: str = "#3d98ff", accent: str = "info") -> None:
        content = Text()
        for row, line in enumerate(hero_number(value)):
            content.append(line, style=f"bold {tone}")
            if row == 1:
                content.append(f"  {unit}", style=f"bold {tone}")
            content.append("\n")
        content.append(label, style="bold #e8e8e8")
        content.append(f"  {detail}", style="#777777")
        super().__init__(content, classes=f"metric-card metric-{accent}")


class TimeSeriesChart(SessionWidget):
    """Terminal-native line chart with a shared vertical time cursor."""

    def __init__(self, series: tuple[tuple[str, list[float], str], ...], *, title: str, classes: str = "") -> None:
        super().__init__(classes=f"time-chart {classes}".strip())
        self.series = series
        self.border_title = title

    def render(self) -> Text:
        width = max(24, self.size.width - 4)
        height = max(5, self.size.height - 3)
        sample_count = len(self.session.timestamps)
        cursor_x = round(self.session.cursor_index / (sample_count - 1) * (width - 1))
        output = Text()
        index = self.session.cursor_index
        track_height = max(1, min(3, (height - 2) // max(1, len(self.series)) - 1))
        for label, values, color in self.series:
            output.append(f"{label:<11}", style="#777777")
            output.append(f"{values[index]:>6.1f}", style=f"bold {color}")
            output.append(f"   min {min(values):.0f}  max {max(values):.0f}\n", style="#555555")
            for line in braille_line(values, width, track_height, cursor_x):
                output.append(line + "\n", style=color)
        lock = "LOCKED" if self.session.cursor_locked else "HOVER"
        output.append(f"{self.session.timestamps[0]}  ─────  {self.session.timestamps[index]} {lock}  ─────  {self.session.timestamps[-1]}", style="#777777")
        return output


class CoreHeatmap(SessionWidget):
    def __init__(self, *, compact: bool = False) -> None:
        super().__init__(classes="core-heatmap")
        self.compact = compact
        self.border_title = "64-CORE SNAPSHOT"

    def render(self) -> Text:
        values = self.session.core_utilization[self.session.cursor_index]
        colors = ("#4a2d17", "#70411d", "#9b5422", "#d9862c", "#ffc777")
        result = Text()
        result.append("▁0  ▃20  ▅40  ▇60  █80–100\n\n" if self.compact else "UTIL  ▁ 0–20  ▃ 20–40  ▅ 40–60  ▇ 60–80  █ 80–100\n\n", style="#777777")
        nodes = self.session.node_utilization[self.session.cursor_index]
        for row in range(4):
            result.append(f"{row * 16:02d}–{row * 16 + 15:02d}  ", style="#777777")
            for col in range(16):
                value = values[row * 16 + col]
                result.append(SPARK_BLOCKS[min(7, value // 13)], style=colors[min(4, value // 20)])
                if not self.compact:
                    result.append(" ")
            gauge = round(nodes[row] / 100 * (6 if self.compact else 12))
            gauge_width = 6 if self.compact else 12
            result.append(f"   N{row} ", style="#777777")
            result.append("█" * gauge, style="#d9862c")
            result.append("░" * (gauge_width - gauge), style="#4a2d17")
            result.append(f" {nodes[row]:02d}%\n", style="#a4a4a4")
        hot = max(range(64), key=values.__getitem__)
        result.append(f"\n▚▚▚ core {hot:02d}  {values[hot]}% · cross-NUMA hotspot", style="bold #ff4b7b")
        return result


class SegmentedGauge(SessionWidget):
    """T1 multi-segment memory gauge using the system's accum-orange ramp."""

    def __init__(self, *, compact: bool = False) -> None:
        super().__init__(classes="resource-gauge")
        self.compact = compact
        self.border_title = "MEMORY PRESSURE · 64 GiB"

    def render(self) -> Text:
        remote = self.session.remote_numa[self.session.cursor_index]
        used, cached, kv = 22.0 + remote * 0.22, 12.0, 4.0 + remote * 0.08
        free = max(0.0, 64.0 - used - cached - kv)
        values = (used, cached, kv, free)
        colors = ("#ffc777", "#d9862c", "#9b5422", "#343434")
        width = max(22, self.size.width - 6)
        counts = [round(value / 64 * width) for value in values]
        counts[-1] += width - sum(counts)
        result = Text()
        for count, color in zip(counts, colors):
            result.append("█" * max(0, count), style=color)
        result.append(f"  {64 - free:4.1f}/64G\n", style="bold #e8e8e8")
        result.append(f"used {used:4.1f}  cached {cached:4.1f}  kv {kv:3.1f}  free {free:4.1f}", style="#a4a4a4")
        if not self.compact:
            result.append("\n\nREMOTE PAGE PRESSURE  ", style="#777777")
            level = min(20, round(remote / 30 * 20))
            result.append("█" * level, style="#ff4b7b" if remote >= 20 else "#d9862c")
            result.append("░" * (20 - level), style="#4a2d17")
            result.append(f"  {remote:4.1f}%", style="bold #ffaa3b")
        return result


class BidirectionalAreaChart(SessionWidget):
    """T2 paired area chart for local reads versus remote DDR traffic."""

    def __init__(self, *, compact: bool = False) -> None:
        super().__init__(classes="bidirectional-area")
        self.compact = compact
        self.border_title = "DDR BANDWIDTH · LOCAL ↑ / REMOTE ↓"

    def render(self) -> Text:
        local = [max(20.0, cpu * 1.55 - remote * 0.8) for cpu, remote in zip(self.session.cpu, self.session.remote_numa)]
        remote = [value * 2.7 for value in self.session.remote_numa]
        width = max(24, self.size.width - (8 if self.compact else 12))
        height = 1 if self.compact else max(2, min(4, (self.size.height - 5) // 2))
        cursor_x = round(self.session.cursor_index / (len(local) - 1) * (width - 1))
        result = Text()
        result.append(f"LOCAL  {local[self.session.cursor_index]:5.1f} GB/s\n", style="bold #3d98ff")
        for line in braille_area(local, width, height, cursor_x):
            result.append(line + "\n", style="#3c7cf6")
        for line in braille_area(remote, width, height, cursor_x, invert=True):
            result.append(line + "\n", style="#ffaa3b")
        result.append(f"REMOTE {remote[self.session.cursor_index]:5.1f} GB/s  · {self.session.timestamps[self.session.cursor_index]}", style="bold #ffaa3b")
        return result


class BottleneckList(Static):
    def __init__(self) -> None:
        super().__init__(
            "[#ff4b7b]01[/] attention_fwd    [bold]18.6s[/]  [#ff4b7b]MEM[/]\n"
            "[#ffaa3b]02[/] matmul_4096       [bold]6.3s[/]  COMPUTE\n"
            "[#ffaa3b]03[/] kv_cache_update  [bold]3.8G[/]  REMOTE\n\n"
            "[bold #ff4b7b]AI[/] pin worker-27 → N0\n"
            "[#a4a4a4]P99 recovery 24–31%[/]",
            classes="overview-panel",
        )
        self.border_title = "BOTTLENECKS"


class OperatorRace(SessionWidget):
    """A time-linked race showing which kernel dominates the selected window."""

    def __init__(self, *, compact: bool = False) -> None:
        super().__init__(classes="operator-race")
        self.compact = compact
        self.border_title = "HOT KERNEL RACE · WINDOW SHARE"

    def render(self) -> Text:
        progress = self.session.cursor_index / max(1, len(self.session.timestamps) - 1)
        remote = self.session.remote_numa[self.session.cursor_index]
        scores = {
            "attention_fwd": 24 + progress * 22 + remote * 0.55,
            "matmul_4096": 37 - progress * 8,
            "kv_cache_update": 12 + remote * 0.75,
            "layernorm": 18 - progress * 3,
        }
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        width = max(10, min(24, self.size.width - 24))
        maximum = max(scores.values())
        colors = ("#ff4b7b", "#ffaa3b", "#3d98ff", "#777777")
        result = Text()
        for rank, ((name, value), color) in enumerate(zip(ranked, colors), 1):
            bar = max(1, round(value / maximum * width))
            result.append(f"{rank:02d} {name:<16} ", style="#a4a4a4")
            result.append("█" * bar, style=color)
            result.append(f" {value:4.1f}%\n", style=f"bold {color}")
            if self.compact and rank == 3:
                break
        result.append(f"{self.session.timestamps[self.session.cursor_index]} · attention overtook matmul after migration", style="#777777")
        return result


class DiagnosisPanel(SessionWidget):
    def __init__(self) -> None:
        super().__init__(classes="overview-panel diagnosis-panel")
        self.border_title = "AI DIAGNOSIS · 87% CONFIDENCE"

    def render(self) -> Text:
        index = self.session.cursor_index
        result = Text("▚▚▚  ROOT CAUSE\n", style="bold #ff4b7b")
        result.append("worker-27 crossed N0 → N2\n", style="bold #e8e8e8")
        result.append(f"remote memory  {self.session.remote_numa[index]:4.1f}%  ", style="#a4a4a4")
        result.append(f"iowait {self.session.cpu_iowait[index]:4.1f}%\n\n", style="#ffaa3b")
        result.append("RECOMMENDED ACTION\n", style="bold #3d98ff")
        result.append("pin worker-27 to NUMA 0\n", style="#e8e8e8")
        result.append("P99 recovery  24–31%  [Enter]", style="#777777")
        return result


class IncidentList(SessionWidget):
    def __init__(self) -> None:
        super().__init__(classes="overview-panel")
        self.border_title = "INCIDENT TIMELINE"

    def render(self) -> Text:
        result = Text()
        for incident in self.session.events:
            selected = incident.sample <= self.session.cursor_index
            color = "#ff4b7b" if incident.severity == "danger" else "#ffaa3b" if incident.severity == "warning" else "#3d98ff"
            result.append("● " if selected else "○ ", style=color if selected else "#555555")
            result.append(self.session.timestamps[incident.sample] + "  ", style="#777777")
            label = incident.label.replace("worker-27 migrated N0 → N2", "worker-27  N0 → N2")
            label = label.replace("remote memory crossed 20%", "remote memory  >20%")
            label = label.replace("P99 regression alert +37%", "P99 alert  +37%")
            result.append(label, style="#f4f4f4" if selected else "#777777")
            result.append("\n")
        result.append("\nClick chart to lock time · ← → inspect", style="#777777")
        return result


class OverviewPane(Vertical):
    def compose(self) -> ComposeResult:
        with Horizontal(id="metric-strip"):
            yield MetricCard("P99 LATENCY", "184", "ms", "▲ 37% regression", "#009aff", "blue")
            yield MetricCard("THROUGHPUT", "42.8", "r/s", "▼ 25% baseline", "#01a7ba", "cyan")
            yield MetricCard("CPU TOTAL", "73", "%", "64C · 54°C", "#5f3cff", "violet")
            yield MetricCard("REMOTE NUMA", "21", "%", "baseline 5%", "#ab43ab", "magenta")
        with Grid(id="overview-main"):
            yield TimeSeriesChart(
                (
                    ("P99 ms", PROFILE.latency, "#ff4b7b"),
                    ("req/s", PROFILE.throughput, "#3c7cf6"),
                    ("CPU %", PROFILE.cpu, "#04d793"),
                    ("remote %", PROFILE.remote_numa, "#ffaa3b"),
                ),
                title="REGRESSION WINDOW · candidate-42",
                classes="overview-trend",
            )
            yield CoreHeatmap(compact=True)
            yield SegmentedGauge(compact=True)
            yield BidirectionalAreaChart(compact=True)
            yield OperatorRace(compact=True)


class DetailPanel(Static):
    def __init__(self, content: str, title: str, classes: str = "") -> None:
        super().__init__(content, classes=f"detail-panel {classes}".strip())
        self.border_title = title


class WorkerTable(SessionWidget):
    def __init__(self, *, numa_mode: bool = False) -> None:
        super().__init__(classes="worker-table")
        self.numa_mode = numa_mode
        self.border_title = "THREAD → MEMORY AFFINITY" if numa_mode else "RUNNABLE WORKERS · 32 THREADS"

    def render(self) -> Text:
        workers = self.session.workers
        selected = self.session.selected_worker
        visible_rows = max(5, self.size.height - 5)
        start = max(0, min(len(workers) - visible_rows, selected - visible_rows // 2))
        result = Text("THREAD      CPU NODE  MIG   RUNQ STATE\n", style="bold #777777")
        for index in range(start, min(len(workers), start + visible_rows)):
            worker = workers[index]
            anomalous = index == 27
            state = "REMOTE" if anomalous else "local"
            line = f"{worker.name:<11}{worker.cpu:>3}  N{worker.numa}  {worker.migrations:>3}  {worker.run_queue_ms:>4.1f} {state}"
            style = "bold #ff4b7b on #18293c" if index == selected else "#ffaa3b" if anomalous else "#a4a4a4"
            result.append(line + "\n", style=style)
        result.append(f"\n{start + 1:02d}–{min(len(workers), start + visible_rows):02d} / {len(workers)}  ↑↓ select  · worker-27 owns remote DDR wait", style="#777777")
        return result

    def on_key(self, event: events.Key) -> None:
        if event.key not in ("up", "down"):
            return
        delta = -1 if event.key == "up" else 1
        self.session.selected_worker = (self.session.selected_worker + delta) % len(self.session.workers)
        self.refresh()
        event.stop()


class CPUPage(Grid):
    def compose(self) -> ComposeResult:
        yield TimeSeriesChart(
            (("total %", PROFILE.cpu, "#3c7cf6"), ("iowait %", PROFILE.cpu_iowait, "#ffaa3b")),
            title="CPU HISTORY · migration/candidate-42",
            classes="wide-chart",
        )
        yield CoreHeatmap()
        yield WorkerTable()


class NUMAPage(Grid):
    def compose(self) -> ComposeResult:
        yield BidirectionalAreaChart()
        yield SegmentedGauge()
        yield DetailPanel(
            "      N0   N1   N2   N3\n"
            "N0   [bold]86[/]    3   [#ff4b7b]21[/]    2\n"
            "N1    4   [bold]91[/]    3    2\n"
            "N2   [#ff4b7b]18[/]    2   [bold]77[/]    3\n"
            "N3    2    3    4   [bold]91[/]\n\n"
            "[#777777]% memory requests by source → target[/]",
            "NUMA ACCESS MATRIX",
        )
        yield WorkerTable(numa_mode=True)


class FlameGraph(SessionWidget):
    def __init__(self) -> None:
        super().__init__(classes="full-chart flame-graph")
        self.border_title = "FLAME GRAPH · slow requests · 48,192 samples"

    def render(self) -> Text:
        result = Text("Filtered window  14:34:36–14:36:24   request latency >180ms   width = samples\n\n", style="#777777")
        colors = ("#603117", "#70411d", "#8a431c", "#b85620", "#e26f25", "#ff9638")
        width = max(72, self.size.width - 8)
        frames = self.session.flame_nodes
        max_depth = max(frame.depth for frame in frames)
        for depth in range(max_depth, -1, -1):
            depth_frames = [(index, frame) for index, frame in enumerate(frames) if frame.depth == depth]
            thicknesses = {
                index: 3 if frame.self_ms >= 12 else 2 if frame.self_ms >= 4 else 1
                for index, frame in depth_frames
            }
            band_height = max(thicknesses.values(), default=1)
            for band_row in range(band_height):
                row = Text(" " * width)
                for index, frame in depth_frames:
                    thickness = thicknesses[index]
                    if band_row < band_height - thickness:
                        continue
                    left = min(width - 1, round(frame.start / 100 * width))
                    right = min(width, max(left + 1, round((frame.start + frame.percent) / 100 * width)))
                    bar_width = right - left
                    label = f" {frame.name} {frame.percent:.0f}% " if band_row == band_height - 1 else ""
                    if bar_width < len(label):
                        label = f" {frame.name} "[:bar_width]
                    label = label.ljust(bar_width)
                    row = row[:left] + Text(
                        label,
                        style=(
                            "bold #f4f4f4 on #18293c"
                            if index == self.session.selected_flame
                            else f"bold #101010 on {colors[(depth + index) % len(colors)]}"
                        ),
                    ) + row[right:]
                result.append_text(row)
                result.append("\n")
        result.append("0% ├──────────────────────── samples / stack depth ────────────────────────┤ 100%\n", style="#555555")
        selected = frames[self.session.selected_flame]
        result.append("\nSELECTED  ", style="bold #3d98ff")
        result.append(f"{selected.name}  self {selected.self_ms:.1f}ms · {selected.percent:.1f}% samples · memory-bound\n", style="#f4f4f4")
        result.append(f"{len(frames)} frames · {max_depth + 1} stack levels · ↑↓ select · Enter inspect · linked to Operators + Trace", style="#777777")
        return result

    def on_key(self, event: events.Key) -> None:
        if event.key not in ("up", "down"):
            return
        delta = -1 if event.key == "up" else 1
        self.session.selected_flame = max(0, min(len(self.session.flame_nodes) - 1, self.session.selected_flame + delta))
        self.refresh()
        event.stop()


class TraceLanes(SessionWidget):
    def __init__(self) -> None:
        super().__init__(classes="full-chart trace-lanes")
        self.border_title = "REQUEST TRACE · req_8f21 · P99 201ms"

    def render(self) -> Text:
        lanes = self.session.trace_lanes
        visible_rows = max(12, self.size.height - 8)
        selected = max(0, min(len(lanes) - 1, self.session.selected_span))
        start = max(0, min(len(lanes) - visible_rows, selected - visible_rows // 2))
        plot_width = max(60, self.size.width - 34)
        cursor_x = round(self.session.cursor_index / (len(self.session.timestamps) - 1) * (plot_width - 1))
        result = Text("GROUP / INSTANCE      0ms          50ms         100ms         150ms         200ms\n", style="#777777")
        previous_group = ""
        density_chars = "░▒▓█"
        for index in range(start, min(len(lanes), start + visible_rows)):
            lane = lanes[index]
            group = lane.group if lane.group != previous_group else ""
            previous_group = lane.group
            result.append(f"{group:<9} {lane.name:<10} ", style="bold #777777" if group else "#a4a4a4")
            offset = len(result)
            row = [" " for _ in range(plot_width)]
            strengths = [0 for _ in range(plot_width)]
            for segment_start, duration, intensity in lane.segments:
                left = round(segment_start / 120 * (plot_width - 1))
                right = min(plot_width, left + max(1, round(duration / 120 * plot_width)))
                char = density_chars[min(3, intensity // 25)]
                for x in range(left, right):
                    row[x], strengths[x] = char, intensity
            row[cursor_x] = "│"
            result.append("".join(row), style=(f"bold {lane.color} on #18293c" if index == selected else lane.color))
            result.stylize("bold #f4f4f4", offset + cursor_x, offset + cursor_x + 1)
            result.append(f" {lane.peak:02d}%\n", style="#777777")
        lane = lanes[selected]
        result.append(f"\n{start + 1:02d}–{min(len(lanes), start + visible_rows):02d}/{len(lanes)} LANES  SELECTED {lane.group}/{lane.name} · {lane.peak}% peak · ↑↓ scroll/select", style="bold #3d98ff")
        return result

    def on_key(self, event: events.Key) -> None:
        if event.key not in ("up", "down"):
            return
        delta = -1 if event.key == "up" else 1
        self.session.selected_span = (self.session.selected_span + delta) % len(self.session.trace_lanes)
        self.refresh()
        event.stop()


class OperatorTable(SessionWidget):
    def __init__(self) -> None:
        super().__init__(classes="full-chart operator-table")
        self.border_title = "OPERATOR RANKING · sorted by total ↓"

    def render(self) -> Text:
        result = Text("NAME                    CALLS       AVG       TOTAL    MEMORY    BOUND       LAST 8\n", style="bold #777777")
        visible_rows = max(8, self.size.height - 7)
        selected = self.session.selected_operator
        start = max(0, min(len(self.session.operators) - visible_rows, selected - visible_rows // 2))
        for index in range(start, min(len(self.session.operators), start + visible_rows)):
            metric = self.session.operators[index]
            line = f"{metric.name:22}{metric.calls:>7,}   {metric.average_ms:>6.1f}ms   {metric.total_s:>6.1f}s   {metric.memory_gb:>5.2f}G   {metric.bound:9}  {sparkline(metric.trend)}"
            style = "bold #3d98ff on #18293c" if index == self.session.selected_operator else "#f4f4f4"
            result.append(line + "\n", style=style)
        metric = self.session.operators[self.session.selected_operator]
        result.append("\nSELECTED  ", style="bold #3d98ff")
        result.append(f"{metric.name} → Flame: attention/load_qkv · Trace: req_8f21 · source: kernels/attention.py:184\n")
        result.append(f"{start + 1:02d}–{min(len(self.session.operators), start + visible_rows):02d}/{len(self.session.operators)}  ↑ ↓ select · Enter inspect · S sort · / filter", style="#777777")
        return result

    def on_key(self, event: events.Key) -> None:
        if event.key not in ("up", "down"):
            return
        delta = -1 if event.key == "up" else 1
        self.session.selected_operator = (self.session.selected_operator + delta) % len(self.session.operators)
        self.refresh()
        event.stop()


class ChartWorkspace(Vertical):
    """Tabbed developer chart workspace opened with /chart."""

    def compose(self) -> ComposeResult:
        with Horizontal(id="workspace-header"):
            yield Static("DEVKIT AI", id="workspace-brand")
            yield Static("CHART WORKSPACE", id="workspace-title")
            yield Static("LIVE  •  kunpeng920  •  2s", id="workspace-status")

        with TabbedContent(initial="overview", id="chart-tabs"):
            with TabPane("Overview", id="overview"):
                yield OverviewPane(id="overview-pane")
            with TabPane("CPU", id="cpu"):
                yield CPUPage(id="cpu-page", classes="chart-page")
            with TabPane("NUMA", id="numa"):
                yield NUMAPage(id="numa-page", classes="chart-page")
            with TabPane("Flame", id="flame"):
                yield FlameGraph()
            with TabPane("Trace", id="trace"):
                yield TraceLanes()
            with TabPane("Operators", id="operators"):
                yield OperatorTable()

        with Horizontal(id="workspace-footer"):
            yield Static("← → cursor / tabs    click lock    Space pause    R latest    Enter inspect", id="workspace-help")
            yield Static("Esc back to Launch", id="workspace-back")

    def on_mount(self) -> None:
        tabs = list(self.query_one("#chart-tabs", TabbedContent).query(Tab))
        for tab, tone in zip(tabs, ("blue", "cyan", "violet", "magenta", "cyan", "violet")):
            tab.add_class(f"tab-{tone}")

    def set_cursor(self, index: int) -> None:
        PROFILE.cursor_index = max(0, min(len(PROFILE.timestamps) - 1, index))
        self.refresh_session()

    def refresh_session(self) -> None:
        active = self.query_one("#chart-tabs", TabbedContent).active or "overview"
        for widget in self.query_one(f"#{active}", TabPane).query(SessionWidget):
            widget.refresh()

    def on_key(self, event: events.Key) -> None:
        if event.key in ("left", "right") and not isinstance(self.app.focused, Tabs):
            PROFILE.cursor_locked = True
            self.set_cursor(PROFILE.cursor_index + (-1 if event.key == "left" else 1))
            event.stop()
        elif event.key == "space":
            PROFILE.paused = not PROFILE.paused
            self.app.query_one("#workspace-status", Static).update(
                "PAUSED  •  kunpeng920" if PROFILE.paused else "LIVE  •  kunpeng920  •  2s"
            )
            event.stop()
        elif event.key.lower() == "r":
            PROFILE.cursor_locked = False
            self.set_cursor(len(PROFILE.timestamps) - 1)
            event.stop()


class LaunchScreen(Vertical):
    def compose(self) -> ComposeResult:
        with Horizontal(id="identity"):
            yield Static(KUNPENG_MARK, id="brand-mark")
            yield Static(WORDMARK, id="wordmark", markup=False)

        with Horizontal(id="badges"):
            yield Static("AI TERMINAL", classes="badge")
            yield Static("NATIVE TUI", classes="badge")
            yield Static("v26.0", classes="badge")
            yield Static("KUNPENG ARM64", classes="badge")

        with Horizontal(classes="content-row"):
            yield Static(
                "[dim][ 0.004][/dim] [bold #04d793]ok[/]   runtime          "
                "[#a4a4a4]本地已就绪，无需连接服务器[/]\n"
                "[dim][ 0.011][/dim] [bold #04d793]ok[/]   toolchain        "
                "[#a4a4a4]交叉编译 x86_64 → Kunpeng ARM64[/]\n"
                "[dim][ 0.019][/dim] [bold #04d793]ok[/]   mcp tools        "
                "[#a4a4a4]2/4 已装载  cpp_migrator · knowledge_base[/]\n"
                "[dim][ 0.024][/dim] [bold #ffaa3b]warn[/] capabilities     "
                "[#a4a4a4]3 项能力未安装[/]  [dim][Enter] 查看[/]\n"
                "[dim][ 0.031][/dim] [bold #04d793]ok[/]   session          "
                "[#a4a4a4]恢复会话 [#7c8db8]migrate nginx[/] · "
                "3 天前 · 82% · [#ffaa3b]2 项待确认[/][/]",
                id="boot-log",
            )

        with Horizontal(classes="content-row"):
            with Horizontal(id="prompt-box"):
                yield Static("❯", id="prompt")
                yield Input(
                    placeholder="想做什么？直接说 —— 例如「把 ./nginx 迁到鲲鹏」",
                    id="task-input",
                )
                yield Static("Ctrl+P  命令面板", id="command-hint")

        with Horizontal(classes="content-row"):
            with Vertical(id="suggestions"):
                yield Static("建 议", id="suggestion-label")
                with Horizontal(id="suggestion-buttons"):
                    yield Suggestion("安装迁移能力包", classes="suggestion")
                    yield Suggestion("扫描当前工程", classes="suggestion")
                    yield Suggestion("继续上次任务", classes="suggestion")

        with Horizontal(classes="content-row"):
            yield Static("", id="launch-feedback")

    def on_mount(self) -> None:
        self.query_one("#task-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if not event.button.has_class("suggestion"):
            return
        task_input = self.query_one("#task-input", Input)
        task_input.value = str(event.button.label)
        task_input.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        value = event.value.strip()
        if not value:
            self.app.notify("请先描述你想完成的任务", severity="warning")
            return
        if value.lower() == "/chart":
            self.app.open_chart_workspace()
            return
        self.query_one("#launch-feedback", Static).update(
            f"[bold #3d98ff]READY[/]  已接收任务：{value}"
        )
        self.app.notify("Launch 页面已完成任务接收；工作台流程待接入")


class DevKitAI(App[None]):
    CSS_PATH = "devkitai.tcss"
    TITLE = "Kunpeng DevKit AI"
    SUB_TITLE = "Native TUI"
    COMMAND_PALETTE_BINDING = "ctrl+p"

    BINDINGS = [
        ("ctrl+q", "quit", "退出"),
        ("escape", "clear_input", "清空"),
    ]

    def compose(self) -> ComposeResult:
        yield HalftoneField(id="halftone")
        yield LaunchScreen(id="launch")
        yield ChartWorkspace(id="chart-workspace", classes="hidden")

    def open_chart_workspace(self) -> None:
        halftone = self.query_one("#halftone", HalftoneField)
        halftone.pause_animation()
        halftone.add_class("hidden")
        self.query_one("#launch").add_class("hidden")
        workspace = self.query_one("#chart-workspace", ChartWorkspace)
        workspace.remove_class("hidden")
        self.query_one("#chart-tabs", TabbedContent).query_one(Tabs).focus()

    def close_chart_workspace(self) -> None:
        self.query_one("#chart-workspace").add_class("hidden")
        halftone = self.query_one("#halftone", HalftoneField)
        halftone.remove_class("hidden")
        halftone.resume_animation()
        self.query_one("#launch").remove_class("hidden")
        task_input = self.query_one("#task-input", Input)
        task_input.value = ""
        task_input.focus()

    def action_clear_input(self) -> None:
        if not self.query_one("#chart-workspace").has_class("hidden"):
            self.close_chart_workspace()
            return
        task_input = self.query_one("#task-input", Input)
        task_input.value = ""
        task_input.focus()


def main() -> None:
    DevKitAI().run()


if __name__ == "__main__":
    main()
