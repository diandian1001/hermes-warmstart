// ============================================================
// 紫微斗数简化版命盘计算（JavaScript）
// ============================================================

// 天干
const TIAN_GAN = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"];
// 地支
const DI_ZHI = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"];
// 十二宫名
const PALACE_NAMES = ["命宫","兄弟","夫妻","子女","财帛","疾厄","迁移","交友","官禄","田宅","福德","父母"];
// 纳音五行局数（60甲子每两对一纳音）
const NAYIN_ELEMENTS = [4,6,3,5,4,6,2,5,4,3,2,5,6,3,2,4,6,3,5,4,6,2,5,4,3,2,5,6,3,2];
// 五虎遁：年干 → 寅月天干
const WU_HU_DUN = [2,4,6,8,0,2,4,6,8,0];
// 阳年天干
const YANG_YEARS = [0,2,4,6,8];
// 时辰名
const HOUR_NAMES = ["子时(23-1点)","丑时(1-3)","寅时(3-5)","卯时(5-7)","辰时(7-9)","巳时(9-11)","午时(11-13)","未时(13-15)","申时(15-17)","酉时(17-19)","戌时(19-21)","亥时(21-23)"];

// 五行局名
const WUXING_JU_NAMES = {2:"水二局",3:"木三局",4:"金四局",5:"土五局",6:"火六局"};

// 简化版阳历→农历（使用查表法，仅支持1900-2100年）
function solarToLunar(year, month, day) {
  // 使用基础算法估算农历
  // 注意：这是简化版，不处理闰月
  const baseDate = new Date(1900, 0, 31); // 1900年正月初一
  const targetDate = new Date(year, month-1, day);
  const diffDays = Math.floor((targetDate - baseDate) / 86400000);
  
  if (diffDays < 0) return null;
  
  // 农历月大小月表（1900-2100简化）
  const lunarMonths = [30,29,30,29,30,29,30,29,30,29,30,29]; // 大月30天，小月29天
  
  let lunarYear = 1900;
  let lunarMonth = 1;
  let lunarDay = diffDays + 1;
  
  // 估算年份
  while (lunarDay > 354) { // 农历一年约354天
    lunarDay -= 354;
    lunarYear++;
  }
  
  // 估算月份
  while (lunarDay > lunarMonths[(lunarMonth-1) % 12]) {
    lunarDay -= lunarMonths[(lunarMonth-1) % 12];
    lunarMonth++;
    if (lunarMonth > 12) {
      lunarMonth = 1;
      lunarYear++;
    }
  }
  
  return { year: lunarYear, month: lunarMonth, day: lunarDay, isLeap: false };
}

// 年干支
function yearGanzhi(year) {
  const tg = (year - 4) % 10;
  const dz = (year - 4) % 12;
  return { tg, dz, name: TIAN_GAN[tg] + DI_ZHI[dz] };
}

// 纳音五行局
function getNayinJu(tg, dz) {
  const ganzhiIndex = (6 * tg - 5 * dz) % 60;
  const pairIndex = Math.floor(ganzhiIndex / 2);
  return NAYIN_ELEMENTS[pairIndex];
}

// 农历月序号（安命宫用）
function lunarMonthSeq(month) {
  return (month % 12) + 1;
}

// 安命宫
function calcMingGong(lunarMonth, hour) {
  const monthSeq = lunarMonthSeq(lunarMonth);
  const result = (monthSeq + hour) % 12;
  return result; // 0=寅, 1=卯, ..., 11=丑
}

// 安身宫
function calcShenGong(lunarMonth, hour) {
  return (lunarMonth - 1 + hour) % 12;
}

// 紫微星位置
function calcZiweiPos(lunarDay, juNumber) {
  const pos = (lunarDay * juNumber) % 12;
  return (pos - 1) % 12; // 转为寅=0
}

// 天府星位置
function calcTianfuPos(ziweiPos) {
  return (2 - ziweiPos) % 12;
}

