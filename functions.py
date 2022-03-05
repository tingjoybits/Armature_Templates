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
import json
from math import radians, degrees
import numpy as np


def props(context=None):
    if not context:
        context = bpy.context
    return context.window_manager.armature_templates_props


def set_bone_list_layer(index_list, value=True):
    for i in range(32):
        if i not in index_list:
            continue
        setattr(props(), "armature_layer_" + str(i), value)


def at_initialization(cls):
    if props().initialize:
        return None
    cls.armature = ''
    initiate_search_props()
    props().initialize = True


def get_layer_bones(context, layer_index, obj):
    if obj is None:
        obj = context.active_object
    if obj.type != 'ARMATURE':
        return []
    bones = []
    for b in obj.pose.bones:
        if not b.bone:
            continue
        if b.bone.layers[layer_index]:
            bones.append(b)
    return bones


def check_extension(name, extension='.json'):
    if name.endswith(extension):
        return name
    name += extension
    return name


def base_file_name(name, extension='.json'):
    if name.endswith(extension):
        return '.'.join(name.split('.')[:-1])
    return name


def get_json_data(json_file_path):
    if not os.path.isfile(json_file_path):
        return None
    f = open(json_file_path)
    file_data = json.load(f)
    f.close()
    return file_data


def save_json_data(json_file_path, save_data):
    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=4)


def write_to_file(file_path, text):
    file = open(file_path, "w")
    if text is not None:
        file.write(text)
    file.close()


def draw_ulist_item(self, layout, item, active_data, active_propname):
    # def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
    if self.layout_type in {'DEFAULT', 'COMPACT'}:
        if item:
            layout.prop(item, "name", text="", emboss=False)
            if getattr(active_data, active_propname) == item.index:
                layout.operator(
                    "wmo.copy_to_clipboard", text="", emboss=False, icon='COPYDOWN'
                ).text = item.name
            flag_icon = 'CHECKBOX_HLT' if item.flag else 'CHECKBOX_DEHLT'
            layout.prop(item, "flag", text="", emboss=False, icon=flag_icon)
        else:
            layout.label(text="", translate=False)
    elif self.layout_type in {'GRID'}:
        layout.alignment = 'CENTER'
        layout.label(text="")  # icon_value=icon


def move_list_item_up(item_list, move_item):
    for i, item in enumerate(item_list):
        if item != move_item:
            continue
        if i == 0:
            break
        previous = item_list[i - 1]
        item_list[i] = previous
        item_list[i - 1] = move_item
        return None


def move_list_item_down(item_list, move_item):
    for i, item in zip(range(len(item_list) - 1, -1, -1), reversed(item_list)):
        if item != move_item:
            continue
        if i == len(item_list) - 1:
            break
        nextitem = item_list[i + 1]
        item_list[i] = nextitem
        item_list[i + 1] = move_item
        return None


def move_list_items_up_top(item_list, move_items):
    for i, item in enumerate(move_items):
        item_list.remove(item)
        item_list.insert(i, item)


def move_list_items_down_bottom(item_list, move_items):
    for item in move_items:
        item_list.remove(item)
        item_list.append(item)


def select_ulist_items(item_list, select=True, invert=False):
    for item in item_list:
        if not invert:
            item.flag = select
            continue
        if item.flag:
            item.flag = False
        else:
            item.flag = True


def evaluate_bone_list(context, obj, template_data):
    added_bones = []
    bones = get_bones_in_selected_layers(context, obj)
    for category in template_data:
        added_bones += template_data.get(category)
    return [
        b.name for b in bones
        if b.name not in added_bones
    ]


def validate_path(path):
    if not os.path.isdir(path):
        os.mkdir(path, mode=0o777)


def get_config_path():
    user_path = bpy.utils.resource_path('USER')
    config_path = os.path.join(user_path, "config")
    config_path = os.path.join(config_path, "armature_templates")
    validate_path(config_path)
    return config_path


def is_native_template_path(template_name):
    module_path = os.path.dirname(__file__)
    templates_path = os.path.join(module_path, "templates")
    native_templates_path = os.path.join(templates_path, template_name + ".json")
    if os.path.isfile(native_templates_path):
        return native_templates_path
    else:
        return False


def get_template_path(return_type=False):
    is_native = is_native_template_path(props().templates)
    if is_native:
        if return_type:
            return 'NATIVE', is_native
        return is_native
    config_templates_path = os.path.join(get_config_path(), "templates")
    config_file_path = os.path.join(config_templates_path, props().templates + ".json")
    if return_type:
        return 'CONFIG', config_file_path
    return config_file_path


