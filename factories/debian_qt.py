#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: caktux
# @Date:   2015-03-06 16:34:42
# @Last Modified by:   caktux
# @Last Modified time: 2015-03-20 00:54:15

import factory
reload(factory)
from factory import *


def backport_factory(name=None, distribution='trusty', architecture='amd64'):
    factory = BuildFactory()

    packages = [
        "harfbuzz",
        "qtbase-opensource-src",
        "qtxmlpatterns-opensource-src",
        "qtdeclarative-opensource-src",
        "qtscript-opensource-src",
        "qtwebkit-opensource-src",
        "qttools-opensource-src",
        "qtquick1-opensource-src",
        "qtquickcontrols-opensource-src",
        "qtlocation-opensource-src"
    ]

    if distribution == 'trusty':
        packages.append("libinput")

    for package in packages:
        for step in [
            # Create backport
            ShellCommand(
                haltOnFailure=True,
                logEnviron = False,
                name="backport-%s" % package,
                description='backporting %s' % package,
                descriptionDone='backport %s' % package,
                command=["backportpackage", "--dont-sign", "-w", "result", "-d", distribution, package],
                env={
                    "DEBFULLNAME": "caktux (Buildserver key)",
                    "DEBEMAIL": "caktux@gmail.com",
                    "UBUMAIL": "caktux@gmail.com"
                }
            )
        ]: factory.addStep(step)

    for step in [
        # Prepare .changes file for Launchpad
        ShellCommand(
            name='prepare-changes',
            description='preparing changes',
            descriptionDone='prepare changes',
            command=Interpolate('sed -i -e s/%(kw:dist)s-backports/%(kw:dist)s/ -e s/urgency=medium/urgency=low/ *.changes', dist=distribution),
            workdir="build/result"
        ),
        # Upload result folder
        DirectoryUpload(
            slavesrc="result",
            masterdest=Interpolate("public_html/builds/%(prop:buildername)s/%(prop:buildnumber)s"),
            url=Interpolate("/builds/%(prop:buildername)s/%(prop:buildnumber)s"),
        ),
        # Clean latest link
        MasterShellCommand(
            name='clean-latest',
            description='cleaning latest link',
            descriptionDone='clean latest link',
            command=['rm', '-f', Interpolate("public_html/builds/%(prop:buildername)s/latest")]
        ),
        # Link latest
        MasterShellCommand(
            name='link-latest',
            description='linking latest',
            descriptionDone='link latest',
            command=['ln', '-sf', Interpolate("%(prop:buildnumber)s"), Interpolate("public_html/builds/%(prop:buildername)s/latest")]
        ),
        # Create source changes folders
        MasterShellCommand(
            name='mkdir-changes',
            description='mkdir',
            descriptionDone='mkdir',
            command=['mkdir', '-p', Interpolate("changes/%(kw:dist)s/%(kw:arch)s/%(kw:name)s", dist=distribution, arch=architecture, name=name)]
        ),
        # Link source changes
        MasterShellCommand(
            name='link-changes',
            description='linking changes',
            descriptionDone='link changes',
            command=['ln', '-sf', Interpolate("../../../../public_html/builds/%(prop:buildername)s/%(prop:buildnumber)s"), Interpolate("changes/%(kw:dist)s/%(kw:arch)s/%(kw:name)s", dist=distribution, arch=architecture, name=name)]
        ),
        # debsign
        MasterShellCommand(
            haltOnFailure=False,
            flunkOnFailure=False,
            name='debsign',
            description='debsigning',
            descriptionDone='debsign',
            command=Interpolate("debsign changes/%(kw:dist)s/%(kw:arch)s/%(kw:name)s/%(prop:buildnumber)s/*.changes", dist=distribution, arch=architecture, name=name)
        ),
        # dput
        MasterShellCommand(
            name='dput',
            description='dputting',
            descriptionDone='dput',
            command=Interpolate("dput ppa:ethereum/ethereum-qt changes/%(kw:dist)s/%(kw:arch)s/%(kw:name)s/%(prop:buildnumber)s/*.changes", dist=distribution, arch=architecture, name=name)
        )
    ]: factory.addStep(step)

    return factory
