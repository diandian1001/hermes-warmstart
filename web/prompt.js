// ============================================================
// 生成画像（集成命盘）
// ============================================================
function buildPrompt(){
  const qs = SCENE_Q[sceneId];
  const scene = SCENARIOS.find(s=>s.id===sceneId);
  const sceneLabel = scene?scene.label:'未选择';

  // 出生信息
  let birthLine = [];
  if(birth.year) birthLine.push(birth.year+'年');
  if(birth.month) birthLine.push(birth.month+'月');
  if(birth.day) birthLine.push(birth.day+'日');
  if(birth.hour && birth.hour!=='0') birthLine.push(BIRTH_FIELDS.find(f=>f.id==='hour').options[parseInt(birth.hour)]);
  if(birth.gender) birthLine.push('· '+birth.gender);
  const birthStr = birthLine.length?birthLine.join(''):'未填写';
  const hasBirth = birth.year && birth.month && birth.day && birth.hour && birth.gender;

  // 命盘计算
  let ziweiBlock = '';
  if(hasBirth) {
    try {
      const chart = calculateZiwei(
        parseInt(birth.year),
        parseInt(birth.month),
        parseInt(birth.day),
        parseInt(birth.hour),
        birth.gender === '男' ? 'male' : 'female'
      );
      if(chart) {
        ziweiBlock = `## 命盘快照
- 农历：${chart.lunar}
- 命宫：${chart.ming_gong}宫（${chart.palaces['命宫']?.ganzhi || ''}）
- 身宫：${chart.shen_gong}宫
- 五行局：${chart.wuxing_ju}
- 当前大限：${chart.current_da_xian ? chart.current_da_xian.age_range + ' · ' + chart.current_da_xian.gong + '宫' : '未计算'}

### 命盘主星分布
`;
        for(const [name, info] of Object.entries(chart.palaces)) {
          if(info.main_star) {
            ziweiBlock += `- ${name}宫（${info.ganzhi}）：${info.main_star}\n`;
          }
        }
        ziweiBlock += '\n';
      }
    } catch(e) {
      console.error('命盘计算失败:', e);
    }
  }

  // 通用维度
  let universal = [];
  UNIVERSAL_Q.forEach((q,i)=>{
    const a = universalAnswers[i];
    if(a===undefined||a===null||a===-1) universal.push({badge:q.badge,val:'未填写'});
    else universal.push({badge:q.badge,val:q.opts[a].v});
  });

  // 场景维度
  let dims = [];
  qs.forEach((q,i)=>{
    const a = sceneAnswers[i];
    if(a===undefined||a===null||a===-1) dims.push({badge:q.badge,val:'未填写'});
    else if(typeof a==='string') dims.push({badge:q.badge,val:a});
    else dims.push({badge:q.badge,val:q.opts[a].v});
  });

  // MBTI映射
  let mbtiTraits = [];
  if(birth.mbti && MBTI_MAP[birth.mbti]){
    const m = MBTI_MAP[birth.mbti];
    mbtiTraits = [m.e, m.i||m.s, m.t||m.f, m.j||m.p];
  }

  // 组装
  let prompt = `# AI 画像 · ${sceneLabel}

## 用户背景
- 出生信息：${birthStr}
- 使用场景：${sceneLabel}

`;

  // 命盘快照（优先级最高）
  if(ziweiBlock) prompt += ziweiBlock;

  // 通用维度
  prompt += `## 通用偏好\n`;
  universal.forEach(u=>{
    prompt += `- ${u.badge}：${u.val}\n`;
  });
  prompt += '\n';

  // 场景维度
  dims.forEach(d=>{
    prompt += `## ${d.badge}\n${d.val}\n\n`;
  });

  // MBTI补充
  if(mbtiTraits.length){
    prompt += `## MBTI 补充参考
类型：${birth.mbti}
${mbtiTraits.join('\n')}

> ⚠️ 以上为性格背景参考，优先级低于场景维度的回答。
> 如果场景回答与 MBTI 推断有冲突，以场景回答为准。

`;
  }

  prompt += `---
> 本画像由 Warmstart v0.6.0 生成，复制到任何 AI 的 system prompt 中即可生效。
`;
  return prompt;
}
