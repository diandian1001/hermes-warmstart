#!/usr/bin/env python3
"""
紫微斗数排盘模块 (Zi Wei Dou Shu Chart Calculator)

纯 Python 实现，基于紫微斗数排盘算法规范。
依赖: lunardate (阳历→农历转换)

用法:
    chart = ZiWeiChart.from_birth_info(year=1995, month=6, day=15, hour=5, gender="male")
    data = chart.to_dict()
"""

import math
from datetime import date
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

import lunardate


# ============================================================================
# 常量定义
# ============================================================================

# 天干
TIAN_GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

# 地支
DI_ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 十二宫功能名称（顺序固定：命宫→兄弟→...→父母，顺时针排列）
PALACE_NAMES = [
    "命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
    "迁移", "交友", "官禄", "田宅", "福德", "父母",
]

# 十二宫固定地支参考（仅用于显示，实际宫位以命宫为起点旋转）

# 十四主星
MAIN_STARS_ALL = [
    "紫微", "天机", "太阳", "武曲", "天同", "廉贞",
    "天府", "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军",
]

# 紫微系六星相对于紫微的偏移（逆时针，即递减方向）
# 紫微(0), 天机(-1), 空(-2), 太阳(-3), 武曲(-4), 天同(-5), 空(-6,-7), 廉贞(-8)
ZIWEI_SERIES = [
    ("紫微", 0),
    ("天机", -1),
    ("太阳", -3),
    ("武曲", -4),
    ("天同", -5),
    ("廉贞", -8),
]

# 天府系八星相对于天府的偏移（顺时针，即递增方向）
# 天府(0), 太阴(+1), 贪狼(+2), 巨门(+3), 天相(+4), 天梁(+5), 七杀(+6), 空(+7,+8,+9), 破军(+10)
TIANFU_SERIES = [
    ("天府", 0),
    ("太阴", 1),
    ("贪狼", 2),
    ("巨门", 3),
    ("天相", 4),
    ("天梁", 5),
    ("七杀", 6),
    ("破军", 10),
]

# 纳音五行表：60甲子每两对一纳音，按五行→局数映射
# 五行局数: 水=2, 木=3, 金=4, 土=5, 火=6
NAYIN_ELEMENTS = [
    4, 6, 3, 5, 4, 6, 2, 5, 4, 3,
    2, 5, 6, 3, 2, 4, 6, 3, 5, 4,
    6, 2, 5, 4, 3, 2, 5, 6, 3, 2,
]

# 五虎遁：年干 → 寅月天干索引
WU_HU_DUN = {
    0: 2, 1: 4, 2: 6, 3: 8, 4: 0,
    5: 2, 6: 4, 7: 6, 8: 8, 9: 0,
}

# 阳年天干（甲丙戊庚壬）
YANG_YEARS = {0, 2, 4, 6, 8}

# 时辰 → 时辰序号（子=0, 丑=1, ..., 亥=11）
# hour 参数仍然使用序号，但也提供映射方便扩展
SHI_CHEN_MAP = {
    0: "子", 1: "丑", 2: "寅", 3: "卯", 4: "辰", 5: "巳",
    6: "午", 7: "未", 8: "申", 9: "酉", 10: "戌", 11: "亥",
}

# 农历月序号映射（安命宫用）
# 正月=2, 二月=3, ..., 十一月=12, 十二月=1
def lunar_month_seq(lunar_month: int) -> int:
    """农历月 → 安命宫月序号"""
    return (lunar_month % 12) + 1


# ============================================================================
# 核心计算函数
# ============================================================================

def year_ganzhi(year: int) -> Tuple[int, int]:
    """公历年 → (天干索引, 地支索引)"""
    tg = (year - 4) % 10
    dz = (year - 4) % 12
    return tg, dz


def get_nayin_ju(tg: int, dz: int) -> int:
    """
    根据天干地支索引获取纳音五行局数。
    tg: 天干索引 (0-9)
    dz: 地支索引 (0-11)
    返回: 2=水二局, 3=木三局, 4=金四局, 5=土五局, 6=火六局
    """
    ganzhi_index = (6 * tg - 5 * dz) % 60  # 0-59
    pair_index = ganzhi_index // 2
    return NAYIN_ELEMENTS[pair_index]


def wuhudun_ying_gan(year_tg: int) -> int:
    """五虎遁：年干 → 寅宫天干索引"""
    return WU_HU_DUN[year_tg]


