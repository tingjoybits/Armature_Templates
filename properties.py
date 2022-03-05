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

import bpy
from bpy.types import PropertyGroup, AddonPreferences
from bpy.props import *
from .functions import *


class AT_Properties(PropertyGroup):
    initialize: BoolProperty(
        name="Initialize",
        default=False
    )
    bone_category: EnumProperty(
        name="Category",
        items=bone_category_enum,
        description='Select the template category of the current mapping'
    )
    templates: EnumProperty(
        name="Template",
        description='Select the template for the bone mapping',
        items=template_list_enum,
        update=update_templates
    )
    mapping_category: BoolProperty(
        name="Mapping Category",
        description='Show the mapping category of the current template',
        default=False
    )
    bone_mapping: EnumProperty(
        name="Bone Mapping",
        description='Select the bone mapping of the template',
        items=bone_mapping_enum,
        update=update_apply_bone_mapping
    )
    ui_switching: BoolProperty(
        default=False
    )
    active_temp_item_list: IntProperty(
        name='Active item in the list',
        min=0, soft_min=0, max=100000, soft_max=10000, default=0
    )
    active_temp_category_list: IntProperty(
        name='Active item in the list',
        min=0, soft_min=0, max=100000, soft_max=10000, default=0
    )
    for i in range(32):
        exec((
            f"armature_layer_{str(i)}: "
            f"BoolProperty(name='Armature Layer {str(i)}', "
            "update=update_armature_layers, "
            "default=False)"
        ))

    @property
    def prefs(self):
        return bpy.context.preferences.addons[__package__].preferences


class AT_Preferences(AddonPreferences):
    bl_idname = __package__

    experimental: BoolProperty(
        name="Experimental Features",
        description='Turn on/off access to experimental features',
        default=False
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'experimental')


class Search_Bones(PropertyGroup):
    name: bpy.props.StringProperty(name="Source Name")
    bone: bpy.props.StringProperty(
        name="Target Bone",
        update=update_mapping_list
    )
    category: bpy.props.StringProperty(name="Category")


class Bone_names_coll(PropertyGroup):
    name: StringProperty(name="Bone Name")


class Item_List_Collection(PropertyGroup):
    name: StringProperty(name="Item")
    flag: BoolProperty(name="Flag", default=True)
    index: IntProperty(name="List Index")


class Armature_settings_coll(PropertyGroup):
    name: StringProperty(name="Name")
    template: StringProperty(name="Template")
    mapping: StringProperty(name="Mapping")
    bone_list: StringProperty(name="Bone List")
    mapping_data: StringProperty(name="Mapping Data")


classes = (
    AT_Properties,
    AT_Preferences,
    Search_Bones,
    Bone_names_coll,
    Item_List_Collection,
    Armature_settings_coll,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    wm = bpy.types.WindowManager
    wm.armature_templates_props = PointerProperty(type=AT_Properties)
    wm.at_search_list_props = CollectionProperty(type=Search_Bones)
    wm.at_bone_data_search_list = CollectionProperty(type=Bone_names_coll)
    wm.at_template_item_list = CollectionProperty(type=Item_List_Collection)
    wm.at_template_category_list = CollectionProperty(type=Item_List_Collection)
    armature = bpy.types.Armature
    armature.armtemp_settings = PointerProperty(type=Armature_settings_coll)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.WindowManager.armature_templates_props
    del bpy.types.WindowManager.at_search_list_props
    del bpy.types.WindowManager.at_bone_data_search_list
    del bpy.types.WindowManager.at_template_item_list
    del bpy.types.WindowManager.at_template_category_list
    del bpy.types.Armature.armtemp_settings
