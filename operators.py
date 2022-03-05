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
from bpy.types import Operator
from .functions import *
from .template import Armature_Templates as AT


class AT_OT_rename_skeleton_bones(Operator):
    bl_idname = "at.rename_bones"
    bl_label = "Rename Bones"
    bl_description = "Rename the active armature bones if they match in the template list as a defined naming convention"
    bl_options = {'REGISTER', 'UNDO'}

    target: bpy.props.EnumProperty(
        name="Target List",
        items=[
            ('LEFT', 'Left', 'Rename the left list of the bones'),
            ('RIGHT', 'Right', 'Rename the right list of the bones')
        ],
        default='RIGHT'
    )

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.label(text='', icon='TRACKING_BACKWARDS_SINGLE')
        row.prop(self, 'target', expand=True)
        row.label(text='', icon='TRACKING_FORWARDS_SINGLE')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=250)

    def execute(self, context):
        obj = context.active_object
        bone_data = get_mapped_bones_data(context)
        bone_names = [b.name for b in obj.data.bones]
        if self.target == 'LEFT':
            for name in bone_data:
                bone_name = bone_data.get(name)
                if name not in bone_names:
                    continue
                bone = obj.data.bones.get(name)
                if bone and bone_name:
                    bone.name = bone_name
        else:
            for name in bone_data:
                bone_name = bone_data.get(name)
                if bone_name not in bone_names:
                    continue
                bone = obj.data.bones.get(bone_name)
                if bone and name:
                    bone.name = name
        # update skin modifier for 3.0+
        for ob in bpy.data.objects:
            if ob.type == 'MESH':
                ob.data.update()
        self.report({'INFO'}, "Skeleton bones has been renamed.")
        return {'FINISHED'}


class AT_OT_save_bone_mapping(Operator):
    bl_idname = "at.save_bone_mapping"
    bl_label = "Save Bone Mapping"
    bl_description = "Save mapping file to a specified location"

    save_to: bpy.props.EnumProperty(
        name="Where to save",
        items=[
            ('DEFAULT', 'Config Folder', 'Save the mapping file to the user config folder of the add-on'),
            ('EXTERNAL', 'External Location', 'Save a separate file to a specified location')
        ],
        default='DEFAULT'
    )
    overwrite: bpy.props.BoolProperty(
        name="Overwrite",
        default=False
    )
    mapping: bpy.props.EnumProperty(
        name="Bone Mapping",
        items=bone_mapping_to_overwrite_enum
    )
    name: bpy.props.StringProperty(
        name="New Name",
        default='new'
    )

    def execute(self, context):
        if self.save_to == 'EXTERNAL':
            return {'FINISHED'}
        if self.name == '' and not self.overwrite:
            self.report({'ERROR'}, "The file name can't be empty!")
            return {'FINISHED'}

        file_name = check_extension(self.name)

        native_mapping_path = get_native_mapping_path(props(context).templates)
        config_mapping_path = get_config_mapping_path(props(context).templates)
        if self.overwrite:
            json_file_path = os.path.join(
                config_mapping_path, self.mapping + ".json"
            )
            if not os.path.isfile(json_file_path):
                json_file_path = os.path.join(
                    native_mapping_path, self.mapping + ".json"
                )
        else:
            json_file_path = os.path.join(config_mapping_path, file_name)

        save_data = get_mapped_bones_data(context)
        save_json_data(json_file_path, save_data)
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, 'save_to', expand=True)
        if self.save_to == 'EXTERNAL':
            row = layout.row()
            row.operator('at.save_bone_mapping_to', text='Browse', icon='FILEBROWSER')
            return None
        row = layout.row()
        row.prop(self, 'overwrite')
        subrow = row.row()
        subrow.enabled = self.overwrite
        subrow.scale_x = 1.5
        subrow.prop(self, 'mapping', text='')
        row = layout.row()
        row.enabled = not self.overwrite
        row.label(text='New Name')
        subrow = row.row()
        subrow.scale_x = 1.5
        subrow.prop(self, "name", text='')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=250)