def get_palace_gan(year_tg: int, dz_index: int) -> int:
    """
    获取某地支宫位的天干。
    year_tg: 年天干索引
    dz_index: 地支索引 (0=子, 1=丑, ..., 11=亥)
    返回: 天干索引
    """
    yin_gan = wuhudun_ying_gan(year_tg)
    # 寅=2, 卯=3, ..., 子=0, 丑=1
    offset = (dz_index - 2) % 12  # 寅相对于当前地支的偏移
    return (yin_gan + offset) % 10


def calc_ming_gong(lunar_month: int, hour: int) -> int:
    """
    安命宫。
    公式: 命宫地支 = (农历月序号 + 时辰序号) % 12
    返回: 地支索引 (0=寅, 1=卯, ..., 11=丑)
    """
    month_seq = lunar_month_seq(lunar_month)
    result = (month_seq + hour) % 12
    # 结果映射: 0→寅(索引2), 1→卯(3), ..., 11→丑(1)
    return result  # 返回的是以寅=0的索引


def calc_shen_gong(lunar_month: int, hour: int) -> int:
    """
    安身宫。
    身宫 = (农历月 + 时辰) 从寅起数。
    返回: 地支索引 (0=寅, 1=卯, ..., 11=丑)
    """
    result = (lunar_month - 1 + hour) % 12
    return result


def calc_ziwei_pos(lunar_day: int, ju_number: int) -> int:
    """
    计算紫微星在十二宫的位置。
    ju_number: 五行局数 (2-6)
    lunar_day: 农历日 (1-30)
    返回: 以寅=0的地支索引

    算法: pos = (lunar_day * ju_number) % 12，然后 (pos - 1) % 12 映射到寅=0。
    """
    pos = (lunar_day * ju_number) % 12
    return (pos - 1) % 12  # 寅=0


def calc_tianfu_pos(ziwei_pos: int) -> int:
    """
    天府星位置（相对于紫微对称）。
    公式: 天府 = (2 - 紫微) % 12, 寅=0
    """
    return (2 - ziwei_pos) % 12


def place_main_stars(ziwei_pos: int) -> Dict[int, List[str]]:
    """
    布十四主星到十二宫。
    返回: {宫位索引(寅=0): [主星名列表]}，支持双星同宫
    """
    stars: Dict[int, List[str]] = {}

    # 紫微系六星（逆排）
    for star_name, offset in ZIWEI_SERIES:
        pos = (ziwei_pos + offset) % 12
        stars.setdefault(pos, []).append(star_name)

    # 天府系八星（顺排）
    tianfu_pos = calc_tianfu_pos(ziwei_pos)
    for star_name, offset in TIANFU_SERIES:
        pos = (tianfu_pos + offset) % 12
        stars.setdefault(pos, []).append(star_name)

    return stars


def calc_da_xian(
    ming_gong_idx: int,
    year_tg: int,
    gender: str,
    ju_number: int,
    palace_gan_map: Dict[int, int],
) -> List[Dict]:
    """
    起大限。
    ming_gong_idx: 命宫索引 (寅=0)
    year_tg: 年天干索引
    gender: "male" / "female"
    ju_number: 五行局数
    palace_gan_map: {宫位索引: 天干索引}

    返回: [{"start_age": N, "end_age": N+9, "gong": "宫名", "stem": "天干"}, ...]
    """
    is_yang_year = year_tg in YANG_YEARS
    is_male = gender == "male"

    # 顺行条件：阳男/阴女
    forward = (is_yang_year and is_male) or (not is_yang_year and not is_male)

    # 起运年龄（简化：五行局数即起运年龄）
    start_age = ju_number

    # 宫位顺序
    palace_order = list(range(12))  # 0=寅, ..., 11=丑
    if not forward:
        palace_order = palace_order[::-1]

    # 从命宫开始
    ming_pos_in_order = palace_order.index(ming_gong_idx)
    rotated = palace_order[ming_pos_in_order:] + palace_order[:ming_pos_in_order]

    da_xian = []
    current_start = start_age
    for palace_idx in rotated:
        dz_name = DI_ZHI[(palace_idx + 2) % 12]  # 转回 0=子的地支索引
        gan_idx = palace_gan_map[palace_idx]
        # 宫位功能名 = 从命宫偏移
        func_name_idx = (palace_idx - ming_gong_idx) % 12
        da_xian.append({
            "start_age": current_start,
            "end_age": current_start + 9,
            "gong": PALACE_NAMES[func_name_idx],
            "stem": TIAN_GAN[gan_idx],
            "branch": dz_name,
        })
        current_start += 10

    return da_xian


