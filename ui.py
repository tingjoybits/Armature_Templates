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
import os
from bpy.types import Panel, Menu, PropertyGroup
from .functions import *


class AT_PT_Armature_Templates(Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_label = "Armature Templates"
    bl_idname = "AT_PT_armature_templates"
    bl_parent_id = "DATA_PT_skeleton"
    bl_options = {'DEFAULT_CLOSED'}

    template = ''
    armature = ''

    def __init__(self):
        at_initialization(__class__)
        ui_switch_select(__class__)
        json_file_path = get_template_path()
        self.file_data = get_json_data(json_file_path)
        self.template = props().templates

    @classmethod
    def poll(cls, context):
        return context.armature

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        wm = context.window_manager
        index_list = get_selected_bone_layers(context)
        load_bone_data_search_list(context, index_list)
        col = row.column()
        row = col.row(align=True)
        row.menu("AT_MT_Template_operations_menu", icon='THREE_DOTS')
        row.popover("POPOVER_PT_bone_layer_select", text='Bone List', icon='GROUP_BONE')
        row = col.row(align=True)
        row.prop(props(), 'templates', text='')
        row.operator("at.remove_template", text='', icon='REMOVE')
        row.prop(props(), 'bone_mapping', text='')
        icon = 'X' if props(context).bone_mapping == 'custom' else 'REMOVE'
        row.operator("at.remove_bone_mapping", text='', icon=icon)
        row = col.row(align=True)
        row.scale_x = 2
        row.prop(props(), 'bone_category', text='')
        sub_row = row.row(align=True)
        sub_row.operator("at.save_bone_mapping", text='Save', icon='EXPORT')
        sub_row.operator("at.load_bone_mapping", text='Load', icon='IMPORT')
        if not hasattr(self, 'file_data'):
            return None
        if not props(context).templates:
            return None
        row = col.row(align=True)
        if not props(context).mapping_category:
            text = 'Mapping [' + props(context).bone_category + ']'
            row.prop(props(), 'mapping_category', text=text, icon='DISCLOSURE_TRI_RIGHT')
            row.operator("at.select_category_bone_list", text='', icon='RESTRICT_SELECT_OFF')
            return None
        text = 'Mapping [' + props(context).bone_category + ']'
        row.prop(props(), 'mapping_category', text=text, icon='DISCLOSURE_TRI_DOWN')
        row.operator("at.select_category_bone_list", text='', icon='RESTRICT_SELECT_OFF')
        category_list = self.file_data.get(props(context).bone_category)
        if not category_list:
            return None
        search_props = context.window_manager.at_search_list_props
        box = col.box()
        for name in category_list:
            row = box.row(align=True)
            row.label(text=name)
            prop = search_props.get(name)
            if not prop:
                continue
            row.operator("at.map_custom_bone_name", text='', icon='OUTLINER_DATA_GP_LAYER').prop_name = name
            sub_row = row.row(align=True)
            sub_row.scale_x = 1.12
            sub_row.prop_search(prop, 'bone', wm, "at_bone_data_search_list", text="")
            row.operator("at.map_selected_bone", text='', icon='TRIA_LEFT').prop_name = name


class AT_MT_Metarigs(Menu):
    bl_label = "Meta-Rigs"
    bl_idname = "AT_MT_Metarigs_menu"

    def draw(self, context):
        layout = self.layout
        path = os.path.join(get_config_path(), "metarigs")
        validate_path(path)
        metarigs = get_file_list_names(path, full_name=False, extension='.py')
        for name in metarigs:
            layout.operator(
                "at.load_metarig",
                text=name,
                icon='OUTLINER_OB_ARMATURE'
            ).metarig_name = name
        layout.separator()
        layout.operator("at.save_metarig")
        if metarigs:
            layout.separator()
            layout.menu("AT_MT_Delete_Metarig_menu")


class AT_MT_Delete_Metarigs(Menu):
    bl_label = "Delete Meta-Rig"
    bl_idname = "AT_MT_Delete_Metarig_menu"

    def draw(self, context):
        layout = self.layout
        path = os.path.join(get_config_path(), "metarigs")
        validate_path(path)
        metarigs = get_file_list_names(path, full_name=False, extension='.py')
        for name in metarigs:
            layout.operator(
                "at.delete_metarig",
                text=name, icon='TRASH'
            ).metarig_name = name


class AT_MT_Template_Submenu(Menu):
    bl_label = "Template"
    bl_idname = "AT_MT_Template_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator(
            "at.create_template", icon='OUTLINER_OB_ARMATURE'
        ).edit = False
        layout.operator(
            "at.create_template", icon='POSE_HLT',
            text='Edit Template'
        ).edit = True
        layout.operator("at.rename_template", icon='OUTLINER_DATA_GP_LAYER')
        layout.operator("at.rename_mapping", icon='OUTLINER_DATA_GP_LAYER')
        layout.separator()
        layout.operator("at.guess_mapping_bones", icon='ZOOM_ALL')