def make_enum_from_file_list(path, start_index, extension='.json', skip_name_list=[]):
    enum = []
    i = start_index
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)) and\
                file.lower().endswith(extension):
            name = file.split(extension)[0]
            if name in skip_name_list:
                continue
            enum.append((name, name, '', i))
            i += 1
    return enum


def template_list_enum(self, context):
    module_path = os.path.dirname(__file__)
    native_path = os.path.join(module_path, "templates")
    validate_path(native_path)
    native = make_enum_from_file_list(native_path, 0)
    config_path = os.path.join(get_config_path(), "templates")
    validate_path(config_path)
    config = make_enum_from_file_list(config_path, len(native))
    return native + config


def bone_category_enum(self, context):
    json_file_path = get_template_path()
    if not os.path.isfile(json_file_path):
        return []
    file_data = get_json_data(json_file_path)
    return [(cat, cat, '', i) for i, cat in enumerate(file_data)]


def scene_armatures_enum(self, context):
    obj = context.active_object
    return [
        (ob.name, ob.name, '')
        for ob in bpy.data.objects
        if ob.name != obj.data.name and ob.type == 'ARMATURE'
    ]


def get_native_mapping_path(template):
    module_path = os.path.dirname(__file__)
    native_path = os.path.join(module_path, "bone_mapping")
    native_mapping_path = os.path.join(native_path, template)
    return native_mapping_path


def get_config_mapping_path(template):
    config_path = os.path.join(get_config_path(), "bone_mapping")
    validate_path(config_path)
    config_mapping_path = os.path.join(config_path, template)
    validate_path(config_mapping_path)
    return config_mapping_path


def get_mapping_path(template, location='CONFIG'):
    if location == 'CONFIG':
        return get_config_mapping_path(template)
    if location == 'NATIVE':
        return get_native_mapping_path(template)
    return ''


def save_custom_file(template_name, template_data, location='CONFIG'):
    custom_mapping_data = {}
    for category, i, name in iterate_template_data(template_data):
        custom_mapping_data[name] = ""
    mapping_path = get_mapping_path(template_name, location)
    validate_path(mapping_path)
    json_file_path = os.path.join(mapping_path, 'custom.json')
    save_json_data(json_file_path, custom_mapping_data)


def create_bone_mapping_enum(context, skip_name_list=[]):
    native_mapping_path = get_native_mapping_path(props(context).templates)
    if os.path.isdir(native_mapping_path):
        native = make_enum_from_file_list(
            native_mapping_path, 0, skip_name_list=skip_name_list
        )
    else:
        native = []
    config_mapping_path = get_config_mapping_path(props(context).templates)
    config = make_enum_from_file_list(
        config_mapping_path, len(native), skip_name_list=skip_name_list
    )
    return native + config


def bone_mapping_to_overwrite_enum(self, context):
    return create_bone_mapping_enum(context, skip_name_list=['custom'])


def bone_mapping_enum(self, context):
    return create_bone_mapping_enum(context)


def iterate_template_data(template_data):
    for category in template_data:
        for i, name in enumerate(template_data.get(category)):
            yield category, i, name


def iterate_wm_search_props(context):
    search_props = context.window_manager.at_search_list_props
    for prop in search_props:
        yield prop.name, prop


def apply_bone_mapping_data(context, mapping_data):
    for name, prop in iterate_wm_search_props(context):
        if mapping_data.get(name) is not None:
            prop.bone = mapping_data.get(name)


def update_apply_bone_mapping(self, context):
    native_mapping_path = get_native_mapping_path(props(context).templates)
    config_mapping_path = get_config_mapping_path(props(context).templates)
    filename = self.bone_mapping + '.json'
    filepath = os.path.join(native_mapping_path, filename)
    if not os.path.isfile(filepath):
        filepath = os.path.join(config_mapping_path, filename)
    file_data = get_json_data(filepath)
    apply_bone_mapping_data(context, file_data)
    obj = context.active_object
    settings = obj.data.armtemp_settings
    settings.mapping = props().bone_mapping
    redraw_area('PROPERTIES')


def set_search_props(class_type, template_data):
    search_props = bpy.context.window_manager.at_search_list_props
    search_props.clear()
    for category, i, name in iterate_template_data(template_data):
        prop = search_props.add()
        prop.name = name
        prop.category = category


def initiate_search_props():
    json_file_path = get_template_path()
    template_data = get_json_data(json_file_path)
    from .properties import Search_Bones
    set_search_props(Search_Bones, template_data)