class AT_OT_load_bone_mapping(Operator):
    bl_idname = "at.load_bone_mapping"
    bl_label = "Load Bone Mapping"
    bl_description = "Load template mapping from a specified file"

    directory: bpy.props.StringProperty(
        subtype="DIR_PATH"
    )
    filename: bpy.props.StringProperty(
        subtype="FILE_NAME",
    )
    filepath: bpy.props.StringProperty(
        subtype="FILE_PATH"
    )
    browse_path: bpy.props.EnumProperty(
        name="Browse Path",
        items=[
            ('CONFIG', 'User Config', 'Browse to the user config directory', 0),
            ('NATIVE', 'Native', 'Browse to the native directory of the add-on installation', 1),
            ('BLEND', 'Blend File', 'Browse to the directory of the current blend file', 2),
        ],
        update=update_browse_path,
        default=0
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.use_property_split = True
        col.prop(self, 'browse_path', expand=True)

    def invoke(self, context, event):
        self.filename = ".json"
        self.directory = os.path.join(get_config_path(), "bone_mapping")
        validate_path(self.directory)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if not self.filepath.endswith(".json"):
            msg = "Selected file has to be a .json file"
            self.report({'ERROR'}, msg)
            return {'FINISHED'}
        props(context)['bone_mapping'] = 0
        file_data = get_json_data(self.filepath)
        apply_bone_mapping_data(context, file_data)
        redraw_area('PROPERTIES')
        return {'FINISHED'}


class AT_OT_map_selected_bone(Operator):
    bl_idname = "at.map_selected_bone"
    bl_label = "Map Selected Bone"
    bl_description = "Map a link to the bone that currently in the active selection"

    prop_name: bpy.props.StringProperty()

    def execute(self, context):
        if self.prop_name == '':
            return {'FINISHED'}
        obj = context.active_object
        mode = context.mode.split('_')[0]
        if mode == 'POSE':
            bones = obj.data.bones
        else:
            bones = obj.data.edit_bones
        if not bones.active:
            return {'FINISHED'}
        search_props = context.window_manager.at_search_list_props
        prop = search_props.get(self.prop_name)
        prop.bone = bones.active.name
        redraw_area('PROPERTIES')
        return {'FINISHED'}


class AT_OT_map_custom_bone_name(Operator):
    bl_idname = "at.map_custom_bone_name"
    bl_label = "Map Custom Name"
    bl_description = "Type a name in the popup window to map a custom bone"

    prop_name: bpy.props.StringProperty()
    custom_name: bpy.props.StringProperty(name="Custom Name")

    def invoke(self, context, event):
        search_props = context.window_manager.at_search_list_props
        self.prop = search_props.get(self.prop_name)
        self.custom_name = self.prop.bone
        return context.window_manager.invoke_props_dialog(self, width=250)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.use_property_split = True
        col.prop(self, 'custom_name')

    def execute(self, context):
        if self.prop_name == '':
            return {'FINISHED'}
        self.prop.bone = self.custom_name
        redraw_area('PROPERTIES')
        return {'FINISHED'}


class AT_OT_save_bone_mapping_to(Operator):
    bl_idname = "at.save_bone_mapping_to"
    bl_label = "Save Bone Mapping"
    bl_description = "Browse folders to save bone mapping file"

    directory: bpy.props.StringProperty(
        subtype="DIR_PATH"
    )
    filename: bpy.props.StringProperty(
        subtype="FILE_NAME",
        default="new mapping"
    )
    filepath: bpy.props.StringProperty(
        subtype="FILE_PATH"
    )
    browse_path: bpy.props.EnumProperty(
        name="Browse Path",
        items=[
            ('CONFIG', 'User Config', 'Browse to the user config directory', 0),
            ('NATIVE', 'Native', 'Browse to the native directory of the add-on installation', 1),
            ('BLEND', 'Blend File', 'Browse to the directory of the current blend file', 2),
        ],
        update=update_browse_path,
        default=2
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.use_property_split = True
        col.prop(self, 'browse_path', expand=True)

    def invoke(self, context, event):
        self.filename = "new mapping"
        if bpy.data.filepath:
            self.directory = os.path.dirname(bpy.data.filepath)
        else:
            self.directory = os.path.expanduser('~')
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if not self.filename:
            msg = "The file name is empty"
            self.report({'ERROR'}, msg)
            return {'FINISHED'}
        if not self.filepath.endswith(".json"):
            self.filepath += ".json"
        save_data = get_mapped_bones_data(context)
        save_json_data(self.filepath, save_data)
        msg = "The mapping file has been saved to: " + self.filepath
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class AT_OT_remove_bone_mapping(Operator):
    bl_idname = "at.remove_bone_mapping"
    bl_label = "Remove Bone Mapping"
    bl_description = "Remove the current file of the bone mapping"

    def invoke(self, context, event):
        if props(context).bone_mapping == 'custom':
            update_apply_bone_mapping(props(context), context)
            return {'FINISHED'}
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        native_path = get_native_mapping_path(props(context).templates)
        config_path = get_config_mapping_path(props(context).templates)
        file_path = os.path.join(config_path, props(context).bone_mapping + ".json")
        if os.path.isfile(file_path):
            os.remove(file_path)
            props(context)['bone_mapping'] = 0
            return {'FINISHED'}

        file_path = os.path.join(native_path, props(context).bone_mapping + ".json")
        if os.path.isfile(file_path):
            props(context)['bone_mapping'] = 0
            os.remove(file_path)
            return {'FINISHED'}

        msg = "Armature Templates: The mapping file '" + props(context).bone_mapping + "' does not exist"
        self.report({'ERROR'}, msg)
        return {'FINISHED'}


class AT_OT_create_template_category(Operator):
    bl_idname = "at.create_template_category"
    bl_label = "Create Template Category"
    bl_description = "Create a new category in the template for bones"

    name: bpy.props.StringProperty(name="Name")

    def execute(self, context):
        if AT.template_data.get(self.name):
            return {'FINISHED'}
        AT.new_category(self.name)
        return {'FINISHED'}


class AT_OT_remove_template_category(Operator):
    bl_idname = "at.remove_template_category"
    bl_label = " Remove Template Category"
    bl_description = "Remove the category in the template and move the containing bones to the source list"

    name: bpy.props.StringProperty(name="Name")

    def execute(self, context):
        AT.template_data.pop(self.name)
        AT.bone_list = evaluate_bone_list(
            context, context.active_object, AT.template_data
        )
        set_template_item_list(AT.bone_list)
        if self.name == AT.active_category:
            set_template_category_list([])
        return {'FINISHED'}


class AT_OT_template_categories(Operator):
    bl_idname = "at.template_categories"
    bl_label = "Template Category"
    bl_description = "Select the category to append items in it"

    name: bpy.props.StringProperty(name="Name")

    def execute(self, context):
        AT.active_category = self.name
        set_template_category_list(AT.get_category_items())
        return {'FINISHED'}


class AT_OT_add_selected_to_template(Operator):
    bl_idname = "at.add_selected_to_template"
    bl_label = "Add"
    bl_description = "Add selected items in the active category"

    def execute(self, context):
        if not AT.bone_list:
            return {'FINISHED'}
        if not AT.get_category_items():
            AT.new_category()
        item_list = context.window_manager.at_template_item_list
        add_list = [i.name for i in item_list if i.flag]
        if not add_list:
            add_list = [item_list[props(context).active_temp_item_list].name]
        AT.append_to_category(item_list=add_list)
        while props(context).active_temp_item_list > len(AT.bone_list) - 1:
            props(context).active_temp_item_list -= 1
            if props(context).active_temp_item_list == 0:
                break
        set_template_item_list(AT.bone_list)
        set_template_category_list(AT.get_category_items())
        return {'FINISHED'}


class AT_OT_add_custom_bone_name(Operator):
    bl_idname = "at.add_custom_bone_name"
    bl_label = "Add Custom Bone Name"
    bl_description = "Add custom name to the bone list of the active template category"

    name: bpy.props.StringProperty(name="Name")

    def execute(self, context):
        if not self.name or self.name in AT.template_data:
            return {'FINISHED'}
        # if not AT.bone_list:
        #     return {'FINISHED'}
        if not AT.get_category_items():
            AT.new_category()
        AT.append_to_category(item_list=[self.name])
        # while props(context).active_temp_item_list > len(AT.bone_list) - 1:
        #     props(context).active_temp_item_list -= 1
        #     if props(context).active_temp_item_list == 0:
        #         break
        # set_template_item_list(AT.bone_list)
        set_template_category_list(AT.get_category_items())
        return {'FINISHED'}


class WM_OT_Copy_to_Clipboard(Operator):
    bl_label = 'Copy to Clipboard'
    bl_idname = 'wmo.copy_to_clipboard'
    bl_description = "Copy text to clipboard buffer"

    text: bpy.props.StringProperty()

    def execute(self, context):
        context.window_manager.clipboard = self.text
        self.report({'INFO'}, 'Copy ' + self.text)
        return {'FINISHED'}


class AT_OT_remove_selected_from_template_category(Operator):
    bl_idname = "at.remove_selected_from_template_category"
    bl_label = "Remove"
    bl_description = "Remove selected items from the active category"

    def execute(self, context):
        item_list = context.window_manager.at_template_category_list
        new_list = [i.name for i in item_list if not i.flag]
        if not item_list:
            return {'FINISHED'}
        if len(new_list) == len(item_list):
            active = item_list[props(context).active_temp_category_list].name
            new_list = [i.name for i in item_list if i.name != active]
        if AT.get_category_items():
            AT.set_category_list(item_list=new_list)
        AT.bone_list = evaluate_bone_list(
            context, context.active_object, AT.template_data
        )
        while props(context).active_temp_category_list > len(new_list) - 1:
            props(context).active_temp_category_list -= 1
            if props(context).active_temp_category_list == 0:
                break

        set_template_item_list(AT.bone_list)
        set_template_category_list(new_list)
        return {'FINISHED'}


class AT_OT_remove_all_from_template_category(Operator):
    bl_idname = "at.remove_all_from_template_category"
    bl_label = "Remove All from Category"
    bl_description = "Remove all items from the active category"

    def execute(self, context):
        AT.template_data[AT.active_category].clear()
        AT.bone_list = evaluate_bone_list(
            context, context.active_object, AT.template_data
        )
        set_template_item_list(AT.bone_list)
        set_template_category_list([])
        return {'FINISHED'}


class AT_OT_move_list_items_up(Operator):
    bl_idname = "at.move_list_items_up"
    bl_label = "Move Up"
    bl_description = (
        "Shift the selected items up in the active category list. "
        "(Ctrl + Click - Move selected to the top)"
    )

    def invoke(self, context, event):
        self.ctrl_press = False
        if event.ctrl:
            self.ctrl_press = True
        return self.execute(context)

    def execute(self, context):
        item_list = context.window_manager.at_template_category_list
        if not item_list:
            return {'FINISHED'}
        bones = AT.get_category_items()
        move_items = [i.name for i in item_list if i.flag]
        if not move_items:
            if props(context).active_temp_category_list == 0:
                return {'FINISHED'}
            active = item_list[props(context).active_temp_category_list].name
            if self.ctrl_press:
                move_list_items_up_top(bones, [active])
                props(context).active_temp_category_list = 0
            else:
                move_list_item_up(bones, active)
                props(context).active_temp_category_list -= 1
        elif move_items[0] != bones[0]:
            if self.ctrl_press:
                move_list_items_up_top(bones, move_items)
            else:
                for n in move_items:
                    move_list_item_up(bones, n)
        else:
            return {'FINISHED'}
        set_template_category_list(bones, flag_list=move_items)
        return {'FINISHED'}


class AT_OT_move_list_items_down(Operator):
    bl_idname = "at.move_list_items_down"
    bl_label = "Move Down"
    bl_description = (
        "Shift the selected items down in the active category list. "
        "(Ctrl + Click - Move selected to the bottom)"
    )

    def invoke(self, context, event):
        self.ctrl_press = False
        if event.ctrl:
            self.ctrl_press = True
        return self.execute(context)

    def execute(self, context):
        item_list = context.window_manager.at_template_category_list
        if not item_list:
            return {'FINISHED'}
        bones = AT.get_category_items()
        move_items = [i.name for i in item_list if i.flag]
        if not move_items:
            if props(context).active_temp_category_list == len(bones) - 1:
                return {'FINISHED'}
            active = item_list[props(context).active_temp_category_list].name
            if self.ctrl_press:
                move_list_items_down_bottom(bones, [active])
                props(context).active_temp_category_list = len(bones) - 1
            else:
                move_list_item_down(bones, active)
                props(context).active_temp_category_list += 1
        elif move_items[-1] != bones[-1]:
            if self.ctrl_press:
                move_list_items_down_bottom(bones, move_items)
            else:
                for n in reversed(move_items):
                    move_list_item_down(bones, n)
        else:
            return {'FINISHED'}
        set_template_category_list(bones, flag_list=move_items)
        return {'FINISHED'}


class AT_OT_Select_UList_Items(Operator):
    bl_idname = "at.select_list_items"
    bl_label = "Select Items"
    bl_description = "Select, deselect or invert all list items"

    select: bpy.props.BoolProperty(
        name="Select",
        default=False
    )
    invert: bpy.props.BoolProperty(
        name="Invert",
        default=False
    )
    list_type: bpy.props.EnumProperty(
        name="List Type",
        items=[
            ('ITEMS', 'Items', ''),
            ('CATEGORY', 'Category', '')
        ],
        default='ITEMS'
    )

    def execute(self, context):
        if self.list_type == 'ITEMS':
            item_list = context.window_manager.at_template_item_list
        elif self.list_type == 'CATEGORY':
            item_list = context.window_manager.at_template_category_list
        select_ulist_items(item_list, select=self.select, invert=self.invert)
        return {'FINISHED'}


class AT_OT_Select_Bone_Layers(Operator):
    bl_idname = "at.select_bone_layers"
    bl_label = "Select Layers"
    bl_description = "Select, deselect or invert layers"

    select: bpy.props.BoolProperty(
        name="Select",
        default=False
    )
    invert: bpy.props.BoolProperty(
        name="Invert",
        default=False
    )
    same: bpy.props.BoolProperty(
        name="Same Selected Layers",
        default=False
    )

    def execute(self, context):
        if self.same:
            armature = context.active_object
            layer_bools = [layer for layer in armature.data.layers]
            set_select_bone_layers(layer_bools)
        elif self.invert:
            selected_list = get_selected_bone_layers(context)
            invert_bools = [(i not in selected_list) for i in range(32)]
            set_select_bone_layers(invert_bools)
        else:
            set_bone_list_layer(range(32), value=self.select)
        return {'FINISHED'}


class AT_OT_rename_template_category(Operator):
    bl_idname = "at.rename_template_category"
    bl_label = "Rename Category"
    bl_description = "Change the name of the active category"

    current_name: bpy.props.StringProperty(name="Current Name")
    new_name: bpy.props.StringProperty(name="New Name")

    def invoke(self, context, event):
        self.new_name = self.current_name
        return context.window_manager.invoke_props_dialog(self, width=250)

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.prop(self, 'new_name')

    def execute(self, context):
        if self.new_name == '':
            self.report({'ERROR'}, "The name can't be empty!")
            return {'FINISHED'}
        AT.rename_category(self.current_name, self.new_name)
        return {'FINISHED'}


class AT_OT_move_template_category_down(Operator):
    bl_idname = "at.move_template_category_down"
    bl_label = "Move Category Down"
    bl_description = "Move the category to the very bottom position"

    name: bpy.props.StringProperty(name="Name")

    def execute(self, context):
        AT.move_category_last(self.name)
        return {'FINISHED'}


class TEMPLATE_UL_Armature_bones(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        draw_ulist_item(self, layout, item, active_data, active_propname)


class TEMPLATE_UL_Category_bones(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        draw_ulist_item(self, layout, item, active_data, active_propname)


class POPUP_OT_Create_Template(Operator):
    bl_label = 'Create Template'
    bl_idname = 'at.create_template'
    bl_description = "Make a new .json file as a template based on the naming convetion of the active armature"

    new_category: bpy.props.StringProperty(
        name="Bone Category Name",
        default="New Category"
    )
    template_name: bpy.props.StringProperty(
        name="Template Name",
        default="new template"
    )
    custom_name: bpy.props.StringProperty(
        name="Custom Bone Name",
        default="Custom Bone Name"
    )
    edit: bpy.props.BoolProperty(
        default=False
    )

    def invoke(self, context, event):
        obj = context.active_object
        bones = get_bones_in_selected_layers(context, obj)  # obj.data.bones
        AT.initiate_properties([b.name for b in bones])
        props(context).active_temp_item_list = 0
        props(context).active_temp_category_list = 0
        if self.edit:
            AT.template_data = get_json_data(get_template_path())
            AT.active_category = [c for c in AT.template_data][0]
            AT.bone_list = evaluate_bone_list(
                context, context.active_object, AT.template_data
            )
            if is_native_template_path(props(context).templates):
                self.template_name = props(context).templates + '_edited'
            else:
                self.template_name = props(context).templates
        set_template_item_list(AT.bone_list)
        set_template_category_list(AT.get_category_items())
        return context.window_manager.invoke_props_dialog(self, width=450)

    def draw(self, context):
        wm = context.window_manager
        layout = self.layout

        row = layout.row(align=True)
        col = row.column()

        row = col.row(align=True)
        col1 = row.column()
        col1.ui_units_x = 50
        row1 = col1.row(align=True)
        row1.operator("at.add_selected_to_template", icon='FORWARD')
        op = row1.operator(
            "at.select_list_items", text='', icon='CHECKMARK'
        )
        op.select = True
        op.list_type = 'ITEMS'
        op.invert = False
        op = row1.operator(
            "at.select_list_items", text='', icon='CHECKBOX_DEHLT'
        )
        op.select = False
        op.list_type = 'ITEMS'
        op.invert = False
        op = row1.operator(
            "at.select_list_items", text='', icon='SELECT_SUBTRACT'
        )
        op.select = False
        op.list_type = 'ITEMS'
        op.invert = True
        row1.separator()
        row1 = col1.row(align=True)
        row1.template_list(
            "TEMPLATE_UL_Armature_bones", "",
            wm, "at_template_item_list", props(), "active_temp_item_list",
            rows=19
        )
        row1.separator()
        row1 = col1.row(align=True)
        row1.prop(self, 'custom_name', text='')
        row1.operator(
            "at.add_custom_bone_name", text='', icon='FORWARD'
        ).name = self.custom_name
        row1.separator()
        # Second Column
        col2 = row.column()
        col2.ui_units_x = 50
        row2 = col2.row(align=True)
        if AT.template_data.get(AT.active_category):
            row2.operator("at.remove_all_from_template_category", text='', icon='X')
        row2.operator("at.remove_selected_from_template_category", icon='BACK')
        op = row2.operator(
            "at.select_list_items", text='', icon='CHECKMARK'
        )
        op.select = True
        op.list_type = 'CATEGORY'
        op.invert = False
        op = row2.operator(
            "at.select_list_items", text='', icon='CHECKBOX_DEHLT'
        )
        op.select = False
        op.list_type = 'CATEGORY'
        op.invert = False
        op = row2.operator(
            "at.select_list_items", text='', icon='SELECT_SUBTRACT'
        )
        op.select = False
        op.list_type = 'CATEGORY'
        op.invert = True
        row2.operator("at.move_list_items_up", text='', icon='TRIA_UP')
        row2.operator("at.move_list_items_down", text='', icon='TRIA_DOWN')
        for category in AT.template_data:
            row2 = col2.row(align=True)
            is_active = True if AT.active_category == category else False
            icon = 'DISCLOSURE_TRI_DOWN' if is_active else 'DISCLOSURE_TRI_RIGHT'
            row2.operator(
                "at.template_categories", text=category, icon=icon,
                depress=is_active
            ).name = category
            row2.operator(
                "at.rename_template_category", text='', icon='OUTLINER_DATA_GP_LAYER',
                depress=is_active
            ).current_name = category
            row2.operator(
                "at.move_template_category_down", text='', icon='TRIA_DOWN_BAR',
                depress=is_active
            ).name = category
            subrow = row2.row(align=False)
            subrow.emboss = 'PULLDOWN_MENU'
            subrow.operator(
                "at.remove_template_category", text='', icon='REMOVE'
            ).name = category
            if is_active:
                row2 = col2.row(align=False)
                row2.template_list(
                    "TEMPLATE_UL_Category_bones", "",
                    wm, "at_template_category_list", props(), "active_temp_category_list",
                    rows=17
                )
        row2 = col2.row(align=False)
        row2.prop(self, 'new_category', text='')
        subrow = row2.row(align=False)
        subrow.emboss = 'PULLDOWN_MENU'
        op = subrow.operator("at.create_template_category", text='', icon='ADD')
        op.name = self.new_category

        row = col.row(align=True)
        row.separator()
        row = col.row(align=True)
        row.prop(self, 'template_name')

    def execute(self, context):
        if self.template_name == '':
            self.report({'ERROR'}, "The name can't be empty!")
            return {'FINISHED'}
        template_name = check_extension(self.template_name)
        base_name = base_file_name(self.template_name)
        if self.edit:
            location, template_path = get_template_path(return_type=True)
            if base_name == props(context).templates:
                save_json_data(template_path, AT.template_data)
                save_custom_file(base_name, AT.template_data, location=location)
                props(context)['bone_category'] = 0
                initiate_search_props()
                redraw_area('PROPERTIES')
                return {'FINISHED'}
        config_templates_path = os.path.join(get_config_path(), "templates")
        config_file_path = os.path.join(config_templates_path, template_name)
        save_json_data(config_file_path, AT.template_data)
        # save blank custom mapping
        save_custom_file(base_name, AT.template_data)
        return {'FINISHED'}


class AT_OT_remove_template(Operator):
    bl_idname = "at.remove_template"
    bl_label = "Remove Template"
    bl_description = "Delete the current template file, can't be undone"

    remove_mapping_files: bpy.props.BoolProperty(
        name='Yes',
        description='Aggre to delete all mapping files that associated with the current template',
        default=False
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=350)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text='Delete all mapping files that associated with the current template?')
        row = layout.row()
        row.alignment = 'CENTER'
        row.prop(self, 'remove_mapping_files')

    def execute(self, context):
        location, template_file_path = get_template_path(return_type=True)
        template = props(context).templates
        if os.path.isfile(template_file_path):
            os.remove(template_file_path)
            props(context)['templates'] = 0
        else:
            msg = "Armature Templates: The template file '" + template + "' does not exist"
            self.report({'ERROR'}, msg)
            return {'FINISHED'}

        initiate_search_props()
        if not self.remove_mapping_files:
            redraw_area('PROPERTIES')
            return {'FINISHED'}

        mapping_native_path = get_native_mapping_path(template)
        mapping_config_path = get_config_mapping_path(template)
        import shutil
        if os.path.isdir(mapping_config_path):
            shutil.rmtree(mapping_config_path)
            props(context)['bone_mapping'] = 0
        if os.path.isfile(mapping_native_path) and location == 'NATIVE':
            shutil.rmtree(mapping_native_path)
            props(context)['bone_mapping'] = 0
        redraw_area('PROPERTIES')
        return {'FINISHED'}


class AT_OT_rename_template(Operator):
    bl_idname = "at.rename_template"
    bl_label = "Rename Template"
    bl_description = "Change the name of the current template file"

    new_name: bpy.props.StringProperty(
        name="New Name"
    )

    def invoke(self, context, event):
        self.new_name = props(context).templates
        return context.window_manager.invoke_props_dialog(self, width=250)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, 'new_name')

    def execute(self, context):
        location, template_file_path = get_template_path(return_type=True)
        template = props(context).templates
        mapping_path = get_mapping_path(template, location=location)
        if os.path.isfile(template_file_path):
            new_name = check_extension(self.new_name)
            new_file = os.path.join(os.path.dirname(template_file_path), new_name)
            os.rename(template_file_path, new_file)
        else:
            msg = "Armature Templates: The template file '" + template + "' does not exist"
            self.report({'ERROR'}, msg)
            return {'FINISHED'}

        initiate_search_props()
        if not os.path.isdir(mapping_path):
            redraw_area('PROPERTIES')
            return {'FINISHED'}
        parent_folder = os.path.abspath(os.path.join(mapping_path, '..'))
        new_template_folder = base_file_name(self.new_name)
        new_path = os.path.join(parent_folder, new_template_folder)
        os.rename(mapping_path, new_path)
        redraw_area('PROPERTIES')
        return {'FINISHED'}


class AT_OT_rename_mapping(Operator):
    bl_idname = "at.rename_mapping"
    bl_label = "Rename Mapping"
    bl_description = "Change the name of the current mapping file"

    new_name: bpy.props.StringProperty(
        name="New Name"
    )

    def invoke(self, context, event):
        self.new_name = props(context).bone_mapping
        return context.window_manager.invoke_props_dialog(self, width=250)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, 'new_name')

    def execute(self, context):
        location, template_file_path = get_template_path(return_type=True)
        mapping = check_extension(props(context).bone_mapping)
        mapping_path = get_mapping_path(props(context).templates, location=location)
        mapping_file_path = os.path.join(mapping_path, mapping)
        if not os.path.isfile(mapping_file_path):
            mapping_file_path = os.path.join(
                get_config_mapping_path(props(context).templates), mapping)
        if os.path.isfile(mapping_file_path):
            new_name = check_extension(self.new_name)
            new_file = os.path.join(mapping_path, new_name)
            os.rename(mapping_file_path, new_file)
        else:
            msg = "Armature Templates: The template file '" + props(context).bone_mapping + "' does not exist"
            self.report({'ERROR'}, msg)
            return {'FINISHED'}

        redraw_area('PROPERTIES')
        return {'FINISHED'}


class AT_OT_guess_mapping_bones(Operator):
    bl_idname = "at.guess_mapping_bones"
    bl_label = "Guess Mapping"
    bl_description = "Search for bone names of the active armature and try to match them in the naming convention of the current template"

    search_source: bpy.props.BoolProperty(
        name='Invert Search Source',
        description='Try a different search method for better result',
        default=False
    )
    category_only: bpy.props.BoolProperty(
        name='Current Category Only',
        description='Remap in the current category only',
        default=False
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=250)

    def find_number(self, find_string, source_name):
        import re
        if not find_string.isnumeric():
            return False
        source_parts = re.findall(r'\d+|[A-Za-z]+', source_name.lower())
        for sp in source_parts:
            if sp.isnumeric() and int(find_string) == int(sp):
                return True

    def get_bones_match_data(self, bones):
        import re
        template_data = get_json_data(get_template_path())
        bones_match = {}
        for category, i, name in iterate_template_data(template_data):
            if self.category_only and props().bone_category != category:
                continue
            bones_match[name] = {}
            for b in bones:
                if self.search_source:
                    search_name = b.name
                    source_name = name
                else:
                    search_name = name
                    source_name = b.name
                n_parts = re.findall(r'\d+|[A-Za-z]+', search_name)
                found_count = 0
                found_parts = []
                for p in n_parts:
                    if not text_lookup(p.lower(), source_name.lower()) and\
                            not self.find_number(p, source_name):
                        continue
                    if p.lower() == 'l' or p.lower() == 'r':
                        source_parts = re.findall(r'\d+|[A-Za-z]+', source_name.lower())
                        if p.lower() not in source_parts:
                            continue
                    found_count += 1
                    found_parts.append(p)
                bones_match[name][b.name] = [found_count] + found_parts
        return bones_match

    def get_mapping_data(self, bones):
        mapping_data = {}
        bones_match = self.get_bones_match_data(bones)
        for name in bones_match:
            biggest_match = 0
            bone_match = ''
            for b in bones:
                match_list = bones_match[name].get(b.name)
                match_count = match_list[0]
                match_parts = [p for i, p in enumerate(match_list) if i != 0]
                if match_count <= 2:
                    is_irrelevant = 0
                    for part in match_parts:
                        if part.lower() == 'l' or\
                                part.lower() == 'r' or\
                                part.isnumeric():
                            is_irrelevant += 1
                    if is_irrelevant == match_count:
                        continue
                if biggest_match < match_count:
                    biggest_match = match_count
                    bone_match = b.name
                if biggest_match == match_count:
                    if len(bone_match) > len(b.name):
                        bone_match = b.name
            mapping_data[name] = bone_match
        return mapping_data

    def execute(self, context):
        bones = get_bones_in_selected_layers(context, None)
        mapping_data = self.get_mapping_data(bones)
        apply_bone_mapping_data(context, mapping_data)
        redraw_area('PROPERTIES')
        return {'FINISHED'}


class AT_OT_fit_metarig(Operator):
    bl_idname = "at.fit_metarig"
    bl_label = "Fit Meta-Rig"
    bl_description = "Choose the skeleton rig to align and to place the active armature bones, according to the template mapping"
    bl_options = {'REGISTER', 'UNDO'}

    to_skeleton: bpy.props.EnumProperty(
        name="Fit to Skeleton",
        items=scene_armatures_enum,
        default=0
    )
    edit_armature: bpy.props.BoolProperty(
        name="Edit Meta-Rig Armature",
        default=False
    )
    create_twist_bones: bpy.props.BoolProperty(
        name="Twist Bones",
        description=(
            'Create the twist bones for arms and legs in the meta-rig. '
            'Makes this armature unusable for generating the rig'
        ),
        default=False
    )
    leg_twist_bones_number: bpy.props.IntProperty(
        name="Leg Bones",
        description='The amount of twist bones per limb',
        min=1, max=9, soft_min=1, soft_max=9,
        default=1
    )
    arm_twist_bones_number: bpy.props.IntProperty(
        name="Arm Bones",
        description='The amount of twist bones per limb',
        min=1, max=9, soft_min=1, soft_max=9,
        default=1
    )
    subdivide_spine_bones: bpy.props.IntProperty(
        name="Add Spine Bones",
        description='Add spine bones by subdividing them, starting from the first bone in the chain',
        min=0, max=4, soft_min=0, soft_max=4,
        default=0
    )
    remove_heel_bones: bpy.props.BoolProperty(
        name="Heel Bones",
        default=False
    )
    remove_pelvis_bones: bpy.props.BoolProperty(
        name="Pelvis Bones",
        default=False
    )
    remove_breast_bones: bpy.props.BoolProperty(
        name="Breast Bones",
        default=False
    )
    remove_face_bones: bpy.props.BoolProperty(
        name="Face Bones",
        default=False
    )
    remove_palm_bones: bpy.props.BoolProperty(
        name="Palm Bones",
        default=False
    )
    reorient_y: bpy.props.BoolProperty(
        name="Reorient Y",
        description='Fix bone orientation in the Y axis. Used for skeleton imported with different bone orientation',
        default=False
    )
    recalculate_roll: bpy.props.BoolProperty(
        name="Recalculate Roll",
        description='Recalculate bone rolls to set the primary rotation of the limbs in X axis',
        default=False
    )
    rename: bpy.props.BoolProperty(
        name="Rename Meta-Rig",
        default=False
    )
    new_name: bpy.props.StringProperty(
        name="New Name",
        default="root"
    )
    rigify_options: bpy.props.BoolProperty(
        name="Rigify Options",
        default=False
    )
    arm_limb_segments: bpy.props.IntProperty(
        name="Arm Limb Segments",
        description='Number of limb segments. The two segments means that limb contains one twist bone',
        min=1, max=10,
        default=2
    )
    leg_limb_segments: bpy.props.IntProperty(
        name="Leg Limb Segments",
        description='Number of limb segments. The two segments means that limb contains one twist bone',
        min=1, max=10,
        default=2
    )
    arm_rotation_axis: bpy.props.EnumProperty(
        name="Arm Rotation Axis",
        description='Set primary rotation axis of the limb',
        items=[(axis, axis.capitalize(), 'Rotation Axis') for axis in ('automatic', 'x', 'z')]
    )
    leg_rotation_axis: bpy.props.EnumProperty(
        name="Leg Rotation Axis",
        description='Set primary rotation axis of the limb',
        items=[(axis, axis.capitalize(), 'Rotation Axis') for axis in ('automatic', 'x', 'z')]
    )
    palm_rotation_axis: bpy.props.EnumProperty(
        name="Finger Rotation Axis",
        description='Set primary rotation axis of fingers',
        items=[(axis, axis, 'Rotation Axis') for axis in ('X', 'Z')]
    )
    finger_rotation_axis: bpy.props.EnumProperty(
        name="Finger Rotation Axis",
        description='Set primary rotation axis of fingers',
        items=[
            (axis, axis[0].upper() + axis[1:], 'Rotation Axis')
            for axis in ('automatic', 'X', 'Y', 'Z', '-X', '-Y', '-Z')
        ]
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        row = col.row(align=True)
        row.use_property_split = True
        row.prop(self, 'to_skeleton')
        sub_col = col.column()
        sub_col.use_property_split = True
        sub_col.prop(self, 'reorient_y')
        scol = sub_col.column()
        scol.enabled = self.reorient_y
        scol.prop(self, 'recalculate_roll')
        if self.rigify_options:
            col.prop(self, 'rigify_options', toggle=True, icon='DISCLOSURE_TRI_DOWN')
            sub_col = col.column()
            sub_col.use_property_split = True
            sub_col.label(text="Limb Segments:")
            sub_col.prop(self, 'arm_limb_segments', text='Arm')
            sub_col.prop(self, 'leg_limb_segments', text='Leg')
            sub_col.label(text="Primary Rotation Axis:")
            sub_col.prop(self, 'arm_rotation_axis', text='Arm')
            sub_col.prop(self, 'leg_rotation_axis', text='Leg')
            sub_col.prop(self, 'palm_rotation_axis', text='Palm')
            sub_col.prop(self, 'finger_rotation_axis', text='Fingers')
        else:
            col.prop(self, 'rigify_options', toggle=True, icon='DISCLOSURE_TRI_RIGHT')

        if self.edit_armature:
            col.prop(self, 'edit_armature', toggle=True, icon='CHECKBOX_HLT')  # DISCLOSURE_TRI_DOWN
            col = col.column()
            col.use_property_split = True
            col.prop(self, 'subdivide_spine_bones')
            col = col.column(heading="Create")
            col.prop(self, 'create_twist_bones')
            sub_col = col.column()
            sub_col.enabled = self.create_twist_bones
            sub_col.prop(self, 'arm_twist_bones_number')
            sub_col.prop(self, 'leg_twist_bones_number')
            col = col.column(heading="Remove")
            col.prop(self, 'remove_heel_bones')
            col.prop(self, 'remove_pelvis_bones')
            col.prop(self, 'remove_breast_bones')
            col.prop(self, 'remove_face_bones')
            col.prop(self, 'remove_palm_bones')
            col.separator()
        else:
            col.prop(self, 'edit_armature', toggle=True, icon='CHECKBOX_DEHLT')  # DISCLOSURE_TRI_RIGHT
        col = layout.column()
        col.use_property_split = True
        col.prop(self, 'rename')
        scol = col.column()
        scol.enabled = self.rename
        scol.prop(self, 'new_name')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=250)

    def update_head_and_tail_positions(self, edit_bones):
        select_set_edit_bone(edit_bones, edit_bones[-1])
        bpy.ops.transform.translate()
        bpy.ops.armature.select_all(action='DESELECT')

    def execute(self, context):
        if not self.to_skeleton:
            return {'FINISHED'}
        obj = context.active_object
        edit_bones = obj.data.edit_bones
        # obj.data.show_names = True
        obj.data.show_axes = True

        to_armature = bpy.data.objects.get(self.to_skeleton)
        main_parent = get_main_parent(to_armature)
        if not main_parent:
            scale = to_armature.scale[0]
            is_scaled = False if scale == 1 else scale
        elif main_parent.type == 'EMPTY':
            is_scaled = main_parent.scale[0]
        else:
            scale = main_parent.scale[0]
            is_scaled = False if scale == 1 else scale

        if is_scaled:
            scale_armature(context, obj, is_scaled, 'fit_metarig')

        mode = context.mode
        if context.mode != 'EDIT_ARMATURE':
            bpy.ops.object.editmode_toggle()

        sorted_spine_names, new_bones_data = create_spine_bones(
            obj, self.subdivide_spine_bones
        )
        transform_bones_to_skeleton(
            context, edit_bones,
            self.to_skeleton, new_bones_data=new_bones_data,
            reorient_y=self.reorient_y
        )
        arm = [
            "upper_arm.L",
            "upper_arm.R",
        ]
        leg = [
            "thigh.L",
            "thigh.R",
        ]
        palm = [
            "palm.01.L",
            "palm.01.R",
        ]
        fingers = [
            "f_index.01.L",
            "thumb.01.L",
            "f_middle.01.L",
            "f_ring.01.L",
            "f_pinky.01.L",
            "f_index.01.R",
            "thumb.01.R",
            "f_middle.01.R",
            "f_ring.01.R",
            "f_pinky.01.R",
        ]
        set_rigify_limb_segments(obj, arm, self.arm_limb_segments)
        set_rigify_limb_segments(obj, leg, self.leg_limb_segments)
        torso_recalculate_roll(edit_bones, sorted_spine_names)
        if self.reorient_y and self.recalculate_roll:
            recalculate_roll(edit_bones)
        set_rigify_bone_rotation_axis(obj, arm, axis=self.arm_rotation_axis)
        set_rigify_bone_rotation_axis(obj, leg, axis=self.leg_rotation_axis)
        set_rigify_bone_rotation_axis(
            obj, palm, axis=self.palm_rotation_axis, palm=True,
        )
        set_rigify_bone_rotation_axis(
            obj, fingers, axis=self.finger_rotation_axis, primary=True,
        )
        if self.subdivide_spine_bones:
            rename_spine_bones(edit_bones, sorted_spine_names)

        if self.rename:
            obj.name = self.new_name
            obj.data.name = self.new_name + '_skeleton'

        if not self.edit_armature:
            self.update_head_and_tail_positions(edit_bones)
            redraw_area('VIEW_3D')
            if mode != 'EDIT_ARMATURE':
                bpy.ops.object.editmode_toggle()
            return {'FINISHED'}

        if not self.create_twist_bones:
            self.update_head_and_tail_positions(edit_bones)

        arm_twist_limbs = [
            "upper_arm.L",
            "upper_arm.R",
            "forearm.L",
            "forearm.R",
        ]
        leg_twist_limbs = [
            "thigh.L",
            "thigh.R",
            "shin.L",
            "shin.R",
        ]
        heel_bones = [
            "heel.02.L",
            "heel.02.R"
        ]
        pelvis_bones = [
            "pelvis.L",
            "pelvis.R"
        ]
        breast_bones = [
            "breast.L",
            "breast.R"
        ]
        face_bones = [
            b.name for b in edit_bones
            if b.layers[0] or b.layers[1] or b.layers[2]
        ]
        palm_bones = [b.name for b in edit_bones if b.name.startswith('palm')]

        if self.create_twist_bones:
            create_twist_bones(
                context, edit_bones, self.to_skeleton,
                arm_twist_limbs, self.reorient_y,
                amount=self.arm_twist_bones_number
            )
            create_twist_bones(
                context, edit_bones, self.to_skeleton,
                leg_twist_limbs, self.reorient_y,
                amount=self.leg_twist_bones_number

            )

        remove_bones = []
        if self.remove_heel_bones:
            remove_bones += heel_bones
        if self.remove_pelvis_bones:
            remove_bones += pelvis_bones
        if self.remove_breast_bones:
            remove_bones += breast_bones
        if self.remove_face_bones:
            remove_bones += face_bones
        if self.remove_palm_bones:
            remove_bones += palm_bones

        for b in edit_bones:
            if b.name in remove_bones:
                edit_bones.remove(b)

        redraw_area('VIEW_3D')
        if mode != 'EDIT_ARMATURE':
            bpy.ops.object.editmode_toggle()
        if is_scaled:
            empty = scale_armature(context, obj, 1, 'fit_metarig')
            bpy.data.objects.remove(empty)
        return {'FINISHED'}


class AT_OT_clean_imported_animation(Operator):
    bl_idname = "at.clean_imported_animation"
    bl_label = "Clean Imported Animation"
    bl_description = "Clear the transform keyframes to fix dislocated bones"
    bl_options = {'UNDO'}

    def execute(self, context):
        armature = context.active_object
        clear_location_keyframes(context, armature, [armature.data.bones[0].name])
        # clear_location_keyframes(context, armature, [])
        return {'FINISHED'}


class AT_OT_constrain_armature(Operator):
    bl_idname = "at.constrain_armature"
    bl_label = "Constrain Armature"
    bl_description = "Choose a skeleton rig to constrain transformation of the active armature according to the template mapping"
    bl_options = {'REGISTER', 'UNDO'}

    to_skeleton: bpy.props.EnumProperty(
        name="Target Skeleton",
        items=scene_armatures_enum,
        default=0
    )
    constrain_type: bpy.props.EnumProperty(
        name="Constrain Type",
        items=[
            ('SIMPLE', 'Simple', 'Simple and straight use of constraint from bone to bone'),
            (
                'COMPLEX', 'Complex',
                (
                    'Use helper empties in order to properly orient constraint. '
                    'It is the way to constrain the skeleton imported from game engine.'
                )
            )
        ],
        default=0
    )
    offset: bpy.props.BoolProperty(
        name="Offset",
        description="Use copy constraints with offset",
        default=False
    )
    constrain_base_object: bpy.props.BoolProperty(
        name="Base Object",
        description="Apply constraints to base armature object",
        default=False
    )
    source_list: bpy.props.EnumProperty(
        name="Select List",
        description="Choose the bone list of the active armature to constrain",
        items=[
            ('LEFT', 'Left', 'The bone list to wich constraints will be applied'),
            ('RIGHT', 'Right', 'The bone list to wich constraints will be applied')
        ],
        default='LEFT'
    )
    rotation_order: bpy.props.EnumProperty(
        name="Rotation Order",
        description="Explicitly specify the euler rotation order",
        items=[
            ('XYZ', 'XYZ Euler', ''),
            ('XZY', 'XZY Euler', ''),
            ('YXZ', 'YXZ Euler', ''),
            ('YZX', 'YZX Euler', ''),
            ('ZXY', 'ZXY Euler', ''),
            ('ZYX', 'ZYX Euler', ''),
        ],
        default='YZX'
    )
    use_uniform_scale: bpy.props.BoolProperty(
        name="Make Uniform Scale",
        description="Redistrebute the copied change in volume equally between the three axes of the owner",
        default=False
    )
    set_rigify_limbs_to_FK: bpy.props.BoolProperty(
        name="Rigify Rig to FK",
        description="Switch the legs and arms of the rigify control rig to FK",
        default=True
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'constrain_type', expand=True)
        col = layout.column()
        col.use_property_split = True
        col.prop(self, 'to_skeleton')
        row = col.row()
        row.prop(self, 'source_list', expand=True)
        if self.constrain_type == 'SIMPLE':
            col.prop(self, 'offset')
        else:
            col.prop(self, 'rotation_order')
        col.prop(self, 'use_uniform_scale')
        # subcol = col.column()
        # subcol.enabled = not self.offset
        col.prop(self, 'constrain_base_object')
        col.prop(self, 'set_rigify_limbs_to_FK')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=250)

    def execute(self, context):
        if not self.to_skeleton:
            return {'FINISHED'}
        obj = context.active_object
        to_armature = bpy.data.objects.get(self.to_skeleton)
        if self.set_rigify_limbs_to_FK:
            set_rigify_limb_ctrls_to_FK(obj)
        if self.constrain_base_object:
            if self.offset and self.constrain_type == 'SIMPLE':
                make_constraint(obj, to_armature, 'COPY_LOCATION', offset=True)
                make_constraint(obj, to_armature, 'COPY_ROTATION', mix_mode='ADD')
                make_constraint(obj, to_armature, 'COPY_SCALE', offset=False)
            else:
                make_constraint(obj, to_armature, 'COPY_TRANSFORMS', mix_mode='BEFORE_FULL')
        bones = obj.pose.bones
        if self.constrain_type == 'COMPLEX':
            coll = make_constraints_collection(context)
        swap_source = self.source_list == 'RIGHT'
        for bone, to_bone in yield_bone_links(context, bones, self.to_skeleton, swap=swap_source):
            if self.constrain_type == 'COMPLEX':
                constrain_to_complex_skeleton(
                    obj, to_armature, bone, to_bone, coll, self.rotation_order, self.use_uniform_scale
                )
                continue
            if not self.offset:
                space = rotat_space = scale_space = 'WORLD'
            else:
                space = 'LOCAL'
                rotat_space = scale_space = 'POSE'

            make_constraint(
                bone, to_armature, 'COPY_LOCATION',
                subtarget_name=to_bone.name, offset=self.offset, space=space  # 'LOCAL' 'POSE'
            )
            make_constraint(
                bone, to_armature, 'COPY_ROTATION',
                subtarget_name=to_bone.name, mix_mode='REPLACE', space=rotat_space  # 'REPLACE' 'ADD'
            )
            make_constraint(
                bone, to_armature, 'COPY_SCALE',
                subtarget_name=to_bone.name, offset=False, space=scale_space, own_space='POSE',
                uniform=self.use_uniform_scale
            )
        return {'FINISHED'}


