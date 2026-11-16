from pathlib import Path
p=Path(__file__).resolve().parent
source=(p/'templates/index.source.html').read_text(encoding='utf-8')
css=(p/'static/css/style.css').read_text(encoding='utf-8')+'\n'+(p/'static/css/theme-serene.css').read_text(encoding='utf-8')
js=(p/'static/js/app.js').read_text(encoding='utf-8')
source=source.replace('  <link rel="stylesheet" href="/static/css/style.css?v=2">\n  <link rel="stylesheet" href="/static/css/theme-serene.css?v=3">\n  <script src="/static/js/app.js?v=2" defer></script>', '<style id="mindscope-style">\n'+css+'\n</style>')
source=source.replace('</body>', '  <script id="mindscope-script">\n'+js+'\n</script>\n</body>')
source=source.replace('<svg viewBox="0 0 40 40"', '<svg width="32" height="32" viewBox="0 0 40 40"')
(p/'templates/index.html').write_text(source,encoding='utf-8')
print('Da cap nhat templates/index.html. Khoi dong lai website de su dung thay doi.')