def ui_switch_select(cls):
    obj = bpy.context.active_object
    if cls.armature != obj.name:
        props().ui_switching = True
        cls.armature = obj.name
        settings = obj.data.armtemp_settings
        if settings.template:
            try:
                props().templates = settings.template
            except TypeError:
                pass
        if settings.mapping:
            try:
                props().bone_mapping = settings.mapping
            except TypeError:
                pass
        if settings.bone_list:
            bools = [bool(int(b)) for b in settings.bone_list.split(' ')]
            set_select_bone_layers(bools)
        else:
            layer_bools = [layer for layer in obj.data.layers]
            set_select_bone_layers(layer_bools)
            set_bone_list_layer([0, 29])
        if settings.mapping_data:
            apply_bone_mapping_data(bpy.context, eval(settings.mapping_data))
            redraw_area('PROPERTIES')
        props().ui_switching = False


def update_templates(self, context):
    obj = context.active_object
    settings = obj.data.armtemp_settings
    self['bone_category'] = 0
    if not self.ui_switching:
        self['bone_mapping'] = 0
        settings.mapping = props().bone_mapping
    initiate_search_props()
    settings.template = props().templates


def update_armature_layers(self, context):
    obj = context.active_object
    settings = obj.data.armtemp_settings
    index_list = get_selected_bone_layers(context)
    bools = [(i in index_list) for i in range(32)]
    settings.bone_list = " ".join([str(int(b)) for b in bools])


def update_mapping_list(self, context):
    if props().ui_switching:
        return None
    obj = context.active_object
    settings = obj.data.armtemp_settings
    data = get_mapped_bones_data(context)
    settings.mapping_data = json.dumps(data)


def update_browse_path(self, context):
    if self.browse_path == 'CONFIG':
        path = os.path.join(get_config_path(), "bone_mapping")
    elif self.browse_path == 'NATIVE':
        module_path = os.path.dirname(__file__)
        path = os.path.join(module_path, "bone_mapping")
    elif bpy.data.filepath:
        path = os.path.dirname(bpy.data.filepath)
    else:
        path = os.path.expanduser('~')
    context.space_data.params.directory = bytes(path, "utf-8")


def get_selected_bone_layers(context):
    index_list = []
    for i in range(32):
        layer_index = getattr(props(context), "armature_layer_" + str(i))
        if layer_index:
            index_list.append(i)
    return index_list


def set_select_bone_layers(bools):
    for i in range(32):
        setattr(props(), "armature_layer_" + str(i), bools[i])


def get_bones_in_selected_layers(context, obj):
    if obj is None:
        obj = context.active_object
    layer_bones = []
    for i in get_selected_bone_layers(context):
        layer_bones += get_layer_bones(context, i, obj)
    return layer_bones


def get_mapped_bones_data(context):
    data = {}
    for name, prop in iterate_wm_search_props(context):
        data[name] = prop.bone
    return data


def text_lookup(find_string, source_text):
    if source_text.find(find_string) != -1:
        return True
    else:
        return False


def get_filtered_list(filter, item_list, case_sensitive=False):
    items = []
    for item in item_list:
        if filter and not case_sensitive:
            if not text_lookup(filter.lower(), item.lower()):
                continue
        elif filter:
            if not text_lookup(filter, item):
                continue
        items.append(item)
    return items


def set_template_item_list(name_list, clear=True):
    item_list = bpy.context.window_manager.at_template_item_list
    if clear:
        item_list.clear()
    for i, n in enumerate(name_list):
        item = item_list.add()
        item.name = n
        item.flag = False
        item.index = i


def set_template_category_list(name_list, flag_list=None, clear=True):
    item_list = bpy.context.window_manager.at_template_category_list
    if clear:
        item_list.clear()
    for i, n in enumerate(name_list):
        item = item_list.add()
        item.name = n
        item.index = i
        if flag_list:
            if n in flag_list:
                item.flag = True
                continue
        item.flag = False


def redraw_area(area_type):
    for area in bpy.context.screen.areas:
        if area.type == area_type:
            area.tag_redraw()


def check_new_bone(edit_bones, bone, to_bone, new_bones_data):
    if bone.name in new_bones_data:
        new_bone = edit_bones.get(new_bones_data.get(bone.name))
        if to_bone:
            children_bone = to_bone.children[0]
            if children_bone:
                to_bone = children_bone
                return new_bone, to_bone
    return None, None


def yield_bone_links(context, edit_bones, to_armature, swap=False, new_bones_data={}):
    to_data = bpy.data.objects[to_armature].data
    mapping_data = get_mapped_bones_data(context)
    for name in mapping_data:
        if not swap:
            bone = edit_bones.get(name)
            to_bone = to_data.bones.get(mapping_data.get(name))
        else:
            bone = edit_bones.get(mapping_data.get(name))
            to_bone = to_data.bones.get(name)
        if not bone or not to_bone:
            continue
        yield bone, to_bone
        if not new_bones_data:
            continue
        new_bone, to_bone = check_new_bone(
            edit_bones, bone, to_bone, new_bones_data
        )
        if new_bone and to_bone:
            yield new_bone, to_bone


