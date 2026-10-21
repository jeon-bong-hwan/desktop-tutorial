"""Build a standalone HTML and a minimal deployable static directory."""
from pathlib import Path
import shutil
import hashlib
import re

root = Path(__file__).resolve().parents[1]
dist = root / 'dist'
dist.mkdir(exist_ok=True)
assets = ['index.html', 'style.css', 'app.js', 'csv.js', 'statistics.js', 'data.js', 'initial-data.js']
for name in assets:
    shutil.copy2(root / name, dist / name)
shutil.copytree(root / 'sync', dist / 'sync', dirs_exist_ok=True)
html = (root / 'index.html').read_text()
html = html.replace('<link rel="stylesheet" href="style.css">', '<style>' + (root / 'style.css').read_text() + '</style>')
html = html.replace('<script src="initial-data.js"></script>', '')
script = 'globalThis.STATION_SYNC_STATUS=' + (root / 'sync/status.json').read_text().replace('<', '\\u003c') + ';\n'
script += 'globalThis.STATION_NTS_STATUS=' + (root / 'sync/nts.json').read_text().replace('<', '\\u003c') + ';\n'
script += 'globalThis.STATION_CHANGES=' + (root / 'sync/changes.json').read_text().replace('<', '\\u003c') + ';\n'
script += (root / 'initial-data.js').read_text() + '\n'
script += (root / 'data.js').read_text().replace('export const ', 'const ') + '\n'
script += (root / 'csv.js').read_text().replace('export function ', 'function ') + '\n'
script += (root / 'statistics.js').read_text().replace('export function ', 'function ') + '\n'
script += '\n'.join(line for line in (root / 'app.js').read_text().splitlines() if not line.startswith('import '))
html = html.replace('<script type="module" src="app.js"></script>', '<script type="module">' + script + '</script>')
(root / 'dist' / 'station-lifecycle.html').write_text(html)
print('Built static site and standalone HTML in', dist)

# Refresh module imports together so browsers cannot mix releases.
version = hashlib.sha256(b''.join((root / name).read_bytes() for name in assets)).hexdigest()[:12]
for name in ['index.html', 'app.js']:
    path = dist / name
    content = path.read_text()
    if name == 'index.html':
        content = content.replace('href="style.css"', f'href="style.css?v={version}"')
        content = re.sub(r'src="([^"?]+\.js)"', lambda m: f'src="{m[1]}?v={version}"', content)
    else:
        content = re.sub(r"from '(\./[^'?]+\.js)'", lambda m: f"from '{m[1]}?v={version}'", content)
    path.write_text(content)
