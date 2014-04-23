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
import json


def assets_init():
    return {
        'css': [],
        'js': []
    }


def assets_add(assets, path):
    if path.endswith('.css'):
        assets['css'].append(path)
    elif path.endswith('.js'):
        assets['js'].append(path)


def assets_merge(*assets_list):
    assets = assets_init()
    for a in assets_list:
        assets['css'].extend(a['css'])
        assets['js'].extend(a['js'])
    return assets


def assets_dump(assets, f):
    json.dump(assets, f, indent=2, sort_keys=True)


def assets_save(assets, path):
    with file(path, 'w') as f:
        assets_dump(assets, f)


def assets_save_if(assets, path):
    if path:
        assets_save(assets, path)
