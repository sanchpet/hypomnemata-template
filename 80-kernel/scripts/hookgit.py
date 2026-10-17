"""HEAD-side view of a staged file, for gates that grandfather history.

A gate built on top of this fires on the act (a card closed, a tray archived)
rather than on a file merely being touched, so a registry-wide sweep over
legacy files does not block. Outside a git repo every file counts as new.
"""
import os
import subprocess


def _git(*args):
    try:
        r = subprocess.run(["git", *args], stdin=subprocess.DEVNULL,
                           capture_output=True, text=True)
    except OSError:
        return None
    return r.stdout if r.returncode == 0 else None


def staged_renames():
    """Staged renames as {new_path: old_path}, repo-root relative."""
    out = _git("diff", "--cached", "-M", "--name-status", "--diff-filter=R", "-z")
    parts = out.split("\0") if out else []
    return {parts[i + 2]: parts[i + 1] for i in range(0, len(parts) - 2, 3)}


def head_source(path, renames):
    """Repo-relative path the file had in HEAD (following a staged rename)."""
    rel = os.path.relpath(path).replace(os.sep, "/")
    return renames.get(rel, rel)


def head_text(source):
    """Text of `source` in HEAD, or None if it did not exist there."""
    return _git("show", f"HEAD:./{source}")
