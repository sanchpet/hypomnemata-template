#!/usr/bin/env python3
"""Миграция заметок старого Obsidian-vault → hypomnemata (ADR-0006).
Имя файла/папки → ASCII-slug (транслит кириллицы); исходный заголовок → aliases
(старые [[вики-ссылки]] резолвятся по алиасу). Вложения копируются как есть (slug-путь).
Использование: migrate-vault.py SRC_DIR DEST_DIR
"""
import sys, os, re, shutil

RU = {'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z',
'и':'i','й':'j','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s',
'т':'t','у':'u','ф':'f','х':'h','ц':'c','ч':'ch','ш':'sh','щ':'shch','ъ':'','ы':'y',
'ь':'','э':'e','ю':'yu','я':'ya'}

def translit(s):
    return ''.join(RU.get(c, RU.get(c.lower(),'').upper() if c.isupper() and c.lower() in RU else c) for c in s)

def slug(name):
    s = translit(name).lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s or 'note'

def slug_path(relpath):
    parts = relpath.split(os.sep)
    return os.sep.join(slug(p) for p in parts)

def add_alias(text, title):
    # title (исходный заголовок) → aliases во frontmatter
    if text.startswith('---\n'):
        end = text.find('\n---', 4)
        if end != -1:
            fm = text[4:end]; body = text[end+4:]
            if re.search(r'^aliases\s*:', fm, re.M):
                fm = re.sub(r'^(aliases\s*:\s*\[)', r'\1"%s", ' % title, fm, count=1, flags=re.M)
            else:
                fm = fm.rstrip('\n') + '\naliases: ["%s"]' % title
            return '---\n' + fm + '\n---' + body
    return '---\naliases: ["%s"]\n---\n\n' % title + text

def main():
    src, dst = sys.argv[1], sys.argv[2]
    min_bytes = int(os.environ.get('MIN_BYTES', '0'))  # пропуск заглушек
    nmd = natt = nskip = 0
    for root, dirs, files in os.walk(src):
        for f in files:
            sp = os.path.join(root, f)
            rel = os.path.relpath(sp, src)
            if f == '.DS_Store':
                continue
            if f.endswith('.md'):
                if min_bytes and os.path.getsize(sp) < min_bytes:
                    nskip += 1
                    continue
                title = f[:-3]
                base = slug(title) + '.md'
                rel_dir = os.path.dirname(rel)
                dp = os.path.join(dst, slug_path(rel_dir), base) if rel_dir else os.path.join(dst, base)
                os.makedirs(os.path.dirname(dp), exist_ok=True)
                with open(sp, encoding='utf-8') as fh: txt = fh.read()
                with open(dp, 'w', encoding='utf-8') as fh: fh.write(add_alias(txt, title))
                nmd += 1
            else:
                name = os.path.basename(rel); rd = os.path.dirname(rel)
                stem, ext = os.path.splitext(name)
                dp = os.path.join(dst, slug_path(rd), slug(stem) + ext.lower()) if rd else os.path.join(dst, slug(stem) + ext.lower())
                os.makedirs(os.path.dirname(dp), exist_ok=True)
                shutil.copy2(sp, dp); natt += 1
    print(f"md: {nmd}, attachments: {natt}, skipped(stub): {nskip} → {dst}")

if __name__ == '__main__':
    main()
