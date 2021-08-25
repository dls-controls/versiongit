import os
import sys
from argparse import ArgumentParser


def maybe_warn_snippet(path, *snippets):
    # type: (str, str) -> None
    path = os.path.abspath(path)
    if os.path.exists(path):
        with open(path) as f:
            dest_text = f.read()
    else:
        dest_text = ""
    if any(snippet not in dest_text for snippet in snippets):
        print(
            """\
Please add the following snippet to %s:
--------------------------------------------------------------------------------
%s
--------------------------------------------------------------------------------
"""
            % (path, "\n".join(snippets))
        )
    return dest_text


def main():
    from versiongit import __version__

    parser = ArgumentParser(
        description="Command line tool adding versiongit to python module"
    )
    parser.add_argument(
        "--version", action="store_true", help="Print the current version of versiongit"
    )
    parser.add_argument(
        "dir", nargs="?", help="The directory to add _version_git.py to"
    )
    args = parser.parse_args()
    if args.version:
        print(__version__)
    else:
        assert args.dir and os.path.isdir(args.dir), (
            "Expected a python package directory, got %r" % args.dir
        )
        versiongit_path = os.path.dirname(os.path.abspath(__file__))
        # Write _version_git.py with descriptive header
        with open(os.path.join(versiongit_path, "_version_git.py")) as f:
            lines = f.readlines()
        header = (
            """# Compute a version number from a git repo or archive

# This file is released into the public domain. Generated by:
# versiongit-%s (https://github.com/dls-controls/versiongit)
"""
            % __version__
        )
        # Make sure when running from git archive or a released version,
        # the format strings are put back in
        for i, line in enumerate(lines):
            split = line.split(" = ")
            if split[0] == "GIT_REFS":
                lines[i] = split[0] + ' = "$Format:%D$"\n'
            elif split[0] == "GIT_SHA1":
                lines[i] = split[0] + ' = "$Format:%h$"\n'
        with open(os.path.join(args.dir, "_version_git.py"), "w") as f:
            f.write(header)
            f.writelines(lines)
        print("Added %s\n" % os.path.join(args.dir, "_version_git.py"))
        # Make sure __init__.py lines are in
        maybe_warn_snippet(
            os.path.join(args.dir, "__init__.py"),
            "from ._version_git import __version__",
        )
        # Make sure .gitattribute lines are in
        maybe_warn_snippet(
            os.path.join(args.dir, "..", ".gitattributes"),
            "*/_version_git.py export-subst",
        )
        # Make sure the setup.py lines are in
        txt = maybe_warn_snippet(
            os.path.join(args.dir, "..", "setup.py"),
            "import glob",
            "import importlib.util",
            "",
            "from setuptools import setup",
            "",
            "# Import <package>._version_git.py without importing <package>",
            'path = glob.glob(__file__.replace("setup.py", "*/_version_git.py"))[0]',
            'spec = importlib.util.spec_from_file_location("_version_git", path)',
            "vg = importlib.util.module_from_spec(spec)",
            "spec.loader.exec_module(vg)",
            "",
            "setup(",
            "cmdclass=vg.get_cmdclass(),",
            "version=vg.__version__",
            ")",
        )
        old_method = """\
# Place the directory containing _version_git on the path
for path, _, filenames in os.walk(os.path.dirname(os.path.abspath(__file__))):
    if "_version_git.py" in filenames:
        sys.path.append(path)
        break"""
        if old_method in txt:
            print(
                """\
Removing the lines:
--------------------------------------------------------------------------------
%s
--------------------------------------------------------------------------------
"""
                % (old_method)
            )


# So we can run the file directly for testing
if __name__ == "__main__":
    sys.path.insert(1, os.path.join(os.path.dirname(__file__), ".."))
    main()
