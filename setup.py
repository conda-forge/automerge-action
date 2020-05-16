from setuptools import setup, find_packages

setup(
    name="conda_forge_automerge_action",
    version="0.1",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'run-automerge-action=conda_forge_automerge_action.__main__:main',
        ],
    },
)
