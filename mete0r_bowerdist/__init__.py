# -*- coding: utf-8 -*-
#
#   bowerdist : build bower components into a directory
#   Copyright (C) 2014 mete0r <mete0r@sarangbang.or.kr>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
from contextlib import contextmanager
import json
import logging
import os.path
import shutil
import subprocess
import sys


logger = logging.getLogger(__name__)


def get_components_directory(root_directory):
    path = os.path.join(root_directory, '.bowerrc')
    if os.path.exists(path):
        with file(path) as f:
            bowerrc = json.load(f)
        return bowerrc['directory']
    return 'bower_components'


def load_component_from_directory(directory=''):
    path = os.path.join(directory, 'bower.json')
    with file(path) as f:
        component = json.load(f)
    component['_dir'] = directory
    return component


class Project:

    install_if_required = True
    bower_executable = 'bower'
    bower_offline = False

    def __init__(self, components_directory, root_component):
        self.components_directory = components_directory
        self.root_component = root_component

    @classmethod
    def load(cls, root_directory=''):
        components_directory = get_components_directory(root_directory)
        components_directory = os.path.join(root_directory,
                                            components_directory)
        root_component = load_component_from_directory(root_directory)
        return cls(components_directory=components_directory,
                   root_component=root_component)

    @property
    def root_directory(self):
        return self.root_component['_dir']

    def load_component(self, name):
        comp_dir = os.path.join(self.components_directory, name)
        if not os.path.exists(comp_dir) and self.install_if_required:
            bower_install(name,
                          root_directory=self.root_directory,
                          bower_executable=self.bower_executable,
                          offline=self.bower_offline)
        try:
            return load_component_from_directory(comp_dir)
        except Exception as e:
            logger.warning('can\'t load component %s (at %s): skipping', name,
                           comp_dir)
            logger.warning('An exception occurred: %s', e)
            return {
                'name': name,
                '_dir': comp_dir
            }

    def components(self):
        seen = set()
        for component in self.traverse_dependencies(self.root_component):
            if component['_dir'] not in seen:
                seen.add(component['_dir'])
                yield component

    def deps_components(self):
        for component in self.components():
            if component['_dir'] != self.root_component['_dir']:
                yield component

    def traverse_dependencies(self, component):
        # dependencies first
        for name in component.get('dependencies', {}):
            dep = self.load_component(name)
            for x in self.traverse_dependencies(dep):
                # prevent circular references
                if x['_dir'] != component['_dir']:
                    yield x

        # the component itself should be last
        yield component

    def get_component_distfiles(self, component):
        comp_dir = component['_dir']

        main = component.get('main', [])
        if isinstance(main, basestring):
            main = [main]

        for element_relpath in main:
            element_srcpath = os.path.join(comp_dir, element_relpath)
            element_srcpath = os.path.normpath(element_srcpath)
            if not os.path.exists(element_srcpath):
                logger.warning('%s is missing', element_srcpath)
            yield {
                'relpath': element_relpath,
                'srcpath': element_srcpath
            }

    def build_proj_component(self, destination):
        distfiles = list(self.get_component_distfiles(self.root_component))
        if len(distfiles) == 0:
            return
        elif len(distfiles) == 1:
            prefix = os.path.dirname(distfiles[0]['relpath'])
        else:
            commonprefix = os.path.commonprefix([d['relpath']
                                                 for d in distfiles])
            # TODO: make sure that prefix is a directory
            prefix = commonprefix

        for distfile in distfiles:
            relpath = distfile['relpath']
            relpath = os.path.relpath(relpath, prefix)
            tgtpath = os.path.join(destination, relpath)
            tgtpath = os.path.normpath(tgtpath)
            distfile['tgtpath'] = tgtpath
            yield distfile

    def build_deps_components(self, destination):
        for component in self.deps_components():
            comp_name = os.path.basename(component['_dir'])
            comp_dest = os.path.join(destination, comp_name)
            for distfile in self.build_component(component, comp_dest):
                yield distfile

    def build_component(self, component, destination):
        for distfile in self.get_component_distfiles(component):
            relpath = distfile['relpath']
            tgtpath = os.path.join(destination, relpath)
            tgtpath = os.path.normpath(tgtpath)
            distfile['tgtpath'] = tgtpath
            yield distfile


def Build(proj_dir='.',
          dist_dir='build',
          deps_dir='bower_component',
          no_deps=False,
          install_method='symlink',
          no_bower_install=False,
          bower_executable='bower',
          bower_offline=False):

    if not os.path.isabs(deps_dir):
        deps_dir = os.path.join(dist_dir, deps_dir)

    install = INSTALL_METHODS[install_method]

    project = Project.load(proj_dir)
    project.install_if_required = not no_bower_install
    project.bower_executable = bower_executable
    project.bower_offline = bower_offline

    deps_files = project.build_deps_components(deps_dir)
    proj_files = project.build_proj_component(dist_dir)

    def build(assets):
        from mete0r_bowerdist.assets import assets_init
        from mete0r_bowerdist.assets import assets_add
        from mete0r_bowerdist.assets import assets_merge
        assets['deps'] = assets_init()
        assets['proj'] = assets_init()

        if not no_deps:
            for distfile in deps_files:
                install(distfile)
                tgtpath = distfile['tgtpath']
                relpath = os.path.relpath(tgtpath, dist_dir)
                assets_add(assets['deps'], relpath)
                yield distfile

        for distfile in proj_files:
            install(distfile)
            tgtpath = distfile['tgtpath']
            relpath = os.path.relpath(tgtpath, dist_dir)
            assets_add(assets['proj'], relpath)
            yield distfile

        assets['dist'] = assets_merge(assets['deps'], assets['proj'])

    return build


def bower_install(name,
                  root_directory=None,
                  bower_executable='bower',
                  offline=False):
    args = [bower_executable, 'install', name]
    if offline:
        args.append('--offline')
    with chdir(root_directory):
        subprocess.check_call(args, stdout=sys.stderr)


@contextmanager
def chdir(wd=None):
    if wd is None:
        yield
        return

    cwd_backup = os.getcwd()
    try:
        os.chdir(wd)
        yield cwd_backup
    finally:
        os.chdir(cwd_backup)


def distfile_installer(f):
    def wrapped(distfile):
        srcpath = distfile['srcpath']
        tgtpath = distfile['tgtpath']
        d = os.path.dirname(tgtpath)
        if not os.path.exists(d):
            os.makedirs(d)
        if os.path.lexists(tgtpath) or os.path.exists(tgtpath):
            os.unlink(tgtpath)
        return f(srcpath, tgtpath)
    return wrapped


@distfile_installer
def symlink_distfile(srcpath, tgtpath):
    logger.info('symlinking to %s', tgtpath)
    d = os.path.dirname(tgtpath)
    symlink_path = os.path.relpath(srcpath, d)
    os.symlink(symlink_path, tgtpath)


@distfile_installer
def link_distfile(srcpath, tgtpath):
    logger.info('linking to %s', tgtpath)
    os.link(srcpath, tgtpath)


@distfile_installer
def copy_distfile(srcpath, tgtpath):
    logger.info('copying to %s', tgtpath)
    shutil.copy(srcpath, tgtpath)


INSTALL_METHODS = {
    'copy': copy_distfile,
    'link': link_distfile,
    'symlink': symlink_distfile
}
