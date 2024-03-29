# type: ignore
import glob
import importlib.util

from setuptools import setup

# Import <package>._version_git.py without importing <package>
path = glob.glob(__file__.replace("setup.py", "*/_version_git.py"))[0]
spec = importlib.util.spec_from_file_location("_version_git", path)
vg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vg)

# Setup information is stored in setup.cfg but this function call
# is still necessary.
setup(cmdclass=vg.get_cmdclass(), version=vg.__version__)