class AT_OT_clear_armature_constraints(Operator):
    bl_idname = "at.clear_armature_constraints"
    bl_label = "Clear Armature Constraints"
    bl_description = "Remove all constraints for each bone of the active armature"
    bl_options = {'REGISTER', 'UNDO'}

    constraints: bpy.props.EnumProperty(
        name="Constraints",
        items=[
            ('AT', 'AT Constraints', 'Remove retargeting constraints labeled with [AT] prefix'),
            ('ALL', 'All', 'Remove all constraints in the armature')
        ],
        description="Remove all or [AT] constraints only",
        default='AT'
    )

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, 'constraints', expand=True)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=190)

    def execute(self, context):
        obj = context.active_object
        use_filter = self.constraints == 'AT'
        remove_constraints(obj, use_filter)
        for bone in obj.pose.bones:
            remove_constraints(bone, use_filter)
        return {'FINISHED'}


class AT_OT_bake_animation(Operator):
    bl_idname = "at.bake_animation"
    bl_label = "Bake Animation"
    bl_description = "Bake animationa of the selected bone list and clear constraints"
    bl_options = {'UNDO'}

    source_list: bpy.props.EnumProperty(
        name="Bone List",
        description="Choose the bone list of the active armature to bake",
        items=[
            ('LEFT', 'Left', 'Bake the left bone list'),
            ('RIGHT', 'Right', 'Bake the right bone list')
        ],
        default='LEFT'
    )
    start_frame: bpy.props.IntProperty(
        name='Start Frame',
        description='Start frame for baking',
        soft_min=0, soft_max=10000, default=0
    )
    end_frame: bpy.props.IntProperty(
        name='End Frame',
        description='End frame for baking',
        soft_min=0, soft_max=10000, default=0
    )
    use_current_action: bpy.props.BoolProperty(
        name='Overwrite Current Action',
        description='Bake animation into current action, instead of creating a new one',
        default=False
    )
    scale_armature: bpy.props.BoolProperty(
        name='Scale Armature',
        description='Parent armature to empty and scale for export via .fbx file',
        default=False
    )
    empty_name: bpy.props.StringProperty(
        name="Parent Empty Name",
        default="scaled_rig"
    )
    scale_value: bpy.props.FloatProperty(
        name="Scale",
        default=0.01
    )

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.use_property_split = True
        row.prop(self, 'source_list', expand=True)
        col = layout.column()
        col.use_property_split = True
        col.prop(self, 'start_frame')
        col.prop(self, 'end_frame')
        col.prop(self, 'use_current_action')
        col.prop(self, 'scale_armature')
        sub_col = col.column()
        sub_col.enabled = self.scale_armature
        sub_col.prop(self, 'empty_name')
        sub_col.prop(self, 'scale_value')

    def invoke(self, context, event):
        self.start_frame = context.scene.frame_start
        self.end_frame = context.scene.frame_end
        self.empty_name = "scaled_" + context.active_object.name
        return context.window_manager.invoke_props_dialog(self, width=300)

    def execute(self, context):
        armature = context.active_object
        visible = is_visible(armature)
        is_visible(armature, set=True)
        armature.select_set(True)

        if self.scale_armature:
            unit_system = context.scene.unit_settings.system
            if unit_system != 'METRIC':
                msg = (
                    'Warning: The current unit system is not a metric type, '
                    'the final result might be different than expected.'
                )
                self.report({'WARNING'}, msg)
            scale_armature(context, armature, self.scale_value, self.empty_name)

        bones = [
            armature.data.bones.get(n)
            for n in iterate_template_links(context, self.source_list)
        ]
        mode = context.mode
        if mode != 'POSE':
            bpy.ops.object.posemode_toggle()
        bpy.ops.pose.select_all(action='DESELECT')
        for b in bones:
            if hasattr(b, 'select'):
                b.select = True
        bpy.ops.nla.bake(
            frame_start=self.start_frame,
            frame_end=self.end_frame,
            step=1,
            only_selected=True,
            visual_keying=True,
            clear_constraints=True,
            use_current_action=self.use_current_action,
            bake_types={'POSE'}
        )
        bpy.ops.pose.select_all(action='DESELECT')
        if mode != 'POSE':
            bpy.ops.object.posemode_toggle()

        is_visible(armature, set=visible)
        return {'FINISHED'}


