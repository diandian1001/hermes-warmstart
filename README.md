# Warmstart — AI Agent 冷启动画像系统

**5 道选择题 → 让任何 AI agent 第一次见你就像认识你十年。**

支持 Hermes · Claude · Cursor · OpenCode · Windsurf · ChatGPT · 及任何接受 system prompt 的 AI 工具。

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-52%20passed-brightgreen.svg)](tests/)

---

## 为什么需要 Warmstart

AI agent 冷启动时的核心痛点：

| | 传统 agent | Warmstart |
|---|---|---|
| 第 1 轮画像覆盖度 | 0-20% | **100%**（5 维全有） |
| 达到完全适配 | 3-5 轮试探 | **第 1 轮** |
| 画像修正方式 | 追加扁平文本 | 数值调整 1 个维度 |

不再让 agent 花 5 轮猜你是什么样的人。

---

## 快速开始

```bash
pip install git+https://github.com/diandian1001/warmstart.git
```

### 交互式评估（推荐）

```bash
python -m warmstart.prompt
```

回答 5 道选择题，自动打印画像模块。

### 自动写入 AI 配置文件

```bash
python -m warmstart.prompt --auto
```

自动检测你环境中的 AI 平台（Hermes / Claude / Cursor / OpenCode / Windsurf / ChatGPT）并写入对应配置文件。

### 写入指定文件

```bash
python -m warmstart.prompt --output CLAUDE.md
python -m warmstart.prompt --output .cursorrules
python -m warmstart.prompt --output ~/.hermes/SOUL.md
```

### 代码调用

```python
from warmstart import create_warmstart_prompt

answers = [0, 1, 2, 0, 1]
module = create_warmstart_prompt(answers)
# → 返回可直接注入 system prompt 的文本模块
```

### 查看支持的平台

```bash
python -m warmstart.prompt --list-platforms
```

---

## 支持的 AI 平台

| 平台 | 自动检测 | 配置文件 |
|------|---------|---------|
| **Hermes Agent** | ✅ | `~/.hermes/SOUL.md` |
| **Claude Desktop / Code** | ✅ | `~/CLAUDE.md` / `~/.claude/CLAUDE.md` |
| **Cursor** | ✅ | `.cursorrules` |
| **OpenCode** | ✅ | `~/.opencode/AGENTS.md` |
| **Windsurf** | ✅ | `.windsurfrules` |
| **ChatGPT** | ✅ | `~/.chatgpt/custom_instructions.md` |
| **任意其他** | — | `python -m warmstart.prompt --output <文件路径>` |

---

## 设计理念

**"以量表为底，以命盘为壳"**

- **底层：心理学量表**（大五人格快速版）→ 提供可量化的用户画像
- **外壳：紫微斗数命盘** → 提供时间维度的动态变化预测（预留接口）

5 个维度 → 5 条 agent 行为指令：

| 维度 | 高分 | 低分 | Agent 行为差异 |
|------|------|------|---------------|
| 尽责性 | 计划型 | 灵活型 | 先框架 vs 先结论 |
| 外向性 | 关系型 | 直接型 | 建立连接 vs 简洁高效 |
| 开放性 | 创新型 | 经验型 | 多样方案 vs 成熟方法 |
| 情绪稳定性 | 敏感型 | 稳定型 | 先共情 vs 直接分析 |
| 宜人性 | 合作型 | 独立型 | 征求意见 vs 尊重判断 |

---

## 项目结构

```
warmstart/
├── warmstart/
│   ├── __init__.py      # 公开 API
│   ├── profile.py       # 画像引擎 (PersonalityProfile)
│   ├── scales.py        # 量表定义（大五 + 可扩展接口）
│   └── prompt.py        # CLI 交互 + 平台检测 + 自动写入
├── tests/
│   └── test_profile.py  # 52 项测试（含输入校验 + mid 档 + ziwei 往返）
├── examples/
│   └── walkthrough.md   # 完整使用教学
├── templates/
│   └── system_prompt_template.txt
├── CONTRIBUTING.md
├── LICENSE
└── pyproject.toml
```

---

## 扩展

### 添加新量表

实现 `Scale` 协议：

```python
from warmstart import Scale, PersonalityProfile

class MyScale(Scale):
    @property
    def questions(self) -> list[dict]:
        return [...]

    def parse_answers(self, answers: list[int]) -> dict:
        # 校验输入，返回 维度名→分数 映射
        ...
```

然后用它：

```python
profile = PersonalityProfile.from_answers(answers, scale=MyScale())
```

### 命盘时间轴（开发中）

当用户提供生辰八字时，在量表画像上叠加命盘时间维度，获得大限/流年驱动的动态画像。

---

## FAQ

**Q: 5 道题够准吗？**
A: 这是初始先验，不是最终画像。agent 会在后续对话中持续修正。目的是从 0% 覆盖直接跳到有方向的猜测。

**Q: 能和大五人格完整量表（50 题）比吗？**
A: 不能。5 题版追求速度（1 分钟）和低门槛。

**Q: 不输入生辰八字能用吗？**
A: 完全能。命盘是可选的第二层。量表画像本身已经足够。

**Q: 支持哪些 AI？**
A: 任何接受 system prompt 的 AI。已内置 Hermes / Claude / Cursor / OpenCode / Windsurf / ChatGPT 的自动检测。其他工具用 `--output` 手动指定即可。

**Q: 为什么用紫微斗数而不是占星？**
A: 紫微斗数提供离散化的命运结构（12 宫 × 14 主星），天然适合作为结构化数据注入 agent。

---

## 许可

MIT © 2026 Diandian
