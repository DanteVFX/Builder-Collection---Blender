
# import standart modules
import math

# import third-party modules
import bpy

# Initial info
bl_info = {
    "name":        "Collection Builder",
    "author":      "Dante Rueda (Darycore)",
    "version":     (1, 0, 0),
    "blender":     (3, 6, 0),
    "location":    "Outliner > Header > Collection Builder button",
    "description": "Creates standard pipeline collections under a parent collection",
    "category":    "Pipeline",
}


# Folder's color
STANDARD_COLLECTIONS = [
    ("ENV",  'COLOR_01'),
    ("CHAR", 'COLOR_04'),
    ("GEO",  'COLOR_03'),
    ("PROP", 'COLOR_02'),
    ("FX",   'COLOR_06'),
    ("LGT",  'COLOR_05'),
    ("VOL",  'COLOR_08'),
    ("CAM",  'COLOR_07'),
]

COLOR_TAG_IDS = [
    'COLOR_01', 'COLOR_02', 'COLOR_03', 'COLOR_04',
    'COLOR_05', 'COLOR_06', 'COLOR_07', 'COLOR_08',
]

COLOR_ICON_MAP = {
    'NONE':     'OUTLINER_COLLECTION',
    'COLOR_01': 'COLORSET_01_VEC',
    'COLOR_02': 'COLORSET_02_VEC',
    'COLOR_03': 'COLORSET_03_VEC',
    'COLOR_04': 'COLORSET_04_VEC',
    'COLOR_05': 'COLORSET_05_VEC',
    'COLOR_06': 'COLORSET_06_VEC',
    'COLOR_07': 'COLORSET_07_VEC',
    'COLOR_08': 'COLORSET_08_VEC',
}

_FALLBACK_TAG_COLORS = {
    'COLOR_01': (0.87, 0.22, 0.22),
    'COLOR_02': (0.90, 0.54, 0.18),
    'COLOR_03': (0.90, 0.83, 0.09),
    'COLOR_04': (0.22, 0.75, 0.22),
    'COLOR_05': (0.20, 0.55, 0.90),
    'COLOR_06': (0.55, 0.22, 0.90),
    'COLOR_07': (0.90, 0.35, 0.75),
    'COLOR_08': (0.55, 0.35, 0.18),
}


# Color Utilities

def _get_theme_tag_colors():

    try:
        theme = bpy.context.preferences.themes[0]
        colors = theme.collection_color
        return {tag: (c.color.r, c.color.g, c.color.b)
                for tag, c in zip(COLOR_TAG_IDS, colors)}

    except Exception:
        return _FALLBACK_TAG_COLORS


def _color_distance(c1, c2):

    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def nearest_color_tag(rgb_tuple):
    theme_colors = _get_theme_tag_colors()

    return min(theme_colors, key=lambda t: _color_distance(rgb_tuple, theme_colors[t]))


def tag_to_rgb(color_tag):

    return _get_theme_tag_colors().get(color_tag, (0.5, 0.5, 0.5))


# Group property
class PIPELINE_CollectionEntry(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(
        name="Enable",
        default=True,
    )
    col_name: bpy.props.StringProperty(
        name="Name",
        default="NEW",
    )
    color_rgb: bpy.props.FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        size=3,
        min=0.0, max=1.0,
        default=(0.5, 0.5, 0.5),
    )
    resolved_tag: bpy.props.StringProperty(default='NONE')


# Add slot
class PIPELINE_OT_add_entry(bpy.types.Operator):
    bl_idname = "pipeline.add_collection_entry"
    bl_label = "Add Collection"
    bl_description = "Add a new collection slot to the list"

    bl_options = {'INTERNAL'}

    def execute(self, context):
        entries = context.window_manager.pipeline_col_entries
        entry = entries.add()
        entry.col_name = "NEW"
        entry.color_rgb = (0.5, 0.5, 0.5)
        entry.enabled = True
        return {'FINISHED'}


