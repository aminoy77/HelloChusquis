from setuptools import setup, find_packages

setup(
    name="hellochusquis",
    version="0.3.0",
    packages=find_packages(),
    py_modules=["cli", "main"],
    install_requires=[
        "rich",
        "pyyaml",
        "httpx",
    ],
    entry_points={
        "console_scripts": [
            "hellochusquis=cli:main",
        ],
    },
)