"""
Hermes Warmstart — Agent 冷启动画像系统

以量表为底（心理学量表），以命盘为壳（紫微斗数），
为 AI agent 提供结构化用户画像先验，让新用户首次对话就能获得个性化适配。

Quickstart:
    from warmstart import create_profile, create_warmstart_prompt

    # 5 题答案 [0/1/2]
    answers = [0, 1, 0, 2, 0]
    profile = create_profile(answers)

    # 生成 warmstart 模块（画像 + 记忆）
    warmstart_block = create_warmstart_prompt(answers, memory_text="用户擅长数据分析。")
    # 将 warmstart_block 拼接到你的 system prompt 中

    # 或交互式评估
    import warmstart.prompt
    warmstart.prompt.main()

扩展量表：
    from warmstart import Scale, PersonalityProfile
    class MyScale(Scale):
        ...
    profile = PersonalityProfile.from_answers(answers, scale=MyScale())
"""

from .profile import PersonalityProfile, create_profile, create_warmstart_prompt
from .scales import BigFiveScale, BIG_FIVE_QUESTIONS, Scale

__version__ = "0.1.1"
__all__ = [
    "PersonalityProfile",
    "create_profile",
    "create_warmstart_prompt",
    "BigFiveScale",
    "BIG_FIVE_QUESTIONS",
    "Scale",
]