def iterate_template_links(context, side):
    mapping_data = get_mapped_bones_data(context)
    for name, to_name in mapping_data.items():
        if name is None or to_name is None:
            continue
        if side == 'LEFT':
            yield name
        elif side == 'RIGHT':
            yield to_name
        else:
            yield name, to_name


def iterate_template_category_links(context, side=None):
    json_file_path = get_template_path()
    file_data = get_json_data(json_file_path)
    category_list = file_data.get(props(context).bone_category)
    if not category_list:
        return []
    mapping_data = get_mapped_bones_data(context)
    for n in category_list:
        if side == 'LEFT':
            yield n
        elif side == 'RIGHT':
            yield mapping_data.get(n)
        else:
            yield n, mapping_data.get(n)


def get_bones_by_name(obj, startswith, bone_type=None, break_name=None):
    if bone_type == 'edit':
        bones = obj.data.edit_bones
    else:
        bones = obj.pose.bones
    bones.update()
    bone_list = []
    for bone in bones:
        if not bone.name.startswith(startswith):
            continue
        if bone.name == break_name:
            break
        bone_list.append(bone)
    return bone_list


def get_spine_bones(obj, bone_type=None, break_name=None):
    bones = get_bones_by_name(
        obj, 'spine', bone_type=bone_type, break_name=break_name
    )
    spine_bones = []
    for bone in bones:
        if not bone_type and bone.name != 'spine':
            if bone.rigify_type:
                break
        spine_bones.append(bone)
    return spine_bones


def rename_objs(obj_list, name):
    for ob in obj_list:
        ob.name = name


def rename_spine_bones(edit_bones, name_list):
    spine_bones = [edit_bones.get(n) for n in name_list if edit_bones.get(n)]
    rename_objs(spine_bones[1:], 'neutral_name')
    rename_objs(spine_bones[1:], 'spine')


def get_selected_edit_bones(obj):
    edit_bones = obj.data.edit_bones
    return [b for b in edit_bones if b.select]


def create_spine_bones(obj, spine_bones_count):
    if not spine_bones_count:
        return None, None
    spine_bones = get_spine_bones(obj)
    if not spine_bones:
        return None, None
    new_bones_data = {}
    edit_bones = obj.data.edit_bones
    for i in range(spine_bones_count):
        select_edit_bones(edit_bones, [spine_bones[i].name])
        bpy.ops.armature.subdivide()
        selected_bones = get_selected_edit_bones(obj)
        new_bones_data[selected_bones[0].name] = selected_bones[1].name

    spine_bones = get_spine_bones(obj, bone_type='edit')
    sorted_names = []
    for bone in spine_bones:
        if bone.name in sorted_names:
            continue
        sorted_names.append(bone.name)
        if bone.name in new_bones_data:
            sorted_names.append(new_bones_data.get(bone.name))
    return sorted_names, new_bones_data


def get_metarig_bone_names():
    return {
        'torso': [
            "spine",
            "spine.001",
            "spine.002",
            "spine.003",
            "spine.004",
            "spine.005",
            "spine.006",
        ],
        'shoulder': [
            "shoulder.L",
            "shoulder.R",
        ],
        'arm': [
            "upper_arm.L",
            "forearm.L",
            "hand.L",
            "upper_arm.R",
            "forearm.R",
            "hand.R",
        ],
        'leg': [
            "thigh.L",
            "shin.L",
            "foot.L",
            "thigh.R",
            "shin.R",
            "foot.R",
        ],
        'toe': [
            "toe.L",
            "toe.R",
        ],
        'finger': [
            "palm.01.L",
            "f_index.01.L",
            "f_index.02.L",
            "f_index.03.L",
            "thumb.01.L",
            "thumb.02.L",
            "thumb.03.L",
            "palm.02.L",
            "f_middle.01.L",
            "f_middle.02.L",
            "f_middle.03.L",
            "palm.03.L",
            "f_ring.01.L",
            "f_ring.02.L",
            "f_ring.03.L",
            "palm.04.L",
            "f_pinky.01.L",
            "f_pinky.02.L",
            "f_pinky.03.L",
            "palm.01.R",
            "f_index.01.R",
            "f_index.02.R",
            "f_index.03.R",
            "thumb.01.R",
            "thumb.02.R",
            "thumb.03.R",
            "palm.02.R",
            "f_middle.01.R",
            "f_middle.02.R",
            "f_middle.03.R",
            "palm.03.R",
            "f_ring.01.R",
            "f_ring.02.R",
            "f_ring.03.R",
            "palm.04.R",
            "f_pinky.01.R",
            "f_pinky.02.R",
            "f_pinky.03.R",
        ]
    }


