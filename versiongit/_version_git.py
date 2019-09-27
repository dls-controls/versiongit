import os
import re
from subprocess import check_output, CalledProcessError, PIPE

# These will be filled in if git archive is run
GIT_ARCHIVE_REF_NAMES = "$Format:%D$"
GIT_ARCHIVE_HASH = "$Format:%h$"


def get_version_from_git(path=None):
    """Try to parse version from git describe, fallback to git archive tags"""
    if path is None:
        # If no path to git repo, choose the directory this file is in
        path = os.path.dirname(os.path.abspath(__file__))
    tag, plus, sha1, dirty, error = "0", "unknown", "error", "", None
    if not GIT_ARCHIVE_HASH.startswith("$"):
        # git archive has written a sha1 for us to use
        sha1 = GIT_ARCHIVE_HASH
        for ref_name in GIT_ARCHIVE_REF_NAMES.split(", "):
            if ref_name.startswith("tag: "):
                # On a git archive tag
                tag, plus = ref_name[5:], "0"
    else:
        git_cmd = "git -C %s describe --tags --dirty --always --long" % path
        # output is TAG-NUM-gHEX[-dirty] or HEX[-dirty]
        try:
            output = check_output(git_cmd.split(), stderr=PIPE).decode().strip()
        except CalledProcessError as e:
            error = e.stderr.decode().strip()
        else:
            if output.endswith("-dirty"):
                output = output[:-6]
                dirty = ".dirty"
            if "-" in output:
                # There is a tag, extract it and the other pieces
                match = re.search(r"^(.+)-(\d+)-g([0-9a-f]+)$", output)
                tag, plus, sha1 = match.groups()
            else:
                # No tag, just sha1
                plus, sha1 = "untagged", output
    if plus != "0" or dirty:
        # Not on a tag, add additional info
        tag = "%(tag)s+%(plus)s.%(sha1)s%(dirty)s" % locals()
    return tag, error, sha1


__version__, git_error, git_sha1 = get_version_from_git()


def get_cmdclass(build_py=None, sdist=None):
    """Create cmdclass dict to pass to setuptools.setup that will write a
    _version_static.py file in our resultant sdist, wheel or egg"""
    if build_py is None:
        from setuptools.command.build_py import build_py
    if sdist is None:
        from setuptools.command.sdist import sdist

    def make_version_static(base_dir, pkg):
        with open(os.path.join(base_dir, pkg, "_version_static.py"), "w") as f:
            f.write("__version__ = %r\n" % __version__)

    class BuildPy(build_py):
        def run(self):
            super(BuildPy, self).run()
            for pkg in self.packages:
                make_version_static(self.build_lib, pkg)

    class Sdist(sdist):
        def make_release_tree(self, base_dir, files):
            super(Sdist, self).make_release_tree(base_dir, files)
            for pkg in self.distribution.packages:
                make_version_static(base_dir, pkg)

    return dict(build_py=BuildPy, sdist=Sdist)
