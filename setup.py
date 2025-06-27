#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name="folder-audio-player",
    version="0.1.1",
    description="A simple folder-based audio player",
    author="Ivan",
    author_email="ivan@example.com",
    url="https://github.com/ivanthecrazy/folder-audio-player",
    packages=find_packages(),
    py_modules=["app", "main", "mpris", "player", "utils"],
    include_package_data=True,
    install_requires=[
        "PyGObject",
        "mutagen",
    ],
    entry_points={
        "console_scripts": [
            "folder-audio-player=main:main",
        ],
    },
    data_files=[
        ('share/applications', ['data/dev.ivan-larionov.FolderAudioPlayer.desktop']),
        ('share/icons/hicolor/scalable/apps', ['data/dev.ivan-larionov.FolderAudioPlayer.svg']),
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Multimedia :: Sound/Audio :: Players",
    ],
)
