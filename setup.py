from setuptools import setup, find_packages

setup(
    name="conda_forge_tick_action",
    version="0.1",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'run-regro-cf-autotick-bot-action=conda_forge_tick_action.__main__:main',
        ],
    },
)
