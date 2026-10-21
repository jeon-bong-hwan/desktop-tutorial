"""Publish built static assets to gh-pages without switching the working branch."""
from pathlib import Path
import os
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
def git(*args, env=None):
    return subprocess.check_output(['git', '-C', str(root), *args], env=env, text=True).strip()

subprocess.run(['node', '--test'], cwd=root, check=True)
subprocess.run(['python3', 'tools/build.py'], cwd=root, check=True)
remote = git('ls-remote', '--heads', 'origin', 'refs/heads/gh-pages')
parent = None
if remote:
    parent = remote.split()[0]
    git('fetch', 'origin', 'refs/heads/gh-pages')
with tempfile.TemporaryDirectory(prefix='station-pages-') as tmp:
    task_env = dict(os.environ)
    task_env['GIT_INDEX_FILE'] = str(Path(tmp) / 'index')
    task_env['GIT_WORK_TREE'] = str(root / 'dist')
    task_env['GIT_DIR'] = git('rev-parse', '--absolute-git-dir')
    git('read-tree', '--empty', env=task_env)
    (root / 'dist' / '.nojekyll').touch()
    files = ['index.html', 'style.css', 'app.js', 'csv.js', 'data.js', 'initial-data.js', '.nojekyll']
    subprocess.run(['git', '--git-dir', task_env['GIT_DIR'], '--work-tree', task_env['GIT_WORK_TREE'], 'add', '--', *files], cwd=root / 'dist', env=task_env, check=True)
    tree = git('write-tree', env=task_env)
    args = ['commit-tree', tree, '-m', 'Publish station lifecycle static website']
    if parent:
        args += ['-p', parent]
    commit = git(*args)
    git('push', 'origin', commit + ':refs/heads/gh-pages')
print('Static files pushed to gh-pages. GitHub Pages must be configured to publish gh-pages / (root).')
print('Expected URL after Pages activation: https://jeon-bong-hwan.github.io/desktop-tutorial/')