class AT_OT_scale_armature(Operator):
    bl_idname = "at.scale_armature"
    bl_label = "Scale Skeleton"
    bl_description = "Parent the armature to the empty and then scale"
    bl_options = {'UNDO'}

    empty_name: bpy.props.StringProperty(
        name="Parent Empty Name",
        default="scaled_rig"
    )
    scale_value: bpy.props.FloatProperty(
        name="Scale",
        default=0.01
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.use_property_split = True
        col.prop(self, 'empty_name')
        col.prop(self, 'scale_value')

    def invoke(self, context, event):
        unit_system = context.scene.unit_settings.system
        if unit_system != 'METRIC':
            msg = (
                'Warning: The current unit system is not a metric type, '
                'the final result might be different than expected.'
            )
            self.report({'WARNING'}, msg)
        self.empty_name = "scaled_" + context.active_object.name
        return context.window_manager.invoke_props_dialog(self, width=300)

    def execute(self, context):
        obj = context.active_object
        scale_armature(context, obj, self.scale_value, self.empty_name)
        return {'FINISHED'}


class AT_OT_mapping_from_ue2rigify(Operator):
    bl_idname = "at.mapping_from_ue2rigify"
    bl_label = "Mapping from ue2rigify"
    bl_description = "Get links from ue2rigify and apply as mapping to the current template"
    bl_options = {'REGISTER', 'UNDO'}

    template: bpy.props.EnumProperty(
        name="Template",
        items=ue2rigify_template_enum,
    )
    links: bpy.props.EnumProperty(
        name="Links",
        items=ue2rigify_links_enum,
    )
    swap_source: bpy.props.BoolProperty(
        name="Swap Source",
        description="Try to swap the source items with the target items to match with the template list",
        default=False
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.use_property_split = True
        col.prop(self, 'template')
        col.prop(self, 'links')
        col.prop(self, 'swap_source')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=250)

    def execute(self, context):
        json_data = get_json_data(self.links)
        mapping_data = {}
        for i in json_data:
            if self.swap_source:
                mapping_data[i.get('to_socket')] = i.get('from_socket')
            else:
                mapping_data[i.get('from_socket')] = i.get('to_socket')
        apply_bone_mapping_data(context, mapping_data)
        redraw_area('PROPERTIES')
        return {'FINISHED'}


class AT_OT_browse_config_folder(Operator):
    bl_idname = "at.browse_config_folder"
    bl_label = "Browse Config Folder"
    bl_description = "Open the config folder in the file browser containing the mapping and template files"

    def execute(self, context):
        import sys
        directory = get_config_path()

        if sys.platform == "win32":
            os.startfile(directory)
        else:
            if sys.platform == "darwin":
                command = "open"
            else:
                command = "xdg-open"
            subprocess.call([command, directory])

        return {'FINISHED'}


class AT_OT_save_metarig(Operator):
    bl_idname = "at.save_metarig"
    bl_label = "Save Meta-Rig"
    bl_description = "Save the active armature as a meta-rig to the .py file located in the user config folder"

    metarig_name: bpy.props.StringProperty(
        name="Meta-Rig Name",
        description="Name the meta-rig file",
        default="New Meta-Rig"
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=250)

    def execute(self, context):
        if context.active_object.type != 'ARMATURE':
            return {'FINISHED'}
        import sys
        if 'rigify' in sys.modules:
            from rigify.utils.rig import write_metarig
        else:
            return {'FINISHED'}
        text = write_metarig(
            context.active_object,
            layers=True,
            func_name="create",
            groups=True,
            widgets=True
        )
        directory = os.path.join(get_config_path(), "metarigs")
        validate_path(directory)
        file_name = check_extension(self.metarig_name, extension='.py')
        file_path = os.path.join(directory, file_name)
        write_to_file(file_path, text)
        return {'FINISHED'}


class AT_OT_load_metarig(Operator):
    bl_idname = "at.load_metarig"
    bl_label = "Load Meta-Rig"
    bl_description = "Load meta-rig from a .py file located in the user config folder"
    bl_options = {'UNDO'}

    metarig_name: bpy.props.StringProperty(
        name="Meta-Rig Name",
    )

    def execute(self, context):
        import sys
        if 'rigify' in sys.modules:
            from rigify.ui import DATA_OT_rigify_add_bone_groups as bone_groups
        else:
            return {'FINISHED'}
        obj = create_new_armature(f"{self.metarig_name}_metarig")
        select_object(obj)
        bone_groups.execute(None, context)

        directory = os.path.join(get_config_path(), "metarigs")
        file_path = os.path.join(directory, self.metarig_name + ".py")
        metarig_script = get_module_from_path(file_path, self.metarig_name + ".py")
        metarig_script.create(obj)
        bpy.ops.object.mode_set(mode='OBJECT')

        return {'FINISHED'}


class AT_OT_delete_metarig(Operator):
    bl_idname = "at.delete_metarig"
    bl_label = "Delete Meta-Rig"
    bl_description = "Delete the meta-rig file located in the user config folder"

    metarig_name: bpy.props.StringProperty(
        name="Meta-Rig Name",
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        directory = os.path.join(get_config_path(), "metarigs")
        validate_path(directory)
        file_name = check_extension(self.metarig_name, extension='.py')
        file_path = os.path.join(directory, file_name)
        if not os.path.isfile(file_path):
            return {'FINISHED'}
        os.remove(file_path)

        return {'FINISHED'}


class AT_OT_select_category_bone_list(Operator):
    bl_idname = "at.select_category_bone_list"
    bl_label = "Select Bone List"
    bl_description = "Select bone list from the template category or from the bone mapping of the current category"

    select_list: bpy.props.EnumProperty(
        name="Select List",
        items=[
            ('LEFT', 'Left', 'Select bones corresponding to the list of the active template'),
            ('RIGHT', 'Right', 'Select bones corresponding to the list of the current bone mapping'),
        ],
        default='LEFT'
    )
    append_to_selection: bpy.props.BoolProperty(
        name="Append to Selection",
        description="Add list of bones to the current selection",
        default=False
    )

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.use_property_split = True
        row.prop(self, 'select_list', expand=True)
        col = layout.column()
        col.use_property_split = True
        col.prop(self, 'append_to_selection')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=250)

    def execute(self, context):
        obj = context.active_object
        mode = context.mode.split('_')[0]
        if mode == 'POSE':
            bones = [
                obj.data.bones.get(n)
                for n in iterate_template_category_links(context, self.select_list)
            ]
            if not self.append_to_selection:
                bpy.ops.pose.select_all(action='DESELECT')
            for b in bones:
                if hasattr(b, 'select'):
                    b.select = True
                    obj.data.bones.active = b
        elif mode == 'EDIT':
            bones = [
                obj.data.edit_bones.get(n)
                for n in iterate_template_category_links(context, self.select_list)
            ]
            if not self.append_to_selection:
                bpy.ops.armature.select_all(action='DESELECT')
            for b in bones:
                if hasattr(b, 'select'):
                    b.select = True
                    b.select_head = True
                    b.select_tail = True
                    obj.data.edit_bones.active = b
        return {'FINISHED'}


# Experimental
class AT_OT_copy_layer_bones(Operator):
    bl_idname = "at.copy_layer_bones"
    bl_label = "Copy Layer Bones"
    bl_description = "Copy bones that located in selected layers, clear their constrains and animation data"
    bl_options = {'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not get_selected_bone_layers(context):
            msg = "Please, select bone layers first."
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}
        layer_bones = get_bones_in_selected_layers(context, obj)
        if not layer_bones:
            msg = "Selected bone layers do not contain any bones to make a skeleton of."
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}
        armature = obj.data.copy()
        armature.name = 'armature'
        from bpy_extras import object_utils
        skeleton = object_utils.object_data_add(
            context, armature, operator=None,
            name='armature'
        )
        context.view_layer.update()
        for bone in skeleton.pose.bones:
            constraints = [c for c in bone.constraints]
            for c in constraints:
                bone.constraints.remove(c)
        keep_bone_names = [b.name for b in layer_bones]
        armature.animation_data_clear()
        bpy.ops.object.editmode_toggle()
        for b in armature.edit_bones:
            if b.name not in keep_bone_names:
                armature.edit_bones.remove(b)
        bpy.ops.object.editmode_toggle()

        for i in get_selected_bone_layers(context):
            armature.layers[i] = True

        return {'FINISHED'}


