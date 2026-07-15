import subprocess, re

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

result = subprocess.run(['git', 'show', 'e1649b5:index.html'], capture_output=True, text=True)
old = result.stdout

idx = old.find('UNIVERSAL_Q = [')
uq_data = 'var ' + old[idx:old.find('];', idx) + 2]

sq_match = re.search(r'const SCENE_Q = (\{.+?^\};)', old, re.DOTALL | re.MULTILINE)
sq_data = 'var SCENE_Q = ' + sq_match.group(1)

q_block = sq_data + '\n\n' + uq_data

marker = "// ========== State & Render"
content = content.replace(marker, q_block + '\n\n' + marker)

old_fn = "function totalSteps(){ return mode === 'exp' ? 11 : 10; }"
new_fn = '''function totalSteps(){
  var scene = SCENE_Q[sceneId];
  var sceneCount = scene ? scene.length : 0;
  if (mode === 'exp') return 1 + 1 + 5 + sceneCount;
  return 1 + 5 + sceneCount;
}'''
content = content.replace(old_fn, new_fn)

old_render = '''  else if(mode==='exp'&&step===1) renderBirth();
  else if((mode==='exp'&&step===2)||(mode==='pro'&&step===1)) renderScenario();
  else {
    var offset = mode==='exp'?2:1;
    if(step>=offset+1&&step<=offset+5) renderUniversal(step-offset-1);
    else if(step>=offset+6&&step<=offset+9) renderSceneQ(step-offset-6);
    else showResult();
  }'''
new_render = '''  else if(mode==='exp'&&step===1) renderBirth();
  else if((mode==='exp'&&step===2)||(mode==='pro'&&step===1)) renderScenario();
  else {
    var offset = mode==='exp'?2:1;
    var sceneQCount = (SCENE_Q[sceneId] || []).length;
    if(step>=offset+1&&step<=offset+5) renderUniversal(step-offset-1);
    else if(step>=offset+6&&step<offset+6+sceneQCount) renderSceneQ(step-offset-6);
    else showResult();
  }'''
content = content.replace(old_render, new_render)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

with open('prompt.js', 'r', encoding='utf-8') as f:
    p = f.read()
p = p.replace('v0.6.2 生成', 'v0.7.1 生成')
with open('prompt.js', 'w', encoding='utf-8') as f:
    f.write(p)

print('SCENE_Q:', 'var SCENE_Q = {' in content)
print('UNIVERSAL_Q:', 'var UNIVERSAL_Q = [' in content)
print('Dynamic steps:', 'sceneCount' in content)
print('v0.7.1:', 'v0.7.1' in p)