def matrix_to_invert_y_matrix(matrix, to_matrix):
    from mathutils import Matrix
    m = to_matrix
    x = 1
    if matrix[2][1] < 0 and m[2][0] > 0 and round(m[2][1], 5) != 1 or\
            round(m[2][1], 5) == -1:
        x = -1
    r = x * -1
    return Matrix((
        ([m[0][1] * r] + [m[0][0] * x] + [m[0][2]] + [m[0][3]]),
        ([m[1][1] * r] + [m[1][0] * x] + [m[1][2]] + [m[1][3]]),
        ([m[2][1] * r] + [m[2][0] * x] + [m[2][2]] + [m[2][3]]),
        matrix[3]))


def transform_bone(bone, to_bone, reorient_y=False):
    if reorient_y:
        bone.matrix = matrix_to_invert_y_matrix(
            bone.matrix, to_bone.matrix_local
        )
    else:
        bone.matrix = to_bone.matrix_local


def transform_bones_to_skeleton(
    context, edit_bones, to_skeleton,
    new_bones_data={}, reorient_y=False
):
    for bone, to_bone in yield_bone_links(
            context, edit_bones, to_skeleton, new_bones_data=new_bones_data):
        bone.length = to_bone.length
    for bone, to_bone in yield_bone_links(
            context, edit_bones, to_skeleton, new_bones_data=new_bones_data):
        transform_bone(bone, to_bone, reorient_y)
    if edit_bones.get("spine.004"):
        edit_bones["spine.004"].parent.tail.xyz = edit_bones["spine.004"].head.xyz


def select_edit_bones(edit_bones, name_list):
    bpy.ops.armature.select_all(action='DESELECT')
    for n in name_list:
        bone = edit_bones.get(n)
        if not bone:
            continue
        bone.select = True
        bone.select_head = True
        bone.select_tail = True


def set_roll_in_bones(edit_bones, name_list, value):
    for name in name_list:
        bone = edit_bones.get(name)
        bone.roll = value


def set_transform_bone_roll(value):
    bpy.ops.transform.transform(
        mode='BONE_ROLL', value=value,
        orient_axis='Z', orient_type='GLOBAL',
        orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
        orient_matrix_type='GLOBAL', mirror=True,
        use_proportional_edit=False,
        proportional_edit_falloff='SMOOTH',
        proportional_size=1,
        use_proportional_connected=False,
        use_proportional_projected=False)


def get_base_roll(e_bone):
    angle = np.arccos(np.dot([0, 0, 1], e_bone.y_axis))

    angle_d = round(degrees(angle), 2)
    angle_d *= -1 if e_bone.y_axis[0] < 0 else 1
    roll_d = round(degrees(e_bone.roll), 2)

    set_roll = 180 + roll_d
    while set_roll <= angle_d - 45:
        set_roll += 90
    while set_roll >= angle_d + 45:
        set_roll -= 90
    return radians(set_roll)


def recalculate_base_roll(edit_bones, name_list, to_roll=0):
    for name in name_list:
        e_bone = edit_bones.get(name)
        if not e_bone:
            continue
        base_roll = get_base_roll(e_bone)
        e_bone.roll = base_roll + radians(to_roll)


def normalize_roll_values(edit_bones, name_list):
    for name in name_list:
        e_bone = edit_bones.get(name)
        if not e_bone:
            continue
        if e_bone.roll > radians(225):
            e_bone.roll -= radians(360)
        elif e_bone.roll < radians(-225):
            e_bone.roll += radians(360)


def torso_recalculate_roll(edit_bones, sorted_spine_names):
    bone_names = get_metarig_bone_names()
    select_edit_bones(edit_bones, [edit_bones[-1].name])
    bpy.ops.transform.transform()
    if not sorted_spine_names:
        names = bone_names.get('torso')
    else:
        names = sorted_spine_names
    select_edit_bones(edit_bones, names)
    bpy.ops.armature.calculate_roll(type='GLOBAL_NEG_Y')
    edit_bones.update()
    set_roll_in_bones(edit_bones, names, 0)
    edit_bones['shoulder.R'].roll = edit_bones['shoulder.L'].roll * -1
    edit_bones['shoulder.R'].length = edit_bones['shoulder.L'].length