classes = [
    AT_OT_save_bone_mapping,
    AT_OT_save_bone_mapping_to,
    AT_OT_load_bone_mapping,
    AT_OT_map_selected_bone,
    AT_OT_map_custom_bone_name,
    AT_OT_remove_bone_mapping,
    AT_OT_rename_skeleton_bones,
    AT_OT_template_categories,
    AT_OT_create_template_category,
    AT_OT_remove_template,
    AT_OT_rename_template,
    AT_OT_rename_mapping,
    AT_OT_remove_template_category,
    AT_OT_add_selected_to_template,
    AT_OT_add_custom_bone_name,
    WM_OT_Copy_to_Clipboard,
    AT_OT_remove_selected_from_template_category,
    AT_OT_remove_all_from_template_category,
    AT_OT_move_list_items_up,
    AT_OT_move_list_items_down,
    AT_OT_Select_UList_Items,
    AT_OT_Select_Bone_Layers,
    AT_OT_rename_template_category,
    AT_OT_move_template_category_down,
    AT_OT_guess_mapping_bones,
    AT_OT_fit_metarig,
    AT_OT_clean_imported_animation,
    AT_OT_constrain_armature,
    AT_OT_clear_armature_constraints,
    AT_OT_bake_animation,
    AT_OT_scale_armature,
    AT_OT_browse_config_folder,
    TEMPLATE_UL_Armature_bones,
    TEMPLATE_UL_Category_bones,
    POPUP_OT_Create_Template,
    AT_OT_save_metarig,
    AT_OT_load_metarig,
    AT_OT_delete_metarig,
    AT_OT_select_category_bone_list,
    AT_OT_copy_layer_bones,
    AT_OT_mapping_from_ue2rigify,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes[::-1]:
        bpy.utils.unregister_class(cls)
