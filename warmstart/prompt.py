"""
Warmstart — 交互式评估 + System Prompt 注入

用法:
    python -m warmstart.prompt                    # 交互式，打印到终端
    python -m warmstart.prompt --output SOUL.md   # 写入指定文件
    python -m warmstart.prompt --auto             # 自动检测平台并写入
    python -m warmstart.prompt --list-platforms   # 列出支持的平台
"""

import argparse
import json
import os
import sys
from pathlib import Path

from .profile import PersonalityProfile, create_profile, create_warmstart_prompt
from .scales import BigFiveScale, BIG_FIVE_QUESTIONS

# ============================================================
# 平台自动检测
# ============================================================

PLATFORMS = {
    "hermes": {
        "name": "Hermes Agent",
        "paths": [
            "~/.hermes/profiles/default/SOUL.md",
            "~/.hermes/SOUL.md",
        ],
        "section": "## 用户画像",
    },
    "claude": {
        "name": "Claude (Desktop / Code)",
        "paths": [
            "~/CLAUDE.md",
            "~/.claude/CLAUDE.md",
            "CLAUDE.md",
        ],
        "section": "## User Profile",
    },
    "cursor": {
        "name": "Cursor",
        "paths": [
            ".cursorrules",
            "~/.cursorrules",
        ],
        "section": "## User Profile",
    },
    "opencode": {
        "name": "OpenCode",
        "paths": [
            "~/.opencode/AGENTS.md",
            "AGENTS.md",
        ],
        "section": "## 用户画像",
    },
    "windsurf": {
        "name": "Windsurf (Codeium)",
        "paths": [
            ".windsurfrules",
            "~/.windsurfrules",
        ],
        "section": "## User Profile",
    },
    "chatgpt": {
        "name": "ChatGPT (Custom Instructions)",
        "paths": [
            "~/.chatgpt/custom_instructions.md",
        ],
        "section": "## About Me",
    },
}


def detect_platform() -> dict | None:
    """自动检测当前环境存在哪个平台配置文件"""
    home = Path.home()
    for key, info in PLATFORMS.items():
        for path_pattern in info["paths"]:
            p = Path(path_pattern.replace("~", str(home)))
            # 检查文件是否存在，或目录是否存在（对于 .hermes/profiles/ 等）
            if p.exists() and p.is_file():
                return {"key": key, "path": str(p), **info}
            # 也检查父目录是否存在（说明安装了该平台）
            if p.parent.exists() and p.parent.is_dir():
                pass  # 继续找实际文件
    return None


def list_platforms():
    """打印所有支持的平台"""
    home = str(Path.home())
    print("\n支持的 AI 平台：\n")
    for key, info in PLATFORMS.items():
        print(f"  {info['name']}")
        for p in info["paths"]:
            resolved = p.replace("~", home)
            exists = "✅" if os.path.exists(resolved) else "  "
            print(f"    {exists} {p}")
        print()


def append_to_file(filepath: str, content: str, section_name: str = "## 用户画像"):
    """
    将画像模块写入文件。
    - 如果文件已存在且包含同名 section：原地替换
    - 如果文件已存在但不包含：追加到末尾
    - 如果文件不存在：创建
    """
    path = Path(filepath).expanduser().resolve()

    if path.exists():
        existing = path.read_text(encoding="utf-8")

        # 查找同名 section，原地替换
        start_marker = section_name
        if start_marker in existing:
            # 找到 section 的起止位置
            start = existing.find(start_marker)
            # 找下一个同级 section（## 开头）或文件末尾
            rest = existing[start + len(start_marker):]
            next_section = rest.find("\n## ")
            if next_section != -1:
                end = start + len(start_marker) + next_section
                new_content = existing[:start] + content + "\n" + existing[end:]
            else:
                new_content = existing[:start] + content
            path.write_text(new_content, encoding="utf-8")
            return f"已原地替换 {path} 中的「{section_name}」"

        # 不存在同名 section，追加到末尾
        new_content = existing.rstrip() + "\n\n" + content + "\n"
        path.write_text(new_content, encoding="utf-8")
        return f"已追加到 {path} 末尾"
    else:
        # 新文件
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"已创建 {path}"


# ============================================================
# 交互式评估
# ============================================================

