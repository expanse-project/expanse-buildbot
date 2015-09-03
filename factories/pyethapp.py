#!/usr/bin/env python
# -*- coding: utf-8 -*-

import factory
reload(factory)
from factory import *

def pyethapp_factory(branch='master'):
    factory = BuildFactory()
    for step in [
        Git(
            haltOnFailure=True,
            logEnviron=False,
            repourl='https://github.com/expanse-project/pyethapp.git',
            branch=branch,
            mode='full',
            method='copy',
            codebase='pyethapp',
            retry=(5, 3)
        ),
        SetPropertyFromCommand(
            haltOnFailure=True,
            logEnviron=False,
            name="set-version",
            command='sed -ne "s/.*version=.*[^0-9]\([0-9]*\.[0-9]*\.[0-9]*\).*/\\1/p" setup.py',
            property="version"
        ),
        ShellCommand(
            haltOnFailure=True,
            logEnviron=False,
            name="pip-requirements",
            description="installing requirements",
            descriptionDone="install requirements",
            command=["pip", "install", "-r", "requirements.txt"]
        ),
        ShellCommand(
            haltOnFailure=True,
            logEnviron=False,
            name="upgrade-requirements",
            description="upgrading test requirements",
            descriptionDone="upgrade test requirements",
            command=["pip", "install", "--upgrade", "--no-deps", "-r", "requirements.txt"]
        ),
        ShellCommand(
            haltOnFailure=True,
            logEnviron=False,
            name="pip-install",
            description="installing",
            descriptionDone="install",
            command=["pip", "install", "-e", "."]
        ),
        ShellCommand(
            logEnviron=False,
            description="running",
            descriptionDone="run",
            name="pyethapp",
            command=["pyethapp", "--help"]
        )
    ]: factory.addStep(step)

    return factory