// 布十四主星
function placeMainStars(ziweiPos) {
  const stars = {};
  
  // 紫微系六星（逆排）
  const ziweiSeries = [
    ["紫微", 0], ["天机", -1], ["太阳", -3], ["武曲", -4], ["天同", -5], ["廉贞", -8]
  ];
  for (const [name, offset] of ziweiSeries) {
    const pos = (ziweiPos + offset + 12) % 12;
    if (!stars[pos]) stars[pos] = [];
    stars[pos].push(name);
  }
  
  // 天府系八星（顺排）
  const tianfuPos = calcTianfuPos(ziweiPos);
  const tianfuSeries = [
    ["天府", 0], ["太阴", 1], ["贪狼", 2], ["巨门", 3], ["天相", 4], ["天梁", 5], ["七杀", 6], ["破军", 10]
  ];
  for (const [name, offset] of tianfuSeries) {
    const pos = (tianfuPos + offset) % 12;
    if (!stars[pos]) stars[pos] = [];
    stars[pos].push(name);
  }
  
  return stars;
}

// 起大限
function calcDaXian(mingGongIdx, yearTg, gender, juNumber) {
  const isYangYear = YANG_YEARS.includes(yearTg);
  const isMale = gender === "male";
  const forward = (isYangYear && isMale) || (!isYangYear && !isMale);
  
  const startAge = juNumber;
  let order = Array.from({length: 12}, (_, i) => i);
  if (!forward) order.reverse();
  
  const mingPosInOrder = order.indexOf(mingGongIdx);
  const rotated = order.slice(mingPosInOrder).concat(order.slice(0, mingPosInOrder));
  
  const daXian = [];
  let currentStart = startAge;
  for (const palaceIdx of rotated) {
    const funcNameIdx = (palaceIdx - mingGongIdx + 12) % 12;
    daXian.push({
      start_age: currentStart,
      end_age: currentStart + 9,
      gong: PALACE_NAMES[funcNameIdx],
    });
    currentStart += 10;
  }
  
  return daXian;
}

// 主函数：计算命盘
function calculateZiwei(year, month, day, hour, gender) {
  // 1. 农历转换
  const lunar = solarToLunar(year, month, day);
  if (!lunar) return null;
  
  // 2. 年干支
  const gz = yearGanzhi(lunar.year);
  
  // 3. 命宫、身宫
  const mingGongIdx = calcMingGong(lunar.month, hour);
  const shenGongIdx = calcShenGong(lunar.month, hour);
  
  // 4. 五行局
  const mingGongDz = (mingGongIdx + 2) % 12;
  const juNumber = getNayinJu(gz.tg, mingGongDz);
  
  // 5. 紫微位置
  const ziweiPos = calcZiweiPos(lunar.day, juNumber);
  
  // 6. 布主星
  const palaceStars = placeMainStars(ziweiPos);
  
  // 7. 大限
  const daXian = calcDaXian(mingGongIdx, gz.tg, gender, juNumber);
  
  // 8. 当前大限
  const currentYear = new Date().getFullYear();
  const currentAge = currentYear - year;
  const currentDaXian = daXian.find(d => currentAge >= d.start_age && currentAge <= d.end_age);
  
  // 9. 组装结果
  const palaces = {};
  for (let i = 0; i < 12; i++) {
    const absIdx = (mingGongIdx + i) % 12;
    const dzIdx = (absIdx + 2) % 12;
    const mainStar = (palaceStars[absIdx] || []).join("/");
    palaces[PALACE_NAMES[i]] = {
      ganzhi: TIAN_GAN[gz.tg] + DI_ZHI[dzIdx],
      main_star: mainStar,
    };
  }
  
  return {
    lunar: `${gz.name}年${lunar.month}月${lunar.day}日`,
    ming_gong: DI_ZHI[(mingGongIdx + 2) % 12],
    shen_gong: DI_ZHI[(shenGongIdx + 2) % 12],
    wuxing_ju: WUXING_JU_NAMES[juNumber],
    palaces: palaces,
    current_da_xian: currentDaXian ? {
      age_range: `${currentDaXian.start_age}-${currentDaXian.end_age}岁`,
      gong: currentDaXian.gong,
    } : null,
  };
}
