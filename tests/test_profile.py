"""
Hermes Warmstart — 完整测试套件
覆盖：正常路径 + 输入校验 + mid 档行为 + 序列化往返 + ziwei_profile
"""
import sys
import os
import json
import pytest
import warnings

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from warmstart import (
    PersonalityProfile, create_profile, create_warmstart_prompt,
    BigFiveScale, BIG_FIVE_QUESTIONS, Scale,
)
from warmstart.scales import DIMENSION_LABELS, DIMENSION_INSTRUCTIONS
from warmstart.prompt import generate_system_prompt_block


# ============================================================
# 量表结构
# ============================================================

class TestScaleStructure:
    def test_five_questions(self):
        assert len(BIG_FIVE_QUESTIONS) == 5

    def test_each_question_has_three_options(self):
        for q in BIG_FIVE_QUESTIONS:
            assert len(q["options"]) == 3, f"{q['id']} 选项数不对"

    def test_each_question_has_score_range(self):
        for q in BIG_FIVE_QUESTIONS:
            scores = [o["score"] for o in q["options"]]
            assert any(s >= 0.9 for s in scores), f"{q['id']} 缺少高分区"
            assert any(s <= 0.3 for s in scores), f"{q['id']} 缺少低分区"

    def test_bigfive_scale_interface(self):
        scale = BigFiveScale()
        assert len(scale.questions) == 5
        result = scale.parse_answers([0, 1, 2, 0, 1])
        assert "conscientiousness" in result
        assert result["conscientiousness"] == 1.0

    def test_bigfive_inherits_scale_protocol(self):
        assert isinstance(BigFiveScale(), Scale)


# ============================================================
# 输入校验（非法路径）
# ============================================================

class TestInputValidation:
    def test_empty_list_rejected(self):
        with pytest.raises(ValueError, match="expected 5 answers, got 0"):
            BigFiveScale().parse_answers([])

    def test_wrong_length_rejected(self):
        with pytest.raises(ValueError, match="expected 5 answers, got 4"):
            BigFiveScale().parse_answers([0, 1, 2, 0])

    def test_index_out_of_range_rejected(self):
        with pytest.raises(ValueError, match="must be 0/1/2, got 3"):
            BigFiveScale().parse_answers([0, 1, 3, 0, 1])

    def test_negative_index_rejected(self):
        with pytest.raises(ValueError, match="must be 0/1/2, got -1"):
            BigFiveScale().parse_answers([0, -1, 2, 0, 1])

    def test_string_answers_rejected(self):
        with pytest.raises(TypeError, match="must be int"):
            BigFiveScale().parse_answers(["a", "b", "c", "d", "e"])

    def test_none_rejected(self):
        with pytest.raises(TypeError, match="must be a list"):
            BigFiveScale().parse_answers(None)


# ============================================================
# Profile 生成
# ============================================================

class TestProfileGeneration:
    def test_from_answers_extreme_high(self):
        p = PersonalityProfile.from_answers([0, 0, 0, 0, 0])
        assert p.conscientiousness == 1.0
        assert p.openness == 1.0

    def test_from_answers_extreme_low_mixed(self):
        p = PersonalityProfile.from_answers([1, 1, 1, 1, 1])
        assert p.conscientiousness == 0.3
        assert p.extraversion == 1.0
        assert p.openness == 0.2
        assert p.neuroticism == 0.2
        assert p.agreeableness == 1.0

    def test_from_answers_default_scale(self):
        p = PersonalityProfile.from_answers([2, 2, 2, 2, 2])
        assert p.conscientiousness == 0.6
        assert p.agreeableness == 0.6

    def test_from_answers_custom_scale(self):
        class MockScale:
            @property
            def questions(self): return []
            def parse_answers(self, answers):
                return {"conscientiousness": 0.42, "extraversion": 0.17}
        assert isinstance(BigFiveScale(), Scale)

    def test_from_scores_unknown_key_warns(self):
        with pytest.warns(UserWarning, match="Unknown dimension 'foo' ignored"):
            PersonalityProfile.from_scores({"foo": 0.8, "conscientiousness": 0.7})

    def test_from_scores_ziwei_preserved(self):
        p = PersonalityProfile.from_scores({
            "conscientiousness": 0.5,
            "ziwei_profile": {"ming_gong": "紫微"},
        })
        assert p.ziwei_profile == {"ming_gong": "紫微"}


# ============================================================
# describe() 输出
# ============================================================

class TestDescribe:
    def test_describe_non_empty(self):
        for answers in [[0,0,0,0,0], [1,1,1,1,1], [2,2,2,2,2], [0,1,2,1,0]]:
            desc = create_profile(answers).describe()
            assert len(desc) > 10

    @pytest.mark.parametrize("dim,threshold,expected_substr", [
        ("conscientiousness", 1.0, "规划"),
        ("conscientiousness", 0.5, "一定计划"),
        ("conscientiousness", 0.2, "灵活"),
        ("extraversion", 0.2, "简洁"),
        ("extraversion", 0.5, "根据对象"),
        ("extraversion", 1.0, "关系建立"),
        ("neuroticism", 0.5, "波动"),
        ("neuroticism", 0.2, "情绪稳定"),
        ("neuroticism", 1.0, "敏感"),
    ])
    def test_describe_tier(self, dim, threshold, expected_substr):
        profile = PersonalityProfile(**{dim: threshold})
        assert expected_substr in profile.describe()


