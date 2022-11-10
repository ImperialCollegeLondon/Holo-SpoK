from distutils.core import setup
from catkin_pkg.python_setup import generate_distutils_setup

d = generate_distutils_setup(
    packages=['spot_driver'],
    scripts=['scripts/spot_interface.py'],
    package_dir={'': 'src'}
)

setup(**d)
