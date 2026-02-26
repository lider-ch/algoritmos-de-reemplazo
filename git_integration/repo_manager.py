"""Git repository manager using gitpython."""
from __future__ import annotations
import os
import datetime


def _get_repo(project_root: str):
    """Return a git.Repo object, initialising if necessary."""
    try:
        import git
        try:
            repo = git.Repo(project_root)
        except git.exc.InvalidGitRepositoryError:
            repo = git.Repo.init(project_root)
            # Create initial .gitignore commit
            gitignore = os.path.join(project_root, ".gitignore")
            if os.path.exists(gitignore):
                repo.index.add([".gitignore"])
                repo.index.commit("chore: init repository with .gitignore")
        return repo
    except ImportError:
        return None


def init_repo(project_root: str) -> str:
    """Initialise (or confirm) git repo. Returns status message."""
    repo = _get_repo(project_root)
    if repo is None:
        return "gitpython no instalado – repositorio no gestionado."
    return f"Repositorio git en: {repo.working_dir}"


def commit_results(project_root: str, message: str | None = None) -> str:
    """Stage all output files and create a commit. Returns status message."""
    repo = _get_repo(project_root)
    if repo is None:
        return "gitpython no instalado."

    if message is None:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"results: simulación {ts}"

    # Stage everything (respecting .gitignore)
    repo.git.add(A=True)
    if not repo.index.diff("HEAD" if repo.head.is_valid() else None) and not repo.untracked_files:
        return "Nada nuevo para confirmar."

    repo.index.commit(message)
    return f"Commit creado: {message}"


def show_log(project_root: str, n: int = 10) -> list[dict]:
    """Return list of recent commit info dicts."""
    repo = _get_repo(project_root)
    if repo is None or not repo.head.is_valid():
        return []
    commits = []
    for commit in repo.iter_commits(max_count=n):
        commits.append({
            "hash":    commit.hexsha[:8],
            "author":  str(commit.author),
            "date":    datetime.datetime.fromtimestamp(commit.committed_date).strftime("%Y-%m-%d %H:%M"),
            "message": commit.message.strip(),
        })
    return commits


def push_to_remote(project_root: str, remote_url: str, branch: str = "main") -> str:
    """Add remote and push. Returns status message."""
    repo = _get_repo(project_root)
    if repo is None:
        return "gitpython no instalado."

    try:
        remote = repo.remote("origin")
        remote.set_url(remote_url)
    except ValueError:
        remote = repo.create_remote("origin", remote_url)

    try:
        repo.git.push("--set-upstream", "origin", branch)
        return f"Push exitoso → {remote_url} ({branch})"
    except Exception as exc:
        return f"Error al hacer push: {exc}"