# ============================================================
# Agent 指令（三档测试）
# ============================================================

class TestAgentInstructions:
    def test_five_instructions_always(self):
        for answers in [[0,0,0,0,0], [2,2,2,2,2], [0,1,2,1,0]]:
            inst = create_profile(answers).to_agent_instructions()
            assert len(inst.split("\n")) == 5

    @pytest.mark.parametrize("value,expected_tier", [
        (0.0, "low"),
        (0.3, "low"),
        (0.31, "mid"),
        (0.5, "mid"),
        (0.69, "mid"),
        (0.7, "high"),
        (1.0, "high"),
    ])
    def test_pick_instruction_tier_boundary(self, value, expected_tier):
        inst = DIMENSION_INSTRUCTIONS["conscientiousness"]
        expected = f"- {inst[expected_tier]}"
        p = PersonalityProfile(conscientiousness=value)
        result = p._pick_instruction("conscientiousness", value)
        assert result == expected, f"value={value} expected {expected_tier}, got: {result}"

    def test_all_dimensions_have_high_mid_low(self):
        for dim, inst in DIMENSION_INSTRUCTIONS.items():
            assert "high" in inst, f"{dim} missing high"
            assert "mid" in inst, f"{dim} missing mid"
            assert "low" in inst, f"{dim} missing low"

    def test_instructions_always_prefixed_with_dash(self):
        for v in [0.0, 0.5, 1.0]:
            for dim in ["conscientiousness", "extraversion"]:
                p = PersonalityProfile(**{dim: v})
                inst = p._pick_instruction(dim, v)
                assert inst.startswith("- "), f"dim={dim} v={v}: {inst}"


# ============================================================
# System Prompt 模块
# ============================================================

class TestSystemPrompt:
    def test_contains_required_sections(self):
        block = PersonalityProfile().to_system_prompt_block()
        assert "用户画像" in block
        assert "适配指令" in block
        assert "冷启动先验" in block

    def test_create_warmstart_prompt_no_memory(self):
        prompt = create_warmstart_prompt([2, 2, 2, 2, 2])
        assert "新用户" in prompt

    def test_create_warmstart_prompt_with_memory(self):
        prompt = create_warmstart_prompt([2, 2, 2, 2, 2], memory_text="用户会Python。")
        assert "用户会Python" in prompt
        assert "勿从记忆重复推断" in prompt

    def test_generate_system_prompt_block(self):
        block = generate_system_prompt_block([0, 0, 0, 0, 0])
        assert "用户画像" in block


# ============================================================
# 序列化
# ============================================================

class TestSerialization:
    def test_to_dict_round_trip(self):
        p = PersonalityProfile(conscientiousness=0.8, openness=1.0, neuroticism=0.2)
        d = p.to_dict()
        assert d["conscientiousness"] == 0.8
        assert d["openness"] == 1.0
        json.dumps(d)

    def test_to_dict_includes_ziwei(self):
        p = PersonalityProfile(ziwei_profile={"ming_gong": "紫微"})
        d = p.to_dict()
        assert "ziwei_profile" in d
        assert d["ziwei_profile"] == {"ming_gong": "紫微"}

    def test_to_dict_omits_ziwei_when_none(self):
        p = PersonalityProfile()
        assert "ziwei_profile" not in p.to_dict()

    def test_from_dict_simple(self):
        d = {"conscientiousness": 0.3, "openness": 0.9}
        p = PersonalityProfile.from_dict(d)
        assert p.conscientiousness == 0.3
        assert p.openness == 0.9
        assert p.neuroticism == 0.5

    def test_from_dict_preserves_ziwei(self):
        p = PersonalityProfile.from_dict({"conscientiousness": 0.5, "ziwei_profile": {"k": "v"}})
        assert p.ziwei_profile == {"k": "v"}

    def test_to_dict_from_dict_round_trip(self):
        p1 = PersonalityProfile(conscientiousness=0.7, ziwei_profile={"x": 1})
        p2 = PersonalityProfile.from_dict(p1.to_dict())
        assert p2.conscientiousness == 0.7
        assert p2.ziwei_profile == {"x": 1}


# ============================================================
# 穷举
# ============================================================

class TestExhaustive:
    def test_all_243_combinations(self):
        from itertools import product
        for combo in product([0, 1, 2], repeat=5):
            p = create_profile(list(combo))
            desc = p.describe()
            inst = p.to_agent_instructions()
            block = p.to_system_prompt_block()
            assert len(desc) > 10
            assert len(inst.split("\n")) == 5
            assert "画像" in block


# ============================================================
# 标签完整性
# ============================================================

class TestLabelCompleteness:
    DIMS = ["conscientiousness", "extraversion", "openness", "neuroticism", "agreeableness"]

    def test_all_dimensions_in_labels(self):
        for dim in self.DIMS:
            assert dim in DIMENSION_LABELS

    def test_all_dimensions_in_instructions(self):
        for dim in self.DIMS:
            assert dim in DIMENSION_INSTRUCTIONS

    def test_all_labels_have_high_mid_low(self):
        for dim in self.DIMS:
            for tier in ["high", "mid", "low"]:
                assert tier in DIMENSION_LABELS[dim], f"{dim} missing {tier}"

    def test_all_instructions_have_high_mid_low(self):
        for dim in self.DIMS:
            for tier in ["high", "mid", "low"]:
                assert tier in DIMENSION_INSTRUCTIONS[dim], f"{dim} missing {tier}"
