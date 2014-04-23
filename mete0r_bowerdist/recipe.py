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
import os.path

from mete0r_bowerdist import Build
from mete0r_bowerdist.assets import assets_save


class Recipe:

    def __init__(self, buildout, name, options):

        buildout_dir = buildout['buildout']['directory']
        parts_dir = buildout['buildout']['parts-directory']
        offline = bool_option(buildout['buildout'], 'offline')

        kwargs = {
            'proj_dir': options.get('project-directory') or buildout_dir,
            'dist_dir': (options.get('dist-directory') or
                         os.path.join(parts_dir, name)),
            'deps_dir': (options.get('dist-deps-directory')
                         or 'bower_component'),
            'no_deps': bool_option(options, 'no-deps'),
            'install_method': options.get('install-method') or 'symlink',
            'no_bower_install': bool_option(options, 'no-bower-install'),
            'bower_executable': options.get('bower-executable') or 'bower',
            'bower_offline': offline
        }

        self.build = Build(**kwargs)

        self.assets_dist_path = options.get('assets-dist')
        self.assets_proj_path = options.get('assets-proj')
        self.assets_deps_path = options.get('assets-deps')

    def install(self):
        assets = {}
        for distfile in self.build(assets):
            yield distfile['tgtpath']

        if self.assets_deps_path:
            assets_save(assets['deps'], self.assets_deps_path)
            yield self.assets_deps_path
        if self.assets_proj_path:
            assets_save(assets['proj'], self.assets_proj_path)
            yield self.assets_proj_path
        if self.assets_dist_path:
            assets_save(assets['dist'], self.assets_dist_path)
            yield self.assets_dist_path

    update = install


def bool_option(options, name, default_value=False):
    value = options.get(name, default_value)
    return {
        'true': True,
        'false': False,
        True: True,
        False: False
    }[value]


def uninstall(name, options):
    pass