class AT_MT_Template_Ops(Menu):
    bl_label = "Operations"
    bl_idname = "AT_MT_Template_operations_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator(
            "at.rename_bones", icon='ARROW_LEFTRIGHT',
            text="Rename Bones"
        )
        layout.separator()
        layout.menu("AT_MT_Template_menu")
        layout.separator()
        layout.menu("AT_MT_Metarigs_menu")
        layout.separator()
        layout.operator("at.fit_metarig", icon='OUTLINER_DATA_ARMATURE')  # ORIENTATION_NORMAL
        layout.operator("at.clean_imported_animation", icon='NORMALIZE_FCURVES')
        layout.separator()
        layout.operator("at.constrain_armature", icon='CONSTRAINT_BONE')
        layout.operator("at.clear_armature_constraints", icon='UNLINKED')
        layout.operator("at.bake_animation", icon='SEQ_LUMA_WAVEFORM')
        layout.separator()
        layout.operator("at.scale_armature", icon='EMPTY_DATA')
        layout.separator()
        layout.operator("at.browse_config_folder", icon='FILEBROWSER')
        if props(context).prefs.experimental:
            layout.separator()
            layout.menu("AT_MT_Experimental_menu")


class AT_MT_Experimental_Ops(Menu):
    bl_label = "Experimental"
    bl_idname = "AT_MT_Experimental_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("at.copy_layer_bones", icon='GROUP_BONE')
        layout.operator("at.mapping_from_ue2rigify", icon='ADD')


class POPOVER_PT_Bone_Layer_Select(Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'HEADER'
    bl_label = "Bone Layer Select"
    bl_idname = "POPOVER_PT_bone_layer_select"
    bl_description = "Select layers containing bones to work with"

    def draw(self, context):
        layout = self.layout
        layout.ui_units_x = 17
        top_row = layout.row()
        col = top_row.column(align=True)
        row = col.row(align=True)
        for i in range(32):
            if i == 16:
                row = col.row(align=True)
            if i == 8 or i == 24:
                row.separator()
            row.prop(props(), "armature_layer_" + str(i), text='', toggle=True)
        op = col.operator("at.select_bone_layers", text='Same Layer Selection')
        op.select = False
        op.invert = False
        op.same = True

        col = top_row.column(align=True)
        # col.operator("at.select_bone_layers", icon='FILEBROWSER')
        op = col.operator(
            "at.select_bone_layers", text='', icon='CHECKMARK'
        )
        op.select = True
        op.invert = False
        op.same = False
        op = col.operator(
            "at.select_bone_layers", text='', icon='CHECKBOX_DEHLT'
        )
        op.select = False
        op.invert = False
        op.same = False
        op = col.operator(
            "at.select_bone_layers", text='', icon='SELECT_SUBTRACT'
        )
        op.select = False
        op.invert = True
        op.same = False


classes = [
    AT_PT_Armature_Templates,
    AT_MT_Delete_Metarigs,
    AT_MT_Metarigs,
    AT_MT_Template_Submenu,
    AT_MT_Template_Ops,
    AT_MT_Experimental_Ops,
    POPOVER_PT_Bone_Layer_Select
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes[::-1]:
        bpy.utils.unregister_class(cls)