def recalculate_roll(edit_bones):
    bone_names = get_metarig_bone_names()
    names = bone_names.get('toe')
    select_edit_bones(edit_bones, names)
    bpy.ops.armature.calculate_roll(type='POS_X')

    names = bone_names.get('finger')
    select_edit_bones(edit_bones, names)
    set_transform_bone_roll((radians(90), 0, 0, 0))
    normalize_roll_values(edit_bones, names)

    names = bone_names.get('arm')
    recalculate_base_roll(edit_bones, names, 0)
    names = bone_names.get('leg')
    recalculate_base_roll(edit_bones, names, 180)
    normalize_roll_values(edit_bones, names)

    names = ['foot.L', 'foot.R']
    select_edit_bones(edit_bones, names)
    bpy.ops.armature.calculate_roll(type='GLOBAL_NEG_Z')


def set_rigify_limb_segments(armature_obj, bone_names, number_value):
    for name in bone_names:
        bone = armature_obj.pose.bones.get(name)
        if not bone:
            continue
        bone.rigify_parameters.segments = number_value


def set_rigify_bone_rotation_axis(
    armature_obj, name_list, axis='x',
    primary=False,
    palm=False
):
    for name in name_list:
        bone = armature_obj.pose.bones.get(name)
        if not bone:
            continue
        if primary:
            bone.rigify_parameters.primary_rotation_axis = axis
            continue
        if palm:
            bone.rigify_parameters.palm_rotation_axis = axis
            continue
        bone.rigify_parameters.rotation_axis = axis


def select_set_edit_bone(edit_bones, bone):
    bpy.ops.armature.select_all(action='DESELECT')
    bone.select = True
    bone.select_head = True
    if bone.use_connect:
        bone.parent.select_tail = True
    bone.select_tail = True
    edit_bones.active = bone


def create_twist_bones(
    context, edit_bones, to_skeleton_name, twist_limb_list, reorient_y,
    amount=1
):
    to_armature = bpy.data.armatures[to_skeleton_name]
    mapping_data = get_mapped_bones_data(context)
    for name in twist_limb_list:
        bone = edit_bones.get(name)
        if not bone:
            continue
        for i in range(amount):
            select_set_edit_bone(edit_bones, bone)
            bpy.ops.armature.duplicate_move()
            new_bone = edit_bones.active
            to_name = mapping_data.get(new_bone.name)
            if not to_name:
                edit_bones.remove(new_bone)
                continue
            to_bone = to_armature.bones.get(to_name)
            if not to_bone:
                edit_bones.remove(new_bone)
                continue
            if reorient_y:
                transform_bone(new_bone, to_bone, reorient_y)
                new_bone.roll = bone.roll
                new_bone.tail = bone.tail
            else:
                new_bone.matrix = to_bone.matrix_local
                new_bone.length = to_bone.length
            new_bone.parent = bone
    bpy.ops.armature.select_all(action='DESELECT')


def load_bone_data_search_list(context, layer_index_list):
    bone_data_list = context.window_manager.at_bone_data_search_list
    bone_data_list.clear()
    bones = []
    for i in layer_index_list:
        bones += get_layer_bones(context, i, None)
    for b in bones:
        item = bone_data_list.add()
        item.name = b.name


def set_active_collection(name):
    def traverse_tree(t):
        yield t
        for child in t.children:
            yield from traverse_tree(child)

    def get_layer_collection(layer_coll, coll_name):
        for coll in traverse_tree(layer_coll):
            if coll.name == coll_name:
                return coll

    main_collection = bpy.context.view_layer.layer_collection
    layer_coll = get_layer_collection(main_collection, name)
    if layer_coll:
        bpy.context.view_layer.active_layer_collection = layer_coll
        return True
    return False


def exclude_layer_collection(context, name, value=bool):
    active_layer_coll = context.view_layer.active_layer_collection
    if not set_active_collection(name):
        return None
    bpy.context.view_layer.active_layer_collection.exclude = value
    set_active_collection(active_layer_coll.name)


