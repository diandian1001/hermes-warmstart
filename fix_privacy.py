with open('PRIVACY.md', 'r', encoding='utf-8') as f:
    c = f.read()
old = "Is `localStorage` used? | **No.** The page does not read from or write to `localStorage`, `sessionStorage`, or IndexedDB."
new = "Is `localStorage` used? | **Yes, for UI language preference only.** The page saves your language choice (Chinese/English) to `localStorage` so it persists across visits. **No questionnaire answers, birth information, or generated profiles are stored.** No `sessionStorage` or IndexedDB is used."
c = c.replace(old, new)
with open('PRIVACY.md', 'w', encoding='utf-8') as f:
    f.write(c)
print('Updated:', 'UI language preference' in c)
