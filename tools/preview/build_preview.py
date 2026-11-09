import re, base64, sys
root = sys.argv[1]; out = sys.argv[2]
def b64(p, mime):
    return f"data:{mime};base64," + base64.b64encode(open(f"{root}/{p}", 'rb').read()).decode()
html = open(f"{root}/{sys.argv[3] if len(sys.argv)>3 else 'index.html'}", encoding="utf-8").read()
css = open(f"{root}/fonts.css", encoding='utf-8').read()
css = re.sub(r'url\(["\']?(?:\./)?(fonts/[^)"\']+\.woff2)["\']?\)', lambda m: f'url({b64(m.group(1), "font/woff2")})', css)
html = html.replace('<link rel="stylesheet" href="fonts.css">', '<style>' + css + '</style>')
logo = b64('logo.png', 'image/png')
html = html.replace('src="logo.png"', f'src="{logo}"').replace("g.src='logo.png'", f"g.src='{logo}'")
for js in ('logos.js', 'games.js', 'stats.js'):
    src = open(f"{root}/{js}", encoding='utf-8').read().replace('</script', '<\\/script')
    html = re.sub(r'<script src="' + re.escape(js) + r'"[^>]*></script>', lambda m: '<script>' + src + '</script>', html, count=1)
html = re.sub(r'<link rel="(manifest|icon|apple-touch-icon)"[^>]*>', '', html)
open(out, 'w', encoding='utf-8').write(html)
print(len(html))
