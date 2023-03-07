import os
import sys
import git
import shutil

from typing import Union
from amiyabot import log


class Progress(git.RemoteProgress):
    def update(self, *args, **kwargs):
        GitAutomation.progress(*args, **kwargs)


class GitAutomation:
    def __init__(self, repo_dir: str, repo_url: str, branch: str = 'master'):
        self.repo_dir = repo_dir
        self.repo_url = repo_url
        self.branch = branch

    @staticmethod
    def progress(op_code: int,
                 cur_count: Union[str, float],
                 max_count: Union[str, float, None] = None,
                 message: str = ''):

        curr = int(cur_count / max_count * 100)
        block = int(curr / 4)
        bar = '=' * block + ' ' * (25 - block)

        print('\r', end='')
        print(f'fetching [{bar}] {cur_count} / {max_count} ({curr}%) {message}', end='')

        sys.stdout.flush()

        if cur_count >= max_count:
            print()

    def update(self):
        log.info(f'fetching repo: {self.repo_url}...')
        if not os.path.exists(self.repo_dir):
            git.Repo.clone_from(self.repo_url, to_path=self.repo_dir, progress=self.progress)
        else:
            try:
                repo = git.Repo(self.repo_dir)
                repo.remotes.origin.pull(progress=self.progress)
            except git.InvalidGitRepositoryError:
                shutil.rmtree(self.repo_dir)
                self.update()
            except git.GitCommandError as e:
                log.error(str(e))
            except Exception as e:
                log.error(e)
