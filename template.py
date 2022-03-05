
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

class Armature_Templates:
    template_data = dict([])
    active_category = ''
    bone_list = []

    @classmethod
    def initiate_properties(cls, source_list):
        cls.template_data.clear()
        cls.template_data['Base'] = []
        cls.active_category = 'Base'
        cls.bone_list = source_list

    @classmethod
    def get_category_items(cls, name=None):
        if not name:
            name = cls.active_category
        return cls.template_data.get(name)

    @classmethod
    def set_category_list(cls, item_list=[], name=None):
        if not name:
            name = cls.active_category
        cls.template_data[name] = item_list

    @classmethod
    def new_category(cls, name=None):
        if not name:
            if not cls.active_category:
                name = 'Base'
                cls.active_category = name
            else:
                name = cls.active_category
        cls.template_data[name] = []

    @classmethod
    def append_to_category(cls, item_list=[], name=None):
        if not name:
            name = cls.active_category
        cls.template_data[name] += item_list
        cls.bone_list = [b for b in cls.bone_list if b not in item_list]

    @classmethod
    def rename_category(cls, current_name, new_name):
        categories = [c for c in cls.template_data]
        for category in categories:
            if category != current_name:
                cls.template_data[category] = cls.template_data.pop(category)
                continue
            cls.template_data[new_name] = cls.template_data.pop(current_name)
        if current_name == cls.active_category:
            cls.active_category = new_name

    @classmethod
    def move_category_last(cls, name):
        cls.template_data[name] = cls.template_data.pop(name)
