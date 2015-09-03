#!/usr/bin/env python
# -*- coding: utf-8 -*-

import factory
reload(factory)
from factory import *

distributions = ['trusty', 'vivid']

@properties.renderer
def get_short_revision_go(props):
    if 'got_revision' in props:
        return props['got_revision']['go-expanse'][:7]
    return None


def _go_cmds(branch='master'):
    cmds = [
        "mkdir -p $GOPATH/src/github.com/expanse",
        "cp -a . $GOPATH/src/github.com/expanse-project/go-expanse",
        "rm -rf $GOPATH/pkg"
    ]

    return " && ".join(cmds)


def go_ethereum_factory(branch='master', deb=False):
    factory = BuildFactory()
    for step in [
        Git(
            haltOnFailure=True,
            logEnviron=False,
            repourl='https://github.com/expanse-project/go-expanse.git',
            branch=branch,
            mode='full',
            method='copy',
            codebase='go-expanse',
            retry=(5, 3)
        ),
        SetPropertyFromCommand(
            haltOnFailure=True,
            logEnviron=False,
            name="set-version",
            command='sed -ne "s/.*Version.*=\s*[^0-9]\([0-9]*\.[0-9]*\.[0-9]*\).*/\\1/p" cmd/gexp/main.go',
            property="version"
        ),
        ShellCommand(
            haltOnFailure=True,
            logEnviron=False,
            name="go-cleanup",
            command="rm -rf $GOPATH",
            description="cleaning up",
            descriptionDone="clean up"
        ),
        ShellCommand(
            haltOnFailure=True,
            logEnviron=False,
            name="move-src",
            command=_go_cmds(branch=branch),
            description="moving src",
            descriptionDone="move src"
        ),
        ShellCommand(
            haltOnFailure=True,
            logEnviron=False,
            name="install-gexp",
            description="installing gexp",
            descriptionDone="install gexp",
            command="go install -v github.com/expanse-project/go-expanse/cmd/gexp",
            env={"GOPATH": Interpolate("${GOPATH}:%(prop:workdir)s/build/Godeps/_workspace")}
        )
    ]: factory.addStep(step)

    for step in [
        ShellCommand(
            haltOnFailure=True,
            name="go-test",
            description="go testing",
            descriptionDone="go test",
            command="go test github.com/expanse-project/go-expanse/...",
            env={"GOPATH": Interpolate("${GOPATH}:%(prop:workdir)s/build/Godeps/_workspace")},
            maxTime=900
        )
    ]: factory.addStep(step)

    if deb:
        for architecture in ['i386', 'amd64']:
            for distribution in distributions:
                for step in [
                    Trigger(
                        schedulerNames=["go-expanse-%s-%s-%s" % (branch, architecture, distribution)],
                        waitForFinish=False,
                        set_properties={
                            "version": Interpolate("%(prop:version)s")
                        }
                    )
                ]: factory.addStep(step)

    return factory
