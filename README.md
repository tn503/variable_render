<img src="variable_render_ui.jpg"/>

# THE VARIABLE RENDER
Render from context menu of property per setting value in input list.

# Usage
1. Run Script.
2. Select 'THE VARIABLE RENDER' from bottom of right click context menu on property.
3. Input values in shown dialog panel. There are 3 way to setting values.
   * Fifteen Toggle buttons.
   * Text box. Write values SPACE separated. and I simple implemented '..' DoubleDot Operator for range expression. START .. STOP( .. STEP).
   * 'bpy.context.selected_objects' button. I think this button is only works for select camera objects and execute on Scene > Camera
4. Press 'OK' button then rendering start. Rendering window close or 'ESC' in Rendering window then abort script.
Image saved folder of .blend file(or Scene->Output Path).

# Input values by text
- space separate.
- sharp start string to vector conversion with gamma correct. #0-9a-fA-F.
  1. #0 -> #000000FF
  2. #F0 -> #F0F0F0FF
  3. #0A3 -> #00AA33FF
  4. #FA01 -> #FFAA0011
  5. and more, #00000 -> #00000F
- DoubleDot conversion. START .. STOP( .. STEP).
- (4 5 6)
- [1 2 3]
- 'TEXT'
- o'object_name' -> try bpy.data.objects.get('object_name')

# known problem
1. prop_tabs_enum(self, "enum_tab") looks strange when invoke from sidebar(side panel).
