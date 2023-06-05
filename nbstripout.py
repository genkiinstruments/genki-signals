#!/usr/bin/env python
"""strip outputs from an IPython Notebook
Opens a notebook, strips its output, and writes the outputless version to the original file.
Useful mainly as a git filter or pre-commit hook for users who don't want to track output in VCS.
This does mostly the same thing as the `Clear All Output` command in the notebook UI.
LICENSE: Public Domain

Taken and adapted from: https://gist.github.com/minrk/6176788
"""


import io
import sys

try:
    # Jupyter >= 4
    from nbformat import read, write, NO_CONVERT
except ImportError:
    # IPython 3
    try:
        from IPython.nbformat import read, write, NO_CONVERT
    except ImportError:
        # IPython < 3
        from IPython.nbformat import current

        def read(f, as_version):
            return current.read(f, "json")

        def write(nb, f):
            return current.write(nb, f, "json")


def _cells(nb):
    """Yield all cells in an nbformat-insensitive manner"""
    if nb.nbformat < 4:
        for ws in nb.worksheets:
            for cell in ws.cells:
                yield cell
    else:
        for cell in nb.cells:
            yield cell


def strip_output(nb):
    """strip the outputs from a notebook object"""
    nb.metadata.pop("signature", None)
    for cell in _cells(nb):
        # All these were determined by trial and error
        if "outputs" in cell:
            cell["outputs"] = []
        if "execution_count" in cell:
            cell["execution_count"] = None
        if "prompt_number" in cell:
            cell["prompt_number"] = None
        if "metadata" not in cell:
            cell["metadata"] = {}
        if "ExecuteTime" in cell["metadata"]:
            del cell["metadata"]["ExecuteTime"]

        for option, default in [
            ("deletable", True),
            ("editable", True),
            ("heading_collapsed", False),
            ("hidden", False),
        ]:
            cell["metadata"][option] = default

    return nb


def main():
    # Because this is used as a git filter, we need to read from `stdin` and save to `stdin`
    nb = read(io.StringIO(sys.stdin.read()), as_version=NO_CONVERT)
    nb = strip_output(nb)
    write(nb, sys.stdout)


if __name__ == "__main__":
    main()
