"""Exercise the repository's ignore rules with Git, not string matching."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RepositoryHygieneTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name)
        self.git = shutil.which('git')
        if not self.git:
            self.fail('Git is required to verify repository ignore behavior')
        self.run_git('init', '--quiet')
        for name in ('gitignore', '.gitignore'):
            source = ROOT / name
            if source.is_file():
                shutil.copy2(source, self.repo / name)

    def run_git(self, *args):
        return subprocess.run(
            [self.git, '-c', f'core.excludesFile={os.devnull}', *args],
            cwd=self.repo, capture_output=True, text=True, check=True,
        )

    def assert_paths_ignored(self, paths):
        for name in paths:
            with self.subTest(path=name):
                target = self.repo / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text('test placeholder', encoding='utf-8')
                # Git must not offer private/generated files as untracked candidates.
                output = self.run_git('ls-files', '--others', '--exclude-standard', '--', name)
                self.assertEqual(output.stdout, '')

    def test_local_credentials_are_not_offered_for_commit(self):
        self.assert_paths_ignored([
            '.env', '.env.local', '.env.production', 'config/.env',
            'private.pem', 'config/private.key', 'identity.p12', 'identity.pfx',
        ])

    def test_virtual_environments_are_ignored(self):
        self.assert_paths_ignored(['.venv/pyvenv.cfg', 'venv/pyvenv.cfg', 'env/pyvenv.cfg'])

    def test_generated_python_files_are_ignored(self):
        self.assert_paths_ignored(['__pycache__/physics_engine.pyc', '.pytest_cache/README.md'])

    def test_documented_examples_and_source_remain_trackable(self):
        for name in ('.env.example', '.env.sample', 'main.py', 'requirements.txt'):
            with self.subTest(path=name):
                (self.repo / name).write_text('test placeholder', encoding='utf-8')
                output = self.run_git('ls-files', '--others', '--exclude-standard', '--', name)
                self.assertEqual(output.stdout.strip(), name)


if __name__ == '__main__':
    unittest.main()