def select_object(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def create_new_armature(name):
    data = bpy.data.armatures.new(name=f"{name}_armature")
    obj = bpy.data.objects.new(name=name, object_data=data)
    bpy.context.view_layer.active_layer_collection.collection.objects.link(obj)
    return obj


def create_collection(name):
    if bpy.data.collections.get(name):
        return None
    coll = bpy.data.collections.new(name=name)
    bpy.context.scene.collection.children.link(coll)
    return coll


def make_constraints_collection(context, name="[AT]_Constraints"):
    coll = create_collection(name=name)
    if not coll:
        return bpy.data.collections.get(name)
    coll.hide_viewport = True
    coll.hide_render = True
    exclude_layer_collection(context, coll.name, True)
    return coll


def get_main_parent(obj):
    def traverse_parent_tree(ob):
        yield ob
        if ob.parent:
            yield from traverse_parent_tree(ob.parent)

    parents = [p for p in traverse_parent_tree(obj) if p != obj]
    if parents:
        return parents[-1]
    return None


def create_empty(coll, name, display_size, new=False):
    empty = bpy.data.objects.get(name)
    if empty and not new:
        return empty
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_size = display_size
    coll.objects.link(empty)
    return empty


def set_matrix_world(obj, armature, target_name):
    if not armature:
        return None
    dbone = armature.data.bones.get(target_name)
    pbone = armature.pose.bones.get(target_name)
    if not pbone:
        return None
    bone_obj = pbone.id_data
    obj.matrix_world = bone_obj.matrix_world @ dbone.matrix_local


def get_layer_bools(armature):
    return [layer for layer in armature.data.layers]


def set_layer_bools(armature, bools):
    for i in range(len(armature.data.layers)):
        armature.data.layers[i] = bools[i]


def set_all_armature_visible_layers(armature, value=bool):
    for i in range(len(armature.data.layers)):
        armature.data.layers[i] = value


def is_visible(obj, set=None):
    is_hidden = obj.hide_get()
    is_in_view = obj.hide_viewport
    if type(set) == tuple:
        obj.hide_set(set[0])
        obj.hide_viewport = set[1]
    elif set is not None:
        obj.hide_set(not set)
        obj.hide_viewport = not set
    else:
        return (is_hidden, is_in_view)


def clear_pose_location(context, armature):
    mode = context.mode.split('_')[0]
    active_obj = context.active_object
    visible = is_visible(armature)
    cur_frame = context.scene.frame_current
    layer_bools = get_layer_bools(armature)
    set_all_armature_visible_layers(armature, True)

    if mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    is_visible(armature, set=True)
    armature.select_set(True)
    context.view_layer.objects.active = armature

    bpy.ops.object.mode_set(mode='POSE')

    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.loc_clear()
    # if mode != 'OBJECT':
    bpy.ops.object.mode_set(mode=mode)

    armature.select_set(False)
    is_visible(armature, set=visible)
    active_obj.select_set(True)
    context.view_layer.objects.active = active_obj
    context.scene.frame_current = cur_frame
    set_layer_bools(armature, layer_bools)


def iterate_nla_strips(armature):
    for track in armature.animation_data.nla_tracks:
        for strip in track.strips:
            yield strip


def clear_location_keyframes(context, armature, exclude_fcurves):
    if not armature:
        return None
    if not armature.animation_data:
        return None
    transform_fcurves = [
        'location',
        'rotation_euler',
        'rotation_quaternion',
        'scale'
    ]

    def keep_it(fcurve, exclude_fcurves):
        for fc in exclude_fcurves:
            if fc not in fcurve.data_path and\
                    fcurve.data_path[-8:] == 'location':
                return False
            return True

    def clean_action(action):
        if not action:
            return None
        for fcurve in action.fcurves:
            if fcurve.data_path in transform_fcurves:
                continue
            if not keep_it(fcurve, exclude_fcurves):
                action.fcurves.remove(fcurve)

    clean_action(armature.animation_data.action)
    for strip in iterate_nla_strips(armature):
        clean_action(strip.action)

    clear_pose_location(context, armature)


def set_rigify_limb_ctrls_to_FK(obj):
    limbs = [
        "upper_arm_parent.L",
        "upper_arm_parent.R",
        "thigh_parent.L",
        "thigh_parent.R",
    ]
    bones = obj.pose.bones
    for b in limbs:
        if not bones.get(b):
            continue
        if bones[b].get('IK_FK') is not None:
            bones[b]['IK_FK'] = 1.0


def make_constraint(
    owner, target, constraint_type,
    subtarget_name=None,
    offset=None,
    mix_mode=None,
    space=None,
    own_space=None,
    euler_order=None,
    uniform=None,
):
    con = owner.constraints.new(constraint_type)
    con.name = '[AT]' + con.name
    con.target = target
    if subtarget_name is not None:
        con.subtarget = subtarget_name
    if offset is not None:
        con.use_offset = offset
    if mix_mode is not None:
        con.mix_mode = mix_mode
    if space is not None:
        con.target_space = space
        con.owner_space = own_space if own_space else space
    if euler_order is not None:
        con.euler_order = euler_order
    if uniform is not None:
        con.use_make_uniform = uniform


def remove_constraints(owner, use_filter, startsw_filter='[AT]'):
    if not hasattr(owner, 'constraints'):
        return None
    for c in owner.constraints:
        if use_filter:
            if not c.name.startswith(startsw_filter):
                continue
        owner.constraints.remove(c)


def constrain_to_complex_skeleton(armature, to_armature, owner, target, coll, euler_order, uniform):
    helper_empty = create_empty(coll, f"[helper][{to_armature.name}]_{target.name}", 0.02)
    orient_empty = create_empty(coll, f"[orient][{armature.name}]_{owner.name}", 0.02)
    remove_constraints(helper_empty, False)
    set_matrix_world(helper_empty, to_armature, target.name)
    set_matrix_world(orient_empty, armature, owner.name)
    orient_empty.parent = helper_empty
    orient_empty.matrix_parent_inverse = helper_empty.matrix_world.inverted()
    make_constraint(
        helper_empty, to_armature, 'COPY_TRANSFORMS',
        subtarget_name=target.name
    )
    make_constraint(
        owner, orient_empty, 'COPY_LOCATION',
        offset=False, space='WORLD'  # 'LOCAL' 'POSE'
    )
    make_constraint(
        owner, orient_empty, 'COPY_ROTATION',
        mix_mode='REPLACE', space='WORLD', euler_order=euler_order  # 'REPLACE' 'ADD'
    )
    make_constraint(
        owner, orient_empty, 'COPY_SCALE',
        offset=False, space='WORLD', uniform=uniform
    )


def scale_armature(context, obj, scale_value, empty_name):
    # unit_length = context.scene.unit_settings.length_unit  # 'METERS'
    unit_scale = context.scene.unit_settings.scale_length  # 1.0
    # scale_value = 0.01
    scale_factor = unit_scale / scale_value
    empty_scale = 1 / scale_factor

    main_parent = get_main_parent(obj)
    if not main_parent:
        parent_empty = create_empty(
            obj.users_collection[0], empty_name,
            0.25 * scale_factor, new=True
        )
        obj.parent = parent_empty
    elif main_parent.type != 'EMPTY':
        parent_empty = create_empty(
            obj.users_collection[0], empty_name,
            0.25 * scale_factor, new=True
        )
        main_parent.parent = parent_empty
    else:
        main_parent.name = empty_name
        parent_empty = main_parent

    transform_fcurves = [
        'location',
        'rotation_euler',
        'rotation_quaternion',
        'scale'
    ]

    if hasattr(obj.animation_data, "action"):
        parent_empty.animation_data_create()
        parent_empty.animation_data.action = obj.animation_data.action.copy()
        parent_empty.animation_data.action.name = obj.name + '_[root_transform]'
        for fc in parent_empty.animation_data.action.fcurves:
            if fc.data_path not in transform_fcurves:
                parent_empty.animation_data.action.fcurves.remove(fc)
            elif fc.data_path == 'scale':
                parent_empty.animation_data.action.fcurves.remove(fc)

        for fc in obj.animation_data.action.fcurves:
            if fc.data_path in transform_fcurves:
                obj.animation_data.action.fcurves.remove(fc)

    obj.scale.x *= scale_factor * parent_empty.scale[0]
    obj.scale.y *= scale_factor * parent_empty.scale[0]
    obj.scale.z *= scale_factor * parent_empty.scale[0]
    parent_empty.scale = (empty_scale, empty_scale, empty_scale)
    obj.select_set(True)
    mode = context.mode.split('_')[0]
    if mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mode != 'OBJECT':
        bpy.ops.object.mode_set(mode=mode)
    return parent_empty


def get_file_list_names(path, full_name=False, extension='.json'):
    file_names = []
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)) and\
                file.lower().endswith(extension):
            if full_name:
                file_names.append(file)
                continue
            name = file.split(extension)[0]
            file_names.append(name)
    return file_names


def get_module_from_path(file_path, name):
    import importlib
    if file_path is not None:
        import imp
        imp.load_source(name, file_path)
    module = importlib.import_module(name)
    return module


# Experimental
def get_ue2rigify_templates_dir():
    templates = "addons\\ue2rigify\\resources\\rig_templates"
    return os.path.join(bpy.utils.script_path_user(), templates)


def ue2rigify_template_enum(self, context):
    # path = os.path.dirname(__file__)
    folders_enum = []
    path = get_ue2rigify_templates_dir()
    for d in os.listdir(path):
        if os.path.isdir(os.path.join(path, d)):
            folders_enum.append((d, d, ''))
    return folders_enum


def ue2rigify_links_enum(self, context):
    template = self.template
    path = get_ue2rigify_templates_dir()
    template_path = os.path.join(path, template)
    files = get_file_list_names(template_path, extension="_links.json")
    return [(os.path.join(template_path, n + "_links.json"), n, '') for n in files]
