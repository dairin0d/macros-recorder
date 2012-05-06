#  ***** BEGIN GPL LICENSE BLOCK *****
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#  ***** END GPL LICENSE BLOCK *****

# <pep8-80 compliant>

bl_info = {
    "name": "Macros Recorder",
    "author": "dairin0d",
    "version": (1, 0),
    "blender": (2, 6, 0),
    "location": "Text Editor -> Text -> Record Macro",
    "description": "Record macros to text blocks",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"\
                "Scripts/Development/Macros_Recorder",
    "tracker_url": "http://projects.blender.org/tracker/"\
                   "?func=detail&aid=31325",
    "category": "Development"}
#============================================================================#

import bpy

from mathutils import Vector

class StringItem(bpy.types.PropertyGroup):
    value = bpy.props.StringProperty()

class SceneMacros(bpy.types.PropertyGroup):
    ops = bpy.props.CollectionProperty(type=StringItem)
    
    def clear(self):
        while self.ops:
            self.ops.remove(0)
    
    def make_entry(self, op):
        idname = op.bl_idname.replace("_OT_", ".").lower()
        props = op.properties
        rna_props = op.rna_type.properties
        args = []
        for k, v in props.items():
            rna_prop = rna_props[k]
            prop_type = rna_prop.type
            if prop_type == 'ENUM':
                if not rna_prop.enum_items:
                    # Somebody forgot to declare items for this enum.
                    # We can only ignore this property.
                    continue
                if rna_prop.is_enum_flag:
                    v_ = set()
                    for i in range(len(rna_prop.enum_items)):
                        if v & (1 << i):
                            v_.add(rna_prop.enum_items[i].identifier)
                    v = repr(v_)
                else:
                    v = repr(rna_prop.enum_items[v].identifier)
            else:
                is_array = (type(v).__name__ == "IDPropertyArray")
                if is_array:
                    if prop_type == 'BOOLEAN':
                        v = tuple(bool(item) for item in v)
                    else:
                        v = tuple(v)
                elif prop_type == 'BOOLEAN':
                    v = bool(v)
            args.append("%s=%s" % (k, v))
        return ("bpy.ops.%s(%s)" % (idname, ", ".join(args)))
    
    def _add(self, op):
        if isinstance(op, str):
            entry = op
        else:
            entry = self.make_entry(op)
        op_storage = self.ops.add()
        op_storage.value = entry
    
    def add(self, op):
        self._add(op)
    
    def add_diff(self, diff):
        for op in diff:
            self._add(op)
    
    def replace_last(self, op):
        if not self.ops:
            op_storage = self.ops.add()
        else:
            op_storage = self.ops[len(self.ops) - 1]
        op_storage.value = self.make_entry(op)
    
    def write_macro_text(self, textblock):
        # NOTE: we can't do a 'live update', because if the user
        # undoes past the point of textblock creation, any access
        # to texts might crash Blender (at least this happens when
        # you try to change operator's arguments after its execution)
        textblock.clear()
        code_template = \
"""
import bpy
from mathutils import Vector

class MacroOperator(bpy.types.Operator):
    bl_idname = "macro.{0}"
    bl_label = "{1}"
    
    def execute(self, context):
{2}
        return {3}

def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
""".strip()
        op_name = textblock.name.replace(".", "_")
        op_label = bpy.path.display_name(textblock.name.replace(".", " "))
        tabs = "        "
        lines = "\n".join((tabs + op.value) for op in self.ops)
        code = code_template.format(op_name, op_label, lines, "{'FINISHED'}")
        textblock.write(code)

