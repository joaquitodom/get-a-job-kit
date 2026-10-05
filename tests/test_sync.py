import subprocess
from pathlib import Path

import pytest

from tools.sync import pull, push

ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def commit_file(repo, path, text, message="change"):
    f = Path(repo) / path
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, encoding="utf-8")
    git(repo, "add", path)
    git(repo, "commit", "-q", "-m", message)


@pytest.fixture
def repos(tmp_path, monkeypatch):
    for k, v in ENV.items():
        monkeypatch.setenv(k, v)
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(remote))
    kit = tmp_path / "kit"  # the maintainer's clone
    git(tmp_path, "clone", "-q", str(remote), str(kit))
    for key, value in (("user.name", "t"), ("user.email", "t@t")):
        git(kit, "config", key, value)
    commit_file(kit, "CLAUDE.md", "v1\n")
    commit_file(kit, "profile/PROFILE.md", "plantilla\n")
    git(kit, "push", "-q", "origin", "main")
    his = tmp_path / "his"  # the job seeker's clone
    git(tmp_path, "clone", "-q", str(remote), str(his))
    for key, value in (("user.name", "t"), ("user.email", "t@t")):
        git(his, "config", key, value)
    return kit, his


def test_pull_reports_kit_files_that_changed(repos):
    kit, his = repos
    commit_file(kit, "CLAUDE.md", "v2\n")
    git(kit, "push", "-q")
    message = pull(his)
    assert "CLAUDE.md" in message
    assert (his / "CLAUDE.md").read_text() == "v2\n"


def test_pull_with_nothing_new_says_nothing(repos):
    _, his = repos
    assert pull(his) == ""


def test_pull_conflict_aborts_and_keeps_his_work(repos):
    kit, his = repos
    commit_file(kit, "profile/PROFILE.md", "del kit\n")
    git(kit, "push", "-q")
    commit_file(his, "profile/PROFILE.md", "suyo\n")
    message = pull(his)
    assert "conflicto" in message.lower()
    assert (his / "profile/PROFILE.md").read_text() == "suyo\n"
    assert not (his / ".git" / "rebase-merge").exists()


def test_pull_without_network_is_silent_and_does_not_raise(repos):
    _, his = repos
    git(his, "remote", "set-url", "origin", str(his.parent / "missing.git"))
    assert pull(his) == ""


def test_push_commits_and_pushes_uncommitted_data(repos, tmp_path):
    kit, his = repos
    (his / "postulaciones").mkdir()
    (his / "postulaciones" / "banco.md").write_text("cv\n", encoding="utf-8")
    push(his)
    git(kit, "pull", "-q")
    assert (kit / "postulaciones" / "banco.md").read_text() == "cv\n"


def test_push_never_commits_kit_files(repos):
    _, his = repos
    (his / "CLAUDE.md").write_text("editado a mano\n", encoding="utf-8")
    push(his)
    assert "CLAUDE.md" in git(his, "status", "--porcelain")


def test_push_with_nothing_to_send_says_nothing(repos):
    _, his = repos
    assert push(his) == ""


def test_push_when_remote_moved_ahead_pulls_first_and_then_pushes(repos):
    kit, his = repos
    commit_file(kit, "CLAUDE.md", "v2\n")
    git(kit, "push", "-q")
    (his / "postulaciones").mkdir()
    (his / "postulaciones" / "fondo.md").write_text("cv\n", encoding="utf-8")
    assert push(his) == ""
    git(kit, "pull", "-q")
    assert (kit / "postulaciones" / "fondo.md").exists()
    assert (his / "CLAUDE.md").read_text() == "v2\n"


from tools.sync import classify_git_error  # noqa: E402


@pytest.mark.parametrize("stderr", [
    "fatal: Authentication failed for 'https://github.com/o/r.git/'",
    "remote: Permission to o/r.git denied to someone.\nfatal: unable to access",
    "fatal: could not read Username for 'https://github.com': terminal prompts disabled",
])
def test_github_login_problems_are_classified_as_auth(stderr):
    assert classify_git_error(stderr) == "auth"


def test_missing_git_identity_is_classified_as_identity():
    assert classify_git_error("Author identity unknown\n*** Please tell me who you are.") == "identity"


def test_network_problems_are_classified_as_offline():
    assert classify_git_error("fatal: unable to access 'https://github.com/o/r.git/': Could not resolve host: github.com") == "offline"


def test_push_without_git_identity_asks_to_configure_it(repos, monkeypatch, tmp_path):
    _, his = repos
    for k in ENV:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "no-global"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    git(his, "config", "--unset", "user.name")
    git(his, "config", "--unset", "user.email")
    git(his, "config", "user.useConfigOnly", "true")
    (his / "postulaciones").mkdir()
    (his / "postulaciones" / "x.md").write_text("cv\n", encoding="utf-8")
    assert "user.email" in push(his)


def _run_main(monkeypatch, capsys, stdin, message):
    import io
    import json

    import tools.sync as sync

    monkeypatch.setattr(sync, "push", lambda repo: message)
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin))
    sync.main(["push"])
    return json.loads(capsys.readouterr().out or "{}")


def test_stop_hook_makes_claude_act_on_a_missing_identity(monkeypatch, capsys):
    from tools.sync import IDENTITY

    out = _run_main(monkeypatch, capsys, '{"stop_hook_active": false}', IDENTITY)
    assert (out["decision"], out["reason"]) == ("block", IDENTITY)


def test_stop_hook_does_not_loop_when_claude_already_continued(monkeypatch, capsys):
    from tools.sync import IDENTITY

    out = _run_main(monkeypatch, capsys, '{"stop_hook_active": true}', IDENTITY)
    assert "decision" not in out and out["systemMessage"] == IDENTITY


def test_pull_blocked_by_his_untracked_file_is_reported_not_silent(repos):
    kit, his = repos
    commit_file(kit, "cv/master-es.pdf", "del kit\n")
    git(kit, "push", "-q")
    (his / "cv").mkdir(exist_ok=True)
    (his / "cv" / "master-es.pdf").write_text("suyo\n", encoding="utf-8")
    message = pull(his)
    assert "cv/master-es.pdf" in message
    assert (his / "cv" / "master-es.pdf").read_text() == "suyo\n"
