# Warmstart — 完整使用教学

> 适用对象：Hermes · Claude · Cursor · OpenCode · Windsurf · ChatGPT · 任意 AI agent

---

## 场景

你刚刚装了一个新的 AI agent，第一次对话。agent 不认识你，回复风格不匹配。

---

## Step 1：安装（30 秒）

```bash
pip install git+https://github.com/diandian1001/warmstart.git
```

---

## Step 2：生成画像（1 分钟）

**方式 A：交互式**

```bash
python -m warmstart.prompt
```

回答 5 道选择题，终端打印完整画像模块。

**方式 B：自动写入**

```bash
python -m warmstart.prompt --auto
```

自动检测你环境中的 AI 平台并写入配置文件。

**方式 C：指定文件**

```bash
# Hermes
python -m warmstart.prompt --output ~/.hermes/SOUL.md

# Claude
python -m warmstart.prompt --output CLAUDE.md

# Cursor
python -m warmstart.prompt --output .cursorrules

# OpenCode
python -m warmstart.prompt --output AGENTS.md
```

**方式 D：代码**

```python
from warmstart import create_warmstart_prompt
answers = [0, 1, 2, 0, 1]
with open("CLAUDE.md", "w") as f:
    f.write(create_warmstart_prompt(answers))
```

---

## Step 3：首次对话验证

问 agent 一个中性问题，观察回复风格是否匹配画像：

```
用户：「帮我做一个工作选择的分析」

期望（计划型+独立型）：
  → 先给分析框架，再给结论
  → 简洁直接
  → 给出具体路径而非空泛建议
```

如果风格不匹配，检查画像是否正确写入配置文件。

---

## Step 4：持续修正（3-5 轮后）

对话几轮后，对照观察到的行为：

```
发现：用户每次做决定都会问"你觉得选哪个好" → 宜人性实际上比评估的高

修正：
  agreeableness: 0.2 → 0.7
  → agent 行为变化：多征求意见，双向沟通
```

直接用代码调整：

```python
from warmstart import PersonalityProfile
profile = PersonalityProfile.from_scores({
    "conscientiousness": 0.6,
    "agreeableness": 0.7,
})
```

---

## 支持的所有 AI 平台

```bash
python -m warmstart.prompt --list-platforms
```

---

## 常见问题

**Q：用户不知道选哪个答案怎么办？**
A：选中间项（选项 3）。中间型画像表现为默认行为。

**Q：画像会不会把 agent 限制死？**
A：不会。画像模块明确写了"当实际表现与画像不一致时，以实际表现为准"。画像是起点，不是终点。

**Q：多用户怎么办？**
A：每个用户独立画像。可以为每个用户维护不同的配置文件。

**Q：我的 AI 工具不在支持列表里？**
A：用 `--output` 手动指定配置文件路径即可。任何接受 system prompt 的 AI 都兼容。