class SceneDiff:
    def __init__(self, context):
        scene = context.scene
        wm = context.window_manager
        
        self.scene_hash = hash(scene)
        self.operators_count = len(wm.operators)
        self.selected = None
        self.active = None
        self.cursor = None
        self.pivot = None
        self.pivot_align = None
        self.orientation = None
        self.proportional = None
        self.proportional_edit = None
        self.proportional_falloff = None
    
    def process(self, context):
        scene = context.scene
        active_obj = context.object
        
        undo_redo = False
        scene_hash = hash(scene)
        if self.scene_hash != scene_hash:
            self.scene_hash = scene_hash
            undo_redo = True
        
        is_updated = False
        if active_obj:
            if 'EDIT' in active_obj.mode:
                if active_obj.is_updated or active_obj.is_updated_data:
                    is_updated = True
                data = active_obj.data
                if data.is_updated or data.is_updated_data:
                    is_updated = True
        
        selected = set(obj.name for obj in context.selected_objects)
        active = (active_obj.name if active_obj else None)
        proportional = scene.tool_settings.use_proportional_edit_objects
        proportional_edit = scene.tool_settings.proportional_edit
        proportional_falloff = scene.tool_settings.proportional_edit_falloff
        cursor = Vector(scene.cursor_location)
        
        v3d = MacroRecorder.v3d
        if v3d:
            cursor = v3d.cursor_location
            pivot = v3d.pivot_point
            pivot_align = v3d.use_pivot_point_align
            orientation = v3d.transform_orientation
        else:
            pivot = None
            pivot_align = None
            orientation = None
        
        if self.selected is None:
            self.selected = selected
        if self.active is None:
            self.active = active
        if self.proportional is None:
            self.proportional = proportional
        if self.proportional_edit is None:
            self.proportional_edit = proportional_edit
        if self.proportional_falloff is None:
            self.proportional_falloff = proportional_falloff
        if self.cursor is None:
            self.cursor = cursor
        if self.pivot is None:
            self.pivot = pivot
        if self.pivot_align is None:
            self.pivot_align = pivot_align
        if self.orientation is None:
            self.orientation = orientation
        
        wm = context.window_manager
        operators_count = len(wm.operators)
        if (operators_count != self.operators_count) or undo_redo or is_updated:
            n_added = operators_count - self.operators_count
            if n_added > 0:
                scene.macros.add_diff(wm.operators[-n_added:])
            elif undo_redo:
                scene.macros.add_diff(wm.operators)
            elif is_updated and (n_added == 0) and wm.operators:
                scene.macros.replace_last(wm.operators[-1])
            self.operators_count = operators_count
        else:
            selected_diff = selected.difference(self.selected)
            unselected_diff = self.selected.difference(selected)
            prefix = "context.scene.objects"
            for name in unselected_diff:
                scene.macros.add("%s[%s].select = False" %
                                 (prefix, repr(name)))
            for name in selected_diff:
                scene.macros.add("%s[%s].select = True" %
                                 (prefix, repr(name)))
            if active != self.active:
                scene.macros.add("{0}.active = {0}[{1}]".format(
                                 prefix, repr(name)))
            if cursor != self.cursor:
                cursor_context = ("space_data" if v3d else "scene")
                scene.macros.add("context.%s.cursor_location = %s" %
                                 (cursor_context, repr(cursor)))
            if proportional != self.proportional:
                scene.macros.add("context.scene.tool_settings."\
                                 "use_proportional_edit_objects = %s" %
                                 repr(proportional))
            if proportional_edit != self.proportional_edit:
                scene.macros.add("context.scene.tool_settings."\
                                 "proportional_edit = %s" %
                                 repr(proportional_edit))
            if proportional_falloff != self.proportional_falloff:
                scene.macros.add("context.scene.tool_settings."\
                                 "proportional_edit_falloff = %s" %
                                 repr(proportional_falloff))
            if (pivot is not None) and (pivot != self.pivot):
                scene.macros.add("context.space_data.pivot_point = %s" %
                                 repr(pivot))
            if (pivot_align is not None) and (pivot_align != self.pivot_align):
                scene.macros.add("context.space_data."\
                                 "use_pivot_point_align = %s" %
                                 repr(pivot_align))
            if (orientation is not None) and (orientation != self.orientation):
                scene.macros.add("context.space_data."\
                                 "transform_orientation = %s" %
                                 repr(orientation))
        
        if selected != self.selected:
            self.selected = selected
        if active != self.active:
            self.active = active
        if proportional != self.proportional:
            self.proportional = proportional
        if proportional_edit != self.proportional_edit:
            self.proportional_edit = proportional_edit
        if proportional_falloff != self.proportional_falloff:
            self.proportional_falloff = proportional_falloff
        if cursor != self.cursor:
            self.cursor = cursor
        if pivot != self.pivot:
            self.pivot = pivot
        if pivot_align != self.pivot_align:
            self.pivot_align = pivot_align
        if orientation != self.orientation:
            self.orientation = orientation

