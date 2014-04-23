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
'''
Usage:
    bowerdist [--project-dir=<directory>]
              [--dist-dir=<directory>]
              [--dist-deps-dir=<directory> | --no-deps]
              [--install=<method>]
              [--no-bower-install]
              [--bower-executable=<path>]
              [--bower-offline]
              [--assets-dist=<path>]
              [--assets-deps=<path>]
              [--assets-proj=<path>]

Options:

    --project-dir=<dir>         the directory containing bower.json / .bowerrc

    --dist-dir=<dir>            the target directory (default: "build")
    --dist-deps-dir=<dir>       target dependencies directory, relative to
                                the target directory if not a absolute path
                                (default: "bower_components")

    --no-deps                   don't distribute dependencies
    --install=<method>          "copy", "link" or "symlink"(default)

    --no-bower-install          don't install missing bower components
    --bower-executable=<path>   path to bower executable (default: "bower")
    --bower-offline             use --offline in bower invocation

    --assets-dist=<path>        output assets file for distribution
    --assets-deps=<path>        output assets file for dependencies
    --assets=proj=<path>        output assets file for this project
'''
import logging

from docopt import docopt

from mete0r_bowerdist import Build
from mete0r_bowerdist.assets import assets_save_if


logger = logging.getLogger(__name__)


def main():
    args = docopt(__doc__)

    logging.basicConfig()

    kwargs = {
        'proj_dir': args['--project-dir'] or '.',
        'dist_dir': args['--dist-dir'] or 'build',
        'deps_dir': args['--dist-deps-dir'] or 'bower_components',
        'no_deps': args['--no-deps'],
        'install_method': args['--install'] or 'symlink',
        'no_bower_install': args['--no-bower-install'] or False,
        'bower_executable': args['--bower-executable'] or 'bower',
        'bower_offline': args['--bower-offline'] or False
    }
    build = Build(**kwargs)

    assets = {}
    for distfile in build(assets):
        print distfile['tgtpath']

    assets_save_if(assets['dist'], args['--assets-dist'])
    assets_save_if(assets['deps'], args['--assets-deps'])
    assets_save_if(assets['proj'], args['--assets-proj'])
