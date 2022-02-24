from setuptools import setup


def _requires_from_file(filename):
    return open(filename, encoding="utf-8").read().splitlines()


setup(
    name='imgconv',
    version='0.1.0',
    install_requires=_requires_from_file("requirements.txt"),
    packages=["dist"],
    entry_points={
        'console_scripts': [
            "imgconv=dist.imgconv.main:main"
        ]
    }
)