class MacroRecorder(bpy.types.Operator):
    """Record operators to a text block"""
    bl_idname = "wm.record_macro"
    bl_label = "Toggle macro recording"
    
    v3d = None
    
    @classmethod
    def poll(cls, context):
        return context.space_data.type in {'TEXT_EDITOR', 'VIEW_3D'}
    
    def invoke(self, context, event):
        global is_macro_recording
        global macro_window
        global macro_recorder
        
        if not is_macro_recording:
            macro_recorder = SceneDiff(context)
            
            for scene in bpy.data.scenes:
                scene.macros.clear()
            
            is_macro_recording = True
            macro_window = context.window
            
            bpy.ops.ed.undo_push(message="Record Macro")
            
            if context.space_data.type == 'VIEW_3D':
                MacroRecorder.v3d = context.space_data
            else:
                MacroRecorder.v3d = None
        else:
            text_block = bpy.data.texts.new("macro")
            context.scene.macros.write_macro_text(text_block)
            if context.space_data.type == 'TEXT_EDITOR':
                context.space_data.text = text_block
            else:
                self.report({'INFO'}, "Created %s" % text_block.name)
            
            is_macro_recording = False
            macro_window = None
            macro_text_block = None
            
            MacroRecorder.v3d = None
            
            bpy.ops.ed.undo_push(message="End Recording")
            
            macro_recorder = None
        
        return {'FINISHED'}

is_macro_recording = False
macro_window = None
macro_recorder = None

def process_diff(scene):
    if not is_macro_recording:
        return
    if bpy.context.window != macro_window:
        return
    macro_recorder.process(bpy.context)

class VIEW3D_PT_macro(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = "Macro"
    
    def draw(self, context):
        pass
    
    def draw_header(self, context):
        icon = ('CANCEL' if is_macro_recording else 'REC')
        self.layout.operator("wm.record_macro", text="", icon=icon)

def menu_func_draw(self, context):
    text = ("Recording... (Stop)" if is_macro_recording else "Record Macro")
    icon = ('CANCEL' if is_macro_recording else 'REC')
    self.layout.operator("wm.record_macro", text=text, icon=icon)

#============================================================================#
def register():
    bpy.utils.register_class(StringItem)
    bpy.utils.register_class(SceneMacros)
    bpy.utils.register_class(MacroRecorder)
    bpy.utils.register_class(VIEW3D_PT_macro)
    
    bpy.types.Scene.macros = bpy.props.PointerProperty(type=SceneMacros)
    
    bpy.types.TEXT_MT_text.append(menu_func_draw)
    
    bpy.app.handlers.scene_update_post.append(process_diff)

def unregister():
    bpy.app.handlers.scene_update_post.remove(process_diff)
    
    bpy.types.TEXT_MT_text.remove(menu_func_draw)
    
    del bpy.types.Scene.macros
    
    bpy.utils.unregister_class(VIEW3D_PT_macro)
    bpy.utils.unregister_class(MacroRecorder)
    bpy.utils.unregister_class(SceneMacros)
    bpy.utils.unregister_class(StringItem)

if __name__ == "__main__":
    register()
