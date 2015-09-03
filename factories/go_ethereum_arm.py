#!/usr/bin/env python
# -*- coding: utf-8 -*-

import factory
reload(factory)
from factory import *

import go_ethereum
reload(go_ethereum)
from go_ethereum import get_short_revision_go, _go_cmds


def arm_go_factory(branch='develop', isPullRequest=False):
    factory = BuildFactory()

    env = {
        "GOPATH": Interpolate("%(prop:workdir)s/go:%(prop:workdir)s/build/Godeps/_workspace"),
        "CC": "arm-linux-gnueabi-gcc",
        "GOOS": "linux",
        "GOARCH": "arm",
        "CGO_ENABLED": "1",
        "GOARM": "5",
        'PATH': [Interpolate("%(prop:workdir)s/go/bin"), "${PATH}"]
    }

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
            command=Interpolate("rm -rf %(prop:workdir)s/go"),
            description="cleaning up",
            descriptionDone="clean up",
            env={"GOPATH": Interpolate("%(prop:workdir)s/go")}
        ),
        ShellCommand(
            haltOnFailure=True,
            logEnviron=False,
            name="move-src",
            command=_go_cmds(branch=branch),
            description="moving src",
            descriptionDone="move src",
            env={"GOPATH": Interpolate("%(prop:workdir)s/go")}
        ),
        ShellCommand(
            haltOnFailure=True,
            logEnviron=False,
            name="build-gexp",
            description="building gexp",
            descriptionDone="build gexp",
            command="go build -v github.com/expanse-project/go-expanse/cmd/gexp",
            env=env
        )
    ]: factory.addStep(step)

    # for step in [
    #     ShellCommand(
    #         haltOnFailure=True,
    #         name="go-test",
    #         description="go testing",
    #         descriptionDone="go test",
    #         command="go test github.com/expanse-project/go-expanse/...",
    #         env=env,
    #         maxTime=900
    #     )
    # ]: factory.addStep(step)

    if not isPullRequest:
        for step in [
            ShellCommand(
                haltOnFailure=True,
                logEnviron=False,
                name="tar-gexp",
                description='packing',
                descriptionDone='pack',
                command=['tar', '-cjf', 'gexp.tar.bz2', 'gexp']
            ),
            SetPropertyFromCommand(
                haltOnFailure=True,
                logEnviron=False,
                name="set-sha256sum",
                command=Interpolate('sha256sum gexp.tar.bz2 | grep -o -w "\w\{64\}"'),
                property='sha256sum'
            ),
            SetProperty(
                description="setting filename",
                descriptionDone="set filename",
                name="set-filename",
                property="filename",
                value=Interpolate("gexp-ARM-%(kw:time_string)s-%(prop:version)s-%(kw:short_revision)s.tar.bz2",
                                  time_string=get_time_string,
                                  short_revision=get_short_revision_go)
            ),
            FileUpload(
                haltOnFailure=True,
                name='upload-gexp',
                slavesrc="gexp.tar.bz2",
                masterdest=Interpolate("public_html/builds/%(prop:buildername)s/%(prop:filename)s"),
                url=Interpolate("/builds/%(prop:buildername)s/%(prop:filename)s")
            ),
            MasterShellCommand(
                name="clean-latest-link",
                description='cleaning latest link',
                descriptionDone='clean latest link',
                command=['rm', '-f', Interpolate("public_html/builds/%(prop:buildername)s/gexp-ARM-latest.tar.bz2")]
            ),
            MasterShellCommand(
                haltOnFailure=True,
                name="link-latest",
                description='linking latest',
                descriptionDone='link latest',
                command=['ln', '-sf', Interpolate("%(prop:filename)s"), Interpolate("public_html/builds/%(prop:buildername)s/gexp-ARM-latest.tar.bz2")]
            )
        ]: factory.addStep(step)

    return factory
