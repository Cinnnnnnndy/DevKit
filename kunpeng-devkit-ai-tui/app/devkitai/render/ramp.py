"""色阶取值：顺序 vs 分类，以及那条"数据色不上文字"的运行期护栏。

``docs/VISUAL.md`` §1.5 / §1.6 里最容易在实现阶段被搞混的一条：

* **顺序 / 强度** —— 在**同一条色阶内**取档，800 → 300 即暗 → 亮 = 低 → 高。
  用于利用率、风险热力、Trace 密度、内存占用。
* **分类 / 身份** —— **每类取一条色阶**，各用其 -400 档。用于泳道身份、算子类别。
* **分类 + 强度** —— 色阶定身份，档位定强度。Trace 密度带就是这个组合：
  *哪条泳道* 用色阶，*多忙* 用档位。

用五条不同色阶去表达"利用率高低"是明确的错误——五种色相混在一起，
读者建立不起"哪个更热"的直觉。

另一条纪律靠 :func:`assert_block_color` 在运行期兜底：语义色只上字符与短文本，
数据色阶只上色块与点阵。色相上 warning 35° 与 accum-orange 25° 本来就近，
终端里最终是靠**字形**区分的，所以把语义色画进色块会直接毁掉这层区分。
"""

from __future__ import annotations

from typing import Sequence

from ..tokens import CATEGORICAL_INDEX, DOMAIN_RAMPS, SEMANTIC


class ColorDisciplineError(ValueError):
    """把语义色用在了色块 / 点阵上，或把数据色阶用在了文字上。"""


_SEMANTIC_VALUES = frozenset(v.lower() for v in SEMANTIC.values())
_RAMP_VALUES = frozenset(c.lower() for ramp in DOMAIN_RAMPS.values() for c in ramp)


def assert_block_color(color: str) -> str:
    """色块 / 点阵着色前调一次——语义色走到这里就是用错地方了。

    这条不是洁癖。一个 90% 的 CPU 利用率本身**不是错误**，它该用顺序色阶的
    最亮档；只有当 AI 判定它构成问题时，才由标注层叠加 danger 色的描边与角标。
    把"数据"和"结论"用不同的颜色系统表达，是整套规范里最重要的一条用色纪律。
    """
    if color.lower() in _SEMANTIC_VALUES:
        name = next(k for k, v in SEMANTIC.items() if v.lower() == color.lower())
        raise ColorDisciplineError(
            f"语义色 {name}={color} 不能用于色块或点阵——它只上字符与短标签。"
            f"数值大小请用 DOMAIN_RAMPS 的顺序档位表达；"
            f"若要表达'AI 判定这里有问题'，走标注层的描边与角标。"
        )
    return color


def assert_text_color(color: str) -> str:
    """文字着色前调一次——数据色阶走到这里就是用错地方了。"""
    if color.lower() in _RAMP_VALUES:
        raise ColorDisciplineError(
            f"数据色阶 {color} 不能用于文字——它只上色块与点阵。"
            f"文字请用中性前景档、accent，或语义色。"
        )
    return color


def sequential(
    value: float,
    lo: float,
    hi: float,
    domain: str = "cpu",
    *,
    steps: Sequence[str] | None = None,
) -> str:
    """顺序取档：把一个数值映射到同一条色阶的某一档（暗 → 亮 = 低 → 高）。

    ``value`` 落在 ``[lo, hi]`` 之外会被夹住；``hi <= lo`` 时一律返回最低档,
    因为"没有量程"和"值最小"在读图上是同一回事，不该突然变成最亮。
    """
    ramp = tuple(steps) if steps is not None else DOMAIN_RAMPS[domain]
    if hi <= lo:
        return assert_block_color(ramp[0])
    t = (value - lo) / (hi - lo)
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    idx = min(int(t * len(ramp)), len(ramp) - 1)
    return assert_block_color(ramp[idx])


def categorical(domain: str) -> str:
    """分类取色：某个域的身份色（各色阶的 -400 档）。"""
    return assert_block_color(DOMAIN_RAMPS[domain][CATEGORICAL_INDEX])


def grayscale(value: float, lo: float, hi: float) -> str:
    """T3 → T1 降级用的灰阶。

    ``NO_COLOR`` / 16 色终端下真彩热力必须掉到块字符，**语义不能丢**——
    所以这里返回的仍然是一条单调色阶，只是色相被抽掉了。
    """
    ramp = ("#3a3a3a", "#5c5c5c", "#8a8a8a", "#c4c4c4")
    return sequential(value, lo, hi, steps=ramp)