def lunar_month_name(month: int) -> str:
    """农历月数字 → 中文名"""
    names = ["", "正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "冬", "腊"]
    if 1 <= month <= 12:
        return names[month]
    return str(month)


def lunar_day_name(day: int) -> str:
    """农历日数字 → 中文名"""
    names = [
        "", "初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
        "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
        "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十",
    ]
    if 1 <= day <= 30:
        return names[day]
    return str(day)


# ============================================================================
# 主类
# ============================================================================

@dataclass
class ZiWeiChart:
    """紫微斗数命盘"""

    # 输入信息
    solar_year: int
    solar_month: int
    solar_day: int
    hour: int              # 时辰序号 0=子, ..., 11=亥
    gender: str            # "male" / "female"

    # 农历信息
    lunar_year: int = 0
    lunar_month: int = 0
    lunar_day: int = 0
    lunar_is_leap: bool = False
    lunar_year_name: str = ""     # 如 "乙亥"
    lunar_month_name: str = ""    # 如 "五"
    lunar_day_name: str = ""      # 如 "十八"

    # 年干支
    year_tg: int = 0   # 年天干索引
    year_dz: int = 0   # 年地支索引

    # 命宫 & 身宫 (寅=0)
    ming_gong_idx: int = 0
    shen_gong_idx: int = 0

    # 五行局
    wuxing_ju: int = 2

    # 紫微天府位置
    ziwei_pos: int = 0
    tianfu_pos: int = 0

    # 十二宫主星（每宫可有多颗星）
    palace_stars: Dict[int, List[str]] = field(default_factory=dict)

    # 十二宫天干映射
    palace_gan: Dict[int, int] = field(default_factory=dict)

    # 大限
    da_xian: List[Dict] = field(default_factory=list)

    @classmethod
    def from_birth_info(
        cls,
        year: int,
        month: int,
        day: int,
        hour: int,
        gender: str,
    ) -> "ZiWeiChart":
        """
        从公历出生信息创建命盘。

        参数:
            year: 公历年
            month: 公历月
            day: 公历日
            hour: 时辰序号 (0=子时, 1=丑时, ..., 11=亥时)
            gender: "male" 或 "female"

        返回: ZiWeiChart 实例

        异常:
            ValueError: 输入参数不合法
        """
        # ── 输入验证 ──
        if not isinstance(hour, int) or not (0 <= hour <= 11):
            raise ValueError(f"hour 必须为 0-11 的整数，当前值: {hour!r}")
        if gender not in ("male", "female"):
            raise ValueError(f"gender 必须为 'male' 或 'female'，当前值: {gender!r}")

        chart = cls(
            solar_year=year,
            solar_month=month,
            solar_day=day,
            hour=hour,
            gender=gender,
        )
        chart._calculate()
        return chart

    def _calculate(self):
        """执行完整的排盘计算"""
        # ── 1. 阳历→农历 ──
        ld = lunardate.LunarDate.fromSolarDate(
            self.solar_year, self.solar_month, self.solar_day
        )
        self.lunar_year = ld.year
        self.lunar_month = ld.month
        self.lunar_day = ld.day
        self.lunar_is_leap = ld.isLeapMonth

        # 年干支
        self.year_tg, self.year_dz = year_ganzhi(self.lunar_year)
        self.lunar_year_name = f"{TIAN_GAN[self.year_tg]}{DI_ZHI[self.year_dz]}"
        self.lunar_month_name = lunar_month_name(self.lunar_month)
        self.lunar_day_name = lunar_day_name(self.lunar_day)

        # ── 2. 安命宫 & 身宫 ──
        self.ming_gong_idx = calc_ming_gong(self.lunar_month, self.hour)
        self.shen_gong_idx = calc_shen_gong(self.lunar_month, self.hour)

        # ── 3. 五行局（命宫纳音） ──
        # 先求命宫的天干
        ming_gong_dz = (self.ming_gong_idx + 2) % 12  # 转回 0=子
        ming_gong_gan = get_palace_gan(self.year_tg, ming_gong_dz)
        self.wuxing_ju = get_nayin_ju(ming_gong_gan, ming_gong_dz)

        # ── 4. 紫微星位置 ──
        self.ziwei_pos = calc_ziwei_pos(self.lunar_day, self.wuxing_ju)
        self.tianfu_pos = calc_tianfu_pos(self.ziwei_pos)

        # ── 5. 布十四主星 ──
        self.palace_stars = place_main_stars(self.ziwei_pos)

        # ── 6. 十二宫天干 ──
        for idx in range(12):
            dz = (idx + 2) % 12  # 寅=0 → 地支索引
            self.palace_gan[idx] = get_palace_gan(self.year_tg, dz)

        # ── 7. 起大限 ──
        self.da_xian = calc_da_xian(
            ming_gong_idx=self.ming_gong_idx,
            year_tg=self.year_tg,
            gender=self.gender,
            ju_number=self.wuxing_ju,
            palace_gan_map=self.palace_gan,
        )

    def to_dict(self) -> Dict:
        """将命盘输出为结构化字典"""
        # 命宫地支名
        ming_dz = DI_ZHI[(self.ming_gong_idx + 2) % 12]
        shen_dz = DI_ZHI[(self.shen_gong_idx + 2) % 12]

        # 十二宫详情（按功能名：命宫→兄弟→...→父母）
        palaces = {}
        for func_idx in range(12):
            abs_idx = (self.ming_gong_idx + func_idx) % 12  # 绝对宫位索引 (寅=0)
            dz_idx = (abs_idx + 2) % 12  # 转回地支索引 (0=子)
            gan = TIAN_GAN[self.palace_gan[abs_idx]]
            dz = DI_ZHI[dz_idx]
            main_stars = self.palace_stars.get(abs_idx, [])
            main_star = "/".join(main_stars) if main_stars else ""
            palaces[PALACE_NAMES[func_idx]] = {
                "ganzhi": f"{gan}{dz}",
                "main_star": main_star,
                "stars": [],
                "tlb": "",
            }

        # 计算当前大限
        today = date.today()
        current_age = today.year - self.solar_year
        # 如果还没过生日，年龄减1
        if (today.month, today.day) < (self.solar_month, self.solar_day):
            current_age -= 1

        current_dx = None
        for dx in self.da_xian:
            if dx["start_age"] <= current_age <= dx["end_age"]:
                current_dx = {
                    "start_age": dx["start_age"],
                    "end_age": dx["end_age"],
                    "gong": dx["gong"],
                    "stem": dx["stem"],
                }
                break

        return {
            "solar": {
                "year": self.solar_year,
                "month": self.solar_month,
                "day": self.solar_day,
                "hour": self.hour,
                "gender": self.gender,
            },
            "lunar": {
                "year": self.lunar_year_name,
                "month": self.lunar_month_name,
                "day": self.lunar_day_name,
                "leap": self.lunar_is_leap,
            },
            "ming_gong": ming_dz,
            "shen_gong": shen_dz,
            "wuxing_ju": f"{['', '', '水二局', '木三局', '金四局', '土五局', '火六局'][self.wuxing_ju]}",
            "palaces": palaces,
            "da_xian": [{
                "start_age": d["start_age"],
                "end_age": d["end_age"],
                "gong": d["gong"],
                "stem": d["stem"],
            } for d in self.da_xian],
            "current_da_xian": current_dx,
        }

    def __repr__(self) -> str:
        d = self.to_dict()
        return (
            f"ZiWeiChart("
            f"{d['solar']['year']}-{d['solar']['month']:02d}-{d['solar']['day']:02d}, "
            f"农历{d['lunar']['year']}年{d['lunar']['month']}月{d['lunar']['day']}, "
            f"命宫{d['ming_gong']}, {d['wuxing_ju']})"
        )


# ============================================================================
# 测试用例
# ============================================================================

if __name__ == "__main__":
    import json

    print("=" * 60)
    print("紫微斗数排盘测试")
    print("=" * 60)

    test_cases = [
        # 测试1: 1995-06-15 巳时(5) 男（规范示例）
        {
            "name": "测试1: 1995-06-15 巳时 男",
            "year": 1995, "month": 6, "day": 15, "hour": 5, "gender": "male",
        },
        # 测试2: 1984-02-10 子时(0) 女
        {
            "name": "测试2: 1984-02-10 子时 女",
            "year": 1984, "month": 2, "day": 10, "hour": 0, "gender": "female",
        },
        # 测试3: 2000-01-01 午时(6) 男
        {
            "name": "测试3: 2000-01-01 午时 男",
            "year": 2000, "month": 1, "day": 1, "hour": 6, "gender": "male",
        },
        # 测试4: 1976-08-23 酉时(9) 女
        {
            "name": "测试4: 1976-08-23 酉时 女",
            "year": 1976, "month": 8, "day": 23, "hour": 9, "gender": "female",
        },
        # 测试5: 1984-02-10 子时(0) 男（阳年男→顺行）
        {
            "name": "测试5: 1984-02-10 子时 男 (顺行)",
            "year": 1984, "month": 2, "day": 10, "hour": 0, "gender": "male",
        },
    ]

    for tc in test_cases:
        print(f"\n{'─' * 50}")
        print(f"📋 {tc['name']}")
        print(f"{'─' * 50}")

        chart = ZiWeiChart.from_birth_info(
            year=tc["year"],
            month=tc["month"],
            day=tc["day"],
            hour=tc["hour"],
            gender=tc["gender"],
        )
        result = chart.to_dict()

        print(f"  公历: {result['solar']['year']}-{result['solar']['month']:02d}-{result['solar']['day']:02d}")
        print(f"  农历: {result['lunar']['year']}年{result['lunar']['month']}月{result['lunar']['day']}{' (闰)' if result['lunar']['leap'] else ''}")
        print(f"  命宫: {result['ming_gong']}  |  身宫: {result['shen_gong']}  |  {result['wuxing_ju']}")
        print(f"  主星分布:")

        # 按十二宫顺序打印
        for gong_name in PALACE_NAMES:
            p = result["palaces"][gong_name]
            star = p["main_star"] if p["main_star"] else "—"
            print(f"    {gong_name:4s} ({p['ganzhi']:3s}): {star}")

        print(f"  大限:")
        for dx in result["da_xian"]:
            marker = ""
            if result["current_da_xian"] and dx["start_age"] == result["current_da_xian"]["start_age"]:
                marker = " ← 当前"
            print(f"    {dx['start_age']:2d}-{dx['end_age']:2d}岁  {dx['stem']}{dx['gong']}{marker}")

    print(f"\n{'=' * 60}")
    print("✅ 全部测试完成")
    print(f"{'=' * 60}")

    # ========================================================================
    # Assert 测试用例 — 验证核心算法正确性
    # ========================================================================
    print(f"\n{'=' * 60}")
    print("🔬 Assert 验证")
    print(f"{'=' * 60}")

    # ── 测试1: 纳音索引公式 ──
    # 甲子(tg=0, dz=0) → ganzhi_index=0 → pair 0 → NAYIN_ELEMENTS[0]=4(金四局)
    assert get_nayin_ju(0, 0) == 4, f"甲子应为金四局(4)，实际: {get_nayin_ju(0, 0)}"
    # 乙丑(tg=1, dz=1) → ganzhi_index=1 → pair 0 → 金四局(4)
    assert get_nayin_ju(1, 1) == 4, f"乙丑应为金四局(4)，实际: {get_nayin_ju(1, 1)}"
    # 丙寅(tg=2, dz=2) → ganzhi_index=2 → pair 1 → NAYIN_ELEMENTS[1]=6(火六局)
    assert get_nayin_ju(2, 2) == 6, f"丙寅应为火六局(6)，实际: {get_nayin_ju(2, 2)}"
    # 戊辰(tg=4, dz=4) → ganzhi_index=4 → pair 2 → NAYIN_ELEMENTS[2]=3(木三局)
    assert get_nayin_ju(4, 4) == 3, f"戊辰应为木三局(3)，实际: {get_nayin_ju(4, 4)}"
    # 壬子(tg=8, dz=0) → ganzhi_index=48 → pair 24 → NAYIN_ELEMENTS[24]=3(木三局)
    assert get_nayin_ju(8, 0) == 3, f"壬子应为木三局(3)，实际: {get_nayin_ju(8, 0)}"
    print("  ✅ 纳音索引公式测试通过")

    # ── 测试2: 紫微位置公式 ──
    # 农历日15, 金四局(4): (15*4)%12=0, (0-1)%12=11 → 寅=0索引中为丑(11)
    assert calc_ziwei_pos(15, 4) == 11, f"日15局4紫微位应为11，实际: {calc_ziwei_pos(15, 4)}"
    # 农历日1, 水二局(2): (1*2)%12=2, (2-1)%12=1 → 卯(1)
    assert calc_ziwei_pos(1, 2) == 1, f"日1局2紫微位应为1，实际: {calc_ziwei_pos(1, 2)}"
    # 农历日10, 火六局(6): (10*6)%12=0, (0-1)%12=11 → 丑(11)
    assert calc_ziwei_pos(10, 6) == 11, f"日10局6紫微位应为11，实际: {calc_ziwei_pos(10, 6)}"
    # 农历日5, 土五局(5): (5*5)%12=1, (1-1)%12=0 → 寅(0)
    assert calc_ziwei_pos(5, 5) == 0, f"日5局5紫微位应为0，实际: {calc_ziwei_pos(5, 5)}"
    print("  ✅ 紫微位置公式测试通过")

    # ── 测试3: 主星覆盖（双星同宫） ──
    # 紫微在寅(0)时，天府在(2-0)%12=2(辰)
    # 紫微系: 紫微@0, 天机@11, 太阳@9, 武曲@8, 天同@7, 廉贞@4
    # 天府系: 天府@2, 太阴@3, 贪狼@4, 巨门@5, 天相@6, 天梁@7, 七杀@8, 破军@0
    stars = place_main_stars(0)
    # 紫微@0 和 破军@0 → 寅宫应有双星: ["紫微", "破军"]
    assert 0 in stars, "寅宫应有星"
    assert isinstance(stars[0], list), "stars[0]应为列表"
    assert "紫微" in stars[0], f"寅宫应含紫微，实际: {stars[0]}"
    assert "破军" in stars[0], f"寅宫应含破军，实际: {stars[0]}"
    assert len(stars[0]) == 2, f"寅宫应有2颗星，实际: {stars[0]}"
    # 廉贞@4 和 贪狼@4 → 午宫应有双星: ["廉贞", "贪狼"]
    assert "廉贞" in stars[4], f"午宫应含廉贞，实际: {stars[4]}"
    assert "贪狼" in stars[4], f"午宫应含贪狼，实际: {stars[4]}"
    # 武曲@8 和 七杀@8 → 申宫应有双星: ["武曲", "七杀"]
    assert "武曲" in stars[8], f"申宫应含武曲，实际: {stars[8]}"
    assert "七杀" in stars[8], f"申宫应含七杀，实际: {stars[8]}"
    print("  ✅ 主星双星同宫测试通过")

    # ── 测试4: 输入验证 ──
    try:
        ZiWeiChart.from_birth_info(1995, 6, 15, hour=12, gender="male")
        assert False, "hour=12 应抛出 ValueError"
    except ValueError as e:
        assert "hour" in str(e), f"异常信息应包含hour，实际: {e}"
    try:
        ZiWeiChart.from_birth_info(1995, 6, 15, hour=-1, gender="male")
        assert False, "hour=-1 应抛出 ValueError"
    except ValueError:
        pass
    try:
        ZiWeiChart.from_birth_info(1995, 6, 15, hour=5, gender="other")
        assert False, "gender='other' 应抛出 ValueError"
    except ValueError as e:
        assert "gender" in str(e), f"异常信息应包含gender，实际: {e}"
    print("  ✅ 输入验证测试通过")

    # ── 测试5: 完整排盘集成测试 ──
    chart = ZiWeiChart.from_birth_info(1995, 6, 15, hour=5, gender="male")
    result = chart.to_dict()

    # 基础字段存在性
    assert "solar" in result
    assert "lunar" in result
    assert "ming_gong" in result
    assert "shen_gong" in result
    assert "wuxing_ju" in result
    assert "palaces" in result
    assert "da_xian" in result

    # 十二宫应全部存在
    for name in PALACE_NAMES:
        assert name in result["palaces"], f"缺少宫位: {name}"

    # 大限应有12条
    assert len(result["da_xian"]) == 12, f"大限应有12条，实际: {len(result['da_xian'])}"

    # to_dict 中 main_star 应为字符串（可用 "/" 连接多星）
    for p in result["palaces"].values():
        assert isinstance(p["main_star"], str), f"main_star应为字符串，实际: {type(p['main_star'])}"

    print("  ✅ 集成测试通过")

    print(f"\n{'=' * 60}")
    print("✅ 全部 Assert 验证通过")
    print(f"{'=' * 60}")