# Remove slot
class PIPELINE_OT_remove_entry(bpy.types.Operator):
    bl_idname = "pipeline.remove_collection_entry"
    bl_label = "Remove Collection"
    bl_description = "Remove this collection slot"
    bl_options = {'INTERNAL'}

    index: bpy.props.IntProperty()

    def execute(self, context):
        entries = context.window_manager.pipeline_col_entries
        if 0 <= self.index < len(entries):
            entries.remove(self.index)
        return {'FINISHED'}



def get_collections_enum(self, context):
    items = [(col.name, col.name, "") for col in bpy.data.collections]

    return items if items else [('NONE', "No collections available", "")]


# Main Function
class PIPELINE_OT_create_collections(bpy.types.Operator):
    bl_idname = "pipeline.create_collections"
    bl_label = "Collection Builder"
    bl_options = {'REGISTER', 'UNDO'}

    parent_collection: bpy.props.EnumProperty(
        name="Parent Collection",
        description="Existing collection where the standard sets will be created",
        items=get_collections_enum,
    )
    new_collection_name: bpy.props.StringProperty(
        name="New Collection Name",
        description="New parent collection created at Scene root",
        default="",
    )
    use_new_collection: bpy.props.BoolProperty(
        name="Create new parent",
        default=False,
    )
    skip_existing: bpy.props.BoolProperty(
        name="Skip existing collections",
        default=True,
    )

    # ── Acceso a la lista compartida en WM ───────────────────────────────────
    @staticmethod
    def _entries(context):
        return context.window_manager.pipeline_col_entries

    def _has_collections(self):
        return bool(bpy.data.collections)

    def _init_entries(self, context):
        entries = self._entries(context)
        entries.clear()
        for name, default_tag in STANDARD_COLLECTIONS:
            entry = entries.add()
            entry.col_name = name
            entry.color_rgb = tag_to_rgb(default_tag)
            entry.resolved_tag = default_tag
            entry.enabled = True

    def _update_resolved_tags(self, context):
        for entry in self._entries(context):
            entry.resolved_tag = nearest_color_tag(tuple(entry.color_rgb))

    # Create the collections
    def draw(self, context):
        layout = self.layout
        has_cols = self._has_collections()
        entries = self._entries(context)

        # Collection Master
        box = layout.box()
        box.label(text="Parent Collection", icon='OUTLINER_COLLECTION')

        if has_cols:
            box.prop(self, "use_new_collection")

        row = box.row()
        row.enabled = has_cols and not self.use_new_collection
        row.prop(self, "parent_collection", text="Existing")

        row2 = box.row()
        row2.enabled = self.use_new_collection or not has_cols
        row2.prop(self, "new_collection_name", text="New name")

        if not has_cols:
            box.label(
                text="No collections in scene. Fill 'New name'.", icon='INFO')

        layout.separator()


        box2 = layout.box()
        box2.label(text="Collections to create", icon='ADD')

        # head labels
        header = box2.row(align=False)
        header.label(text="", icon='BLANK1')
        header.label(text="Name")
        header.label(text="Color pick")
        header.label(text="→ Tag")
        header.label(text="", icon='BLANK1')

        box2.separator(factor=0.3)

        self._update_resolved_tags(context)

        for i, entry in enumerate(entries):
            row = box2.row(align=True)

            # Check on/off
            row.prop(entry, "enabled", text="", icon=(
                'CHECKBOX_HLT' if entry.enabled else 'CHECKBOX_DEHLT'
            ))

            # Nombre
            sub_name = row.row()
            sub_name.enabled = entry.enabled
            sub_name.prop(entry, "col_name", text="")

            # Color picker RGB
            sub_color = row.row()
            sub_color.enabled = entry.enabled
            sub_color.prop(entry, "color_rgb", text="")

            # Preview tag
            tag_icon = COLOR_ICON_MAP.get(entry.resolved_tag, 'DOT')
            sub_tag = row.row()
            sub_tag.enabled = False
            sub_tag.label(text="", icon=tag_icon)

            # Button delete
            op = row.operator(
                "pipeline.remove_collection_entry",
                text="", icon='X', emboss=False,
            )
            op.index = i

        layout.separator()

        # Final Button at the end of the list
        add_row = layout.row()
        add_row.operator(
            "pipeline.add_collection_entry",
            text="Add Collection", icon='ADD',
        )

        layout.separator()

        box3 = layout.box()
        box3.label(
            text="Color will be mapped to nearest Blender tag", icon='INFO')

        layout.prop(self, "skip_existing")


    def invoke(self, context, event):
        self._init_entries(context)
        has_cols = self._has_collections()

        if has_cols:
            layer_coll = context.view_layer.active_layer_collection
            if layer_coll and layer_coll.collection.name in bpy.data.collections:
                self.parent_collection = layer_coll.collection.name
            self.use_new_collection = False
        else:
            self.use_new_collection = True
            self.new_collection_name = "SHOT_01"

        return context.window_manager.invoke_props_dialog(self, width=400)

    #  Execution
    def execute(self, context):
        has_cols = self._has_collections()
        use_new = self.use_new_collection or not has_cols

        # Fix Master collection name
        if use_new:
            name = self.new_collection_name.strip()
            if not name:
                self.report(
                    {'ERROR'}, "Please enter a name for the new collection")
                return {'CANCELLED'}
            parent = bpy.data.collections.new(name)
            context.scene.collection.children.link(parent)
        else:
            if self.parent_collection == 'NONE':
                self.report({'ERROR'}, "No valid parent collection selected")
                return {'CANCELLED'}
            parent = bpy.data.collections.get(self.parent_collection)
            if not parent:
                self.report(
                    {'ERROR'}, f"Collection '{self.parent_collection}' not found")
                return {'CANCELLED'}

        created, skipped, disabled = [], [], []

        for entry in self._entries(context):
            col_name = entry.col_name.strip()
            if not col_name:
                continue
            if not entry.enabled:
                disabled.append(col_name)
                continue
            if col_name in parent.children:
                if self.skip_existing:
                    skipped.append(col_name)
                    continue

            color_tag = nearest_color_tag(tuple(entry.color_rgb))
            col = bpy.data.collections.new(col_name)
            col.color_tag = color_tag
            parent.children.link(col)
            created.append(f"{col_name}({color_tag})")

        parts = []
        if created:
            parts.append(f"Created: {', '.join(created)}")
        if skipped:
            parts.append(f"Skipped: {', '.join(skipped)}")
        if disabled:
            parts.append(f"Disabled: {', '.join(disabled)}")

        self.report({'INFO'}, " | ".join(parts) if parts else "Nothing to do")
        return {'FINISHED'}


# Outliner header button
def _draw_outliner_header(self, context):

    # Enable on outliner when is istalled
    if context.space_data.display_mode != 'VIEW_LAYER':
        return
    self.layout.separator()
    self.layout.operator(
        "pipeline.create_collections",
        text="Collection Builder",
        icon='OUTLINER_COLLECTION',
    )


# Register
classes = (
    PIPELINE_CollectionEntry,
    PIPELINE_OT_add_entry,
    PIPELINE_OT_remove_entry,
    PIPELINE_OT_create_collections,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.pipeline_col_entries = bpy.props.CollectionProperty(
        type=PIPELINE_CollectionEntry
    )

    # Add button on OUTLINER
    bpy.types.OUTLINER_HT_header.append(_draw_outliner_header)


def unregister():
    bpy.types.OUTLINER_HT_header.remove(_draw_outliner_header)

    del bpy.types.WindowManager.pipeline_col_entries

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
    bpy.ops.pipeline.create_collections('INVOKE_DEFAULT')
