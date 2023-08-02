import os
import sys
import git
import shutil

from typing import Union, List
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
        print(f'Fetching [{bar}] {cur_count} / {max_count} ({curr}%) {message}', end='')

        sys.stdout.flush()

        if cur_count >= max_count:
            print()

    def update(self, options: List[str] = None):
        log.info(f'Pulling repo "{self.repo_url}" -> "{self.repo_dir}"...')
        if not os.path.exists(self.repo_dir):
            git.Repo.clone_from(self.repo_url,
                                to_path=self.repo_dir,
                                progress=self.progress,
                                multi_options=options or [])
        else:
            try:
                repo = git.Repo(self.repo_dir)
                repo.remotes.origin.pull(progress=self.progress)
            except git.InvalidGitRepositoryError:
                shutil.rmtree(self.repo_dir)
                self.update(options)
            except git.GitCommandError as e:
                log.error(e)
                log.warning(f'Git 操作失败，请确保 "git" 命令能够正确执行或删除目录 "{self.repo_dir}" 后重试')
            except Exception as e:
                log.error(e)