def interactive_quiz() -> PersonalityProfile:
    """终端交互式 5 题评估"""
    questions = BIG_FIVE_QUESTIONS

    print("\n" + "=" * 50)
    print("  Agent 画像快速评估（5题）")
    print("=" * 50)
    print("请根据实际情况选择最接近的一项。\n")

    answers = []
    for i, q in enumerate(questions, 1):
        print(f"\n[{i}/5] {q['question']}")
        for j, opt in enumerate(q["options"]):
            print(f"  {j+1}. {opt['text']}")
        while True:
            try:
                choice = input("  你的选择 (1/2/3): ").strip()
                idx = int(choice) - 1
                if 0 <= idx <= 2:
                    answers.append(idx)
                    break
            except ValueError:
                pass
            print("  请输入 1、2 或 3")

    return create_profile(answers)


def generate_system_prompt_block(answers: list[int]) -> str:
    """生成可直接粘贴到 system prompt 的画像模块"""
    profile = create_profile(answers)
    return profile.to_system_prompt_block()


# ============================================================
# CLI
# ============================================================

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="warmstart",
        description="生成 AI agent 冷启动画像，5 道选择题即可个性化适配",
    )
    p.add_argument(
        "--output", "-o",
        type=str,
        help="写入指定文件（如 SOUL.md、CLAUDE.md、.cursorrules）",
    )
    p.add_argument(
        "--auto",
        action="store_true",
        help="自动检测当前环境的 AI 平台并写入对应配置文件",
    )
    p.add_argument(
        "--list-platforms",
        action="store_true",
        help="列出所有支持的 AI 平台及其配置路径",
    )
    p.add_argument(
        "--section",
        type=str,
        default="## 用户画像",
        help="写入文件时使用的 section 标题（默认：'## 用户画像'）",
    )
    p.add_argument(
        "--scores",
        type=str,
        help="跳过交互，直接用 JSON 分数生成画像（如 '{\"conscientiousness\":0.6,...}'）",
    )
    return p


def main(args=None):
    parser = build_parser()
    opts = parser.parse_args(args)

    # --list-platforms：只列平台，不跑评估
    if opts.list_platforms:
        list_platforms()
        return

    try:
        # 确定画像来源：JSON 分数 或 交互式
        if opts.scores:
            scores = json.loads(opts.scores)
            profile = PersonalityProfile.from_scores(scores)
        else:
            print("=" * 60)
            print("  Warmstart — AI Agent 冷启动画像生成器")
            print("  底：大五人格快速量表 | 壳：紫微斗数命盘（预留）")
            print("=" * 60)
            profile = interactive_quiz()

        content = profile.to_system_prompt_block()

        # 确定输出目标
        if opts.auto:
            detected = detect_platform()
            if detected:
                result = append_to_file(detected["path"], content, opts.section)
                print(f"\n✅ {result}")
                print(f"   平台: {detected['name']}")
            else:
                print("\n⚠️  未检测到已知平台的配置文件。")
                print("   请使用 --output <path> 指定文件，或 --list-platforms 查看已知路径。")
                sys.exit(1)
        elif opts.output:
            result = append_to_file(opts.output, content, opts.section)
            print(f"\n✅ {result}")
        else:
            # 默认：打印到终端
            print("\n" + "=" * 60)
            print("  生成结果")
            print("=" * 60)
            print(f"\n【画像分数】{json.dumps(profile.to_dict(), ensure_ascii=False)}")
            print(f"\n【自然语言画像】\n{profile.describe()}")
            print(f"\n【Agent行为指令】\n{profile.to_agent_instructions()}")
            print(f"\n【完整 System Prompt 模块】\n{content}")

            print("\n" + "=" * 60)
            print("  下一步")
            print("=" * 60)
            print(f"""
  方式一：复制上面的模块，粘贴到你的 AI agent 的配置文件。
         常见路径：
""")
            home = str(Path.home())
            for key, info in PLATFORMS.items():
                print(f"          {info['name']}: {info['paths'][0].replace('~', home)}")
            print(f"""
  方式二：下次直接自动写入：
          python -m warmstart.prompt --auto

  方式三：写入指定文件：
          python -m warmstart.prompt --output ~/.hermes/SOUL.md
          python -m warmstart.prompt --output CLAUDE.md
          python -m warmstart.prompt --output .cursorrules
""")

    except KeyboardInterrupt:
        print("\n\n  已取消评估。")
    except EOFError:
        print("\n\n  输入流结束，已退出。")


if __name__ == "__main__":
    main()
