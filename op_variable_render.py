
import bpy

import os.path
from decimal import *
import re


def set_active_property(datablock, data_path, index, val):
    data_path = data_path.replace('[', '.').replace(']', '.')
    for i in data_path.split('.')[:-1]:
        if i:
            if i.startswith('"'):
                i = i.replace('"', '')
                datablock = datablock.get(i)
            elif i.isnumeric():
                datablock = datablock[int(i)]
            elif i.startswith("'"):
                i = i.replace("'", '')
                datablock = datablock.get(i)
            else:
                datablock = getattr(datablock, i)
    
    if index==-1:
        setattr(datablock, data_path.split('.')[-1], val)
    else:
        data = getattr(datablock, data_path.split('.')[-1])
        l = len(data)
        
        data[index] = val
        
        setattr(datablock, data_path.split('.')[-1], data)


def get_active_property(datablock, data_path, index):
    data_path = data_path.replace('[', '.').replace(']', '.')
    for i in data_path.split('.'):
        if i:
            if i.startswith('"'):
                i = i.replace('"', '')
                datablock = datablock.get(i)
            elif i.isnumeric():
                datablock = datablock[int(i)]
            elif i.startswith("'"):
                i = i.replace("'", '')
                datablock = datablock.get(i)
            else:
                datablock = getattr(datablock, i)
    
    if index!=-1:
        datablock = datablock[index]

    return datablock


def make_image_file_name(datablock, data_path, index, new_val):
    if type(new_val) is bpy.types.Object:
        new_val = new_val.name
    
    if type(new_val) in [list, tuple]:
        new_val = [str(i) for i in new_val]
    
    pattern = re.compile('["\'].*?["\']')
    
    if data_path.count('.default_value'):
        name_data_path = re.sub(r'default_value.*$', 'name', data_path)
        index_string = data_path.rpartition('default_value')[-1]
        
        prop_name = get_active_property(datablock, name_data_path, -1) + index_string
        
        path = repr(datablock) + '.' + data_path
        
        names = pattern.findall(path)
        names = [i.replace('"', '') for i in names]
        names = [i.replace('\'', '') for i in names]
        names.append(prop_name)
        
        return '-'.join(names) + f"({new_val})"
    else:
        path = repr(datablock) + '.' + data_path
        if index!=-1: path+= f'[{index}]'
        
        names = pattern.findall(path)
        names = [i.replace('"', '') for i in names]
        names = [i.replace('\'', '') for i in names]
        names.append(path.split('.')[-1])
        
        return '-'.join(names) + f"({new_val})"


def isfloat(s):
    try:
        float(s)
    except ValueError:
        return False
    else:
        return True


def parse_values_string(self, context):
    s = self.input_string
    
    def dotdot_range(start, stop, step = '0'):
        li = []
        
        if start.count('.') or stop.count('.') or step.count('.'):
            start, stop = Decimal(start), Decimal(stop)
            
            pre = int(max(len(str(start).split(".")[-1]), len(str(stop).split(".")[-1])))
            
            if step == '0':
                step = Decimal("0.1") ** Decimal(pre)
            else:
                step = Decimal(step)
            
            li = []
            li.append(start)
            while start + step <= stop:
                start+=step
                li.append(start)
            return li
            
        else:
            d = int(stop) - int(start)
            
            if step == '0':
                step = 10 ** int(len(str(d))-1)
            else:
                step = int(step)
            
            return list(range(int(start), int(stop)+1, step))


    if s.count('..'):
        rs = re.findall(r'[^\[\(]*\.\.[^\[\(\)\]]*\.\.[^\]\)]*', s)
        for i in rs:
            start = i.split('..')[0]
            stop = i.split('..')[1]
            step = i.split('..')[-1]
            
            li = dotdot_range(start, stop, step)
            
            li_string = [str(k) for k in li]
            li_string = ' '.join(li_string)
            
            s = s.replace(i , li_string)
            
        rs2 = re.findall(r'[^\[\(]*\.\.[^\]\)]*', s)
        for i in rs2:
            start = i.split('..')[0]
            stop = i.split('..')[-1]
            li = dotdot_range(start, stop)
            
            li_string = [str(k) for k in li]
            li_string = ' '.join(li_string)
            
            s = s.replace(i , li_string)

    li = []
    li2 = []
    
    def srgb_to_linearrgb(c):
        if c < 0.04045:
            return c * (1.0 / 12.92)
        else:
            return pow((c + 0.055) * (1.0 / 1.055), 2.4);
        
    if s.count('#'):
        v_size = self.active_property_size
        a = re.findall(r'#[0-9a-fA-F]+', s)
        
        for i in a:
            s = s.replace(i ,'')
            if len(i)==2:# #1 -> #111
                i = i + i[1:] + i[1:]
            if len(i)==3:# #12 -> #121212
                i = i + i[1:] + i[1:]
            if len(i)==4:# #123 -> #123F add alpha value F
                i = i + 'F'
            if len(i)==5:# #123F -> #112233FF
                i = '#'+i[1]+i[1]+i[2]+i[2]+i[3]+i[3]+i[4]+i[4]
            
            i = i[1:].ljust(8, 'F')
            vec = []
            for n, m in zip(i[::2], i[1::2]):
                val = int(n+m, 16)
                vec.append(srgb_to_linearrgb(val/255))
                
            if v_size:
                li.append(vec[:v_size])
            else:
                li.append(vec[0])
    
    names = re.findall(r"o'.*?'", s)
    for i in names:
        s = s.replace(i, '')
        ob = bpy.data.objects.get(i[1:].strip("'"))
        if ob: li.append(ob)
    
    strings = re.findall(r"'.*?'", s)
    for i in strings:
        i = i.strip("'")
        li.append(i)
        s = s.replace(i, '')

    s = s.replace('(', ' (')
    s = s.replace('[', ' [')
    
    for i in s.split():
        i = i.strip()
        
        if isfloat(i):
            li.append(Decimal(i))
                
        elif i.startswith('(') or i.startswith('['):
            li2 = []
            li , li2 = li2, li
            i = i.strip(' ()[]')
            if isfloat(i):
                li.append(Decimal(i))
        
        elif i.endswith(')') or i.endswith(']'):
            i = i.strip(' ()[]')
            if isfloat(i):
                li.append(Decimal(i))
            li , li2 = li2, li
            li.append(li2)
            li2 = []
    return li


def update_string(self, context):
    array = []
    array2 = []
    array.extend([Decimal(i) for i in self.enum1])
    array.extend([Decimal(i) for i in self.enum2])
    array.extend([Decimal(i) for i in self.enum3])
    
    array_string = parse_values_string(self, context)
    
    if [type(i) is Decimal for i in array_string].count(False):
        for i in array_string:
            if type(i) in [tuple, list]:
                array2.append([str(k) for k in i])
            elif type(i) is bpy.types.Object:
                array2.append(repr(i).replace('bpy.data.', ''))
            elif type(i) in [Decimal, int, str, float]:
                array.append(i)
            else:
                print('XX error XX', i)
                array.append('XX error XX')
        
        array = set(array)
        array = sorted(list(array))
        
        array.extend(array2)
        self.list_string = ", ".join([str(i) for i in array])
        self.list_string = self.list_string.replace("'", "")
    else:
        array.extend(array_string)
        array = set(array)
        array = sorted(list(array))
        
        self.list_string = ", ".join([str(i) for i in array])
        self.list_string = self.list_string.replace("'", "")


def make_render_jobs(self, context):
    values = parse_values_string(self, context)
    
    if not [type(i) is Decimal for i in values].count(False):
        values.extend([Decimal(i) for i in self.enum1])
        values.extend([Decimal(i) for i in self.enum2])
        values.extend([Decimal(i) for i in self.enum3])
        
        values = set(values)
        values = sorted(list(values))
    else:
        print('do not use enum property values.')
    
    if not len(values):
        print('No input values.')
        self.report({'ERROR_INVALID_INPUT'}, "ERROR_INVALID_INPUT. No input values.")
        return {'CANCELLED'}
    
    val = get_active_property(*self.context_property)
    initial_val = val
    if hasattr(val, '__len__') and callable(getattr(val, '__len__')):
        initial_val = val[:]
        
        for v in values:
            if hasattr(v, '__len__') and callable(getattr(v, '__len__')):
                if len(v) != len(initial_val):
                    self.report({'ERROR_INVALID_INPUT'}, "ERROR_INVALID_INPUT. value length error, " + str(v))
                    return {'CANCELLED'}
            else:
                self.report({'ERROR_INVALID_INPUT'}, "ERROR_INVALID_INPUT. value length error, " + str(v))
                return {'CANCELLED'}
        
    else:
        init_type = type(initial_val)
        try:
            values = [init_type(v) for v in values]
        except Exception as e:
            print("Exception", e)
            print('cast value error')
            self.report({'ERROR_INVALID_INPUT'}, "ERROR_INVALID_INPUT. cast value error.")
            return {'CANCELLED'}
    
    if type(values) is list:
        values.append(initial_val)
    elif type(values) is tuple:
        values = list(values)
        values.append(initial_val)
    else:
        values = (values, initial_val)
    
    #try set all values
    try:
        for v in values:
            set_active_property(*self.context_property, v)
    except Exception as e:
        print("Exception", e)
        set_active_property(*self.context_property, initial_val)
        
        print('set value error')
        self.report({'ERROR_INVALID_INPUT'}, "ERROR_INVALID_INPUT. set value error.")
        return {'CANCELLED'}
    
    self.jobs = []
    initial_filepath = bpy.context.scene.render.filepath
    if not bpy.data.filepath:
        path = os.path.join(bpy.context.scene.render.filepath, '(Unsaved)')
    elif self.use_blend_file_path:
        path, ext = os.path.splitext(bpy.data.filepath)
    else:
        blend_name, ext = os.path.splitext(os.path.basename(bpy.data.filepath))
        path = os.path.join(bpy.context.scene.render.filepath, blend_name)
    
    for v in values[:-1]:
        image_path = path + '_' + make_image_file_name(*self.context_property, v)
        tup = (v, image_path)
        self.jobs.append(tup)
    
    tup = (values[-1], initial_filepath)
    self.jobs.append(tup)#append initial val and path at the end of the list
    


def getter1(self): return self.enum1x
def setter1(self, val):
    if bin(val)[2:].rjust(5,'0').count('1')==1:
        self.enum1x = self.enum1x ^ val
        self.enum1x = self.enum1x | 1
    
    update_string(self, None)

def getter2(self): return self.enum2x
def setter2(self, val):
    if bin(val)[2:].rjust(5,'0').count('1')==1:
        self.enum2x = self.enum2x ^ val
        self.enum2x = self.enum2x | 1
    
    update_string(self, None)

def getter3(self): return self.enum3x
def setter3(self, val):
    if bin(val)[2:].rjust(5,'0').count('1')==1:
        self.enum3x = self.enum3x ^ val
        self.enum3x = self.enum3x | 1
    
    update_string(self, None)


STRING_CACHE = {}
def intern_enum_items(items):
    def intern_string(s):
        if not isinstance(s, str):
            return s
        global STRING_CACHE
        if s not in STRING_CACHE:
            STRING_CACHE[s] = s
        return STRING_CACHE[s]
    return [tuple(intern_string(s) for s in item) for item in items]


def enum_items_callback1(self, context):
    items = []
    base = Decimal(self.enum_tab)
    for i,k in enumerate(range(1 ,6)):
        k = k * int(self.enum_step)
        val = base * k
        tup = ( str(val), str(val), '', 2**(i+1))
        items.append(tup)
    
    return intern_enum_items(items)

def enum_items_callback2(self, context):
    items = []
    base = Decimal(self.enum_tab)
    for i,k in enumerate(range(6 ,11)):
        k = k * int(self.enum_step)
        val = base * k
        tup = ( str(val), str(val), '', 2**(i+1))
        items.append(tup)
    
    return intern_enum_items(items)

def enum_items_callback3(self, context):
    items = []
    base = Decimal(self.enum_tab)
    for i,k in enumerate(range(11 ,16)):
        k = k * int(self.enum_step)
        val = base * k
        tup = ( str(val), str(val), '', 2**(i+1) )
        items.append(tup)
    
    return intern_enum_items(items)


def update_enum_step(self, context):
    update_string(self, None)

def update_enum_tab(self, context):
    update_string(self, None)
    
def bool_update_selected_objects(self, value):
    self['selected_objects'] = False
    
    a = []
    for i in bpy.context.selected_objects:
        s = f"o'{i.name}'"
        a.append(s)
    self.input_string = " ".join(a)

def bool_update_clear_enum(self, value):
    self['clear_enum'] = False
    self.enum1x = 1
    self.enum2x = 1
    self.enum3x = 1
    update_string(self, None)
    
def bool_update_clear_textbox(self, value):
    self['clear_textbox'] = False
    self.input_string = ''
    update_string(self, None)

class Variable_Render_Operator(bpy.types.Operator):
    """Change value and render and save image"""
    bl_idname = "render.variable_render_operator"
    bl_label = "THE VARIABLE RENDER"
    bl_options = {'REGISTER'}
    
    enter_invoke = False #for prevent bpy.context.property returns None
    
    input_string: bpy.props.StringProperty(name="values", default="0.1 .. 0.3", update = update_string) 
    list_string: bpy.props.StringProperty(name="list_string")
    data_path_string: bpy.props.StringProperty(name="data_path_string")
    render_INVOKE_DEFAULT: bpy.props.BoolProperty(default = True, description='Show render view.')
    use_blend_file_path: bpy.props.BoolProperty(default = True, description='Render images are saved in the same folder as .blend file, else Scene > Output path.')
    
    selected_objects: bpy.props.BoolProperty(default = False, update=bool_update_selected_objects)
    clear_enum: bpy.props.BoolProperty(default = False, update=bool_update_clear_enum)
    clear_textbox: bpy.props.BoolProperty(default = False, update=bool_update_clear_textbox)
    
    enum_tab: bpy.props.EnumProperty(items=( ("0.001","0.001",""), ("0.01","0.01",""), ("0.1","0.1",""), ("1","1",""), ("10","10",""), ("100","100",""), ("1000","1000",""),), default='0.1', update=update_string)
    enum1x:bpy.props.IntProperty(default = 1)
    enum2x:bpy.props.IntProperty(default = 1)
    enum3x:bpy.props.IntProperty(default = 1)
    enum1: bpy.props.EnumProperty(items=enum_items_callback1, options={'ENUM_FLAG'}, set=setter1, get=getter1)
    enum2: bpy.props.EnumProperty(items=enum_items_callback2, options={'ENUM_FLAG'}, set=setter2, get=getter2)
    enum3: bpy.props.EnumProperty(items=enum_items_callback3, options={'ENUM_FLAG'}, set=setter3, get=getter3)
    
    enum_step: bpy.props.EnumProperty(items=[('1','1',''),('2', '2', ''),('3', '3', ''),('4', '4', ''),('5', '5', ''),
    ('6', '6', ''),('7', '7', ''),('8', '8', ''),('9', '9', '')], default='1', update=update_string)
    
    active_property_size: bpy.props.IntProperty(default = 0) 

    @classmethod
    def poll(cls, context):
        #return cls.enter_invoke or (context.property is not None) #for prevent context.property returns None
        if cls.enter_invoke:#for prevent context.property returns None
            return True
        elif context.property:
            datablock, data_path, index = context.property
            return (type(datablock) not in [bpy.types.Screen, bpy.types.Text])


    def render_complete_handler(self, scene, context=None):
        self.rendering = False
        print('render_complete')

    def render_cancel_handler(self, scene, context=None):
        self.rendering = False
        self.render_cancel = True
        print('render_cancel')
            
    def modal(self, context, event):
        if event.type == 'TIMER':
            if not self.rendering and not bpy.app.is_job_running('RENDER'):
                
                if self.render_cancel or (self.render_count and len(context.window_manager.windows)==1):
                    self.report({'INFO'}, "render modal Cancelled")
                    print("render modal Cancelled")
                    
                    bpy.app.handlers.render_complete.remove(self.render_complete_handler)
                    bpy.app.handlers.render_cancel.remove(self.render_cancel_handler)
                    context.window_manager.event_timer_remove(self.timer)
                    
                    if len(self.jobs):
                        set_val, image_path = self.jobs.pop()
                        bpy.context.scene.render.filepath = image_path
                        set_active_property(*self.context_property, set_val)
                    
                    return {'CANCELLED'}
                                
                if len(self.jobs):
                    set_val, image_path = self.jobs.pop(0)
                    set_active_property(*self.context_property, set_val)
                    bpy.context.scene.render.filepath = image_path
                    
                    if len(self.jobs):
                        self.rendering = True
                        self.render_count += 1
                        print('render start', self.render_count, '/', self.render_total, 'new value:', set_val)
                        
                        bpy.ops.render.render('INVOKE_DEFAULT', write_still=True)
                    else:
                        #Do not execute rendering last job. Just only set initial value.
                        self.report({'INFO'}, "render modal Done")
                        print("render modal Done. set initial value:", set_val)
                        
                        bpy.app.handlers.render_complete.remove(self.render_complete_handler)
                        bpy.app.handlers.render_cancel.remove(self.render_cancel_handler)
                        context.window_manager.event_timer_remove(self.timer)
                        return {'FINISHED'}
                    
        return {'RUNNING_MODAL'}
    
    
    def execute(self, context):
        make_render_jobs(self, context)
        
        if len(self.jobs):
            self.rendering = False
            self.render_cancel = False
            self.render_total = len(self.jobs)-1
            
            print('\njobs')
            for i in self.jobs[:-1]:
                print(i)
            
            bpy.app.handlers.render_complete.append(self.render_complete_handler)
            bpy.app.handlers.render_cancel.append(self.render_cancel_handler)

            if self.render_INVOKE_DEFAULT:
                #Control multipul bpy.ops.render.render('INVOKE_DEFAULT') needs running model.
                self.timer = context.window_manager.event_timer_add(0.1, window=context.window)
                context.window_manager.modal_handler_add(self)
                return {'RUNNING_MODAL'}
            else:
                for i, tup in enumerate(self.jobs): 
                    set_val, image_path = tup
                    set_active_property(*self.context_property, set_val)
                    bpy.context.scene.render.filepath = image_path
                    
                    if i==self.render_total:
                        #Do not execute rendering last job. Just only set initial value.
                        self.report({'INFO'}, "render Done")
                        print("render modal Done. set initial value:", set_val)
                        
                        bpy.app.handlers.render_complete.remove(self.render_complete_handler)
                        bpy.app.handlers.render_cancel.remove(self.render_cancel_handler)
                        return {'FINISHED'}
                    else:
                        self.rendering = True
                        self.render_count += 1
                        print('render start', self.render_count, '/', self.render_total, 'new value:', set_val)
                        bpy.ops.render.render(write_still=True)
        else:
            return {'CANCELLED'}
    
    
    def draw(self, context):
        layout = self.layout
        rd = context.scene.render
        box_metadata = layout.box()
        header_md, panel_md = box_metadata.panel("myvrender_metadata_info_panel_id", default_closed=True)#Blender v4.1 or later
        header_md.label(text="Output Metadata")
        
        if panel_md:
            spmd1 = panel_md.split(factor=0.25, align=True)
            spmd1.prop(rd, "use_stamp_date", text="Date")
            spmd1.prop(rd, "use_stamp_time", text="Time")
            spmd1.prop(rd, "use_stamp_render_time", text="Render Time")
            spmd1.prop(rd, "use_stamp_frame", text="Frame")
            
            spmd3 = panel_md.split(factor=0.25, align=True)
            spmd3.prop(rd, "use_stamp_frame_range", text="Frame Range")
            spmd3.prop(rd, "use_stamp_memory", text="Memory")
            spmd3.prop(rd, "use_stamp_hostname", text="Hostname")
            spmd3.prop(rd, "use_stamp_camera", text="Camera")
            
            spmd6 = panel_md.split(factor=0.25, align=True)
            spmd6.prop(rd, "use_stamp_lens", text="Lens")
            spmd6.prop(rd, "use_stamp_scene", text="Scene")
            spmd6.prop(rd, "use_stamp_marker", text="Marker")
            spmd6.prop(rd, "use_stamp_filename", text="Filename")
            
            panel_md.prop(rd, "use_stamp_note", text='Note')
            col0 = panel_md.column()
            col0.active = rd.use_stamp_note
            col0.prop(rd, "stamp_note_text", text="")
            
            panel_md.prop(rd, "use_stamp", text="Burn Into Image")
            panel_md.use_property_split = True
            
            col = panel_md.column()
            col.active = rd.use_stamp
            col.prop(rd, "stamp_font_size", text="Font Size")
            col.column().prop(rd, "stamp_foreground", slider=True)
            col.column().prop(rd, "stamp_background", slider=True)
            col.prop(rd, "use_stamp_labels", text="Include Labels")
        
        box00 = layout.box()
        header, panel = box00.panel("myvrender__context_property_info_panel_id", default_closed=True)#Blender version 4.1 or later
        header.label(text="context.property info")
        if panel:
            box0 = panel.box()
            box0.label(text = 'self.active_property : ' + str(self.active_property))
            box0.label(text = 'type(self.active_property) : ' + str(type(self.active_property)))
            
            if hasattr(self.active_property, '__len__') and callable(getattr(self.active_property, '__len__')):
                box0.label(text = 'len(self.active_property) : ' + str(len(self.active_property)))
            else:
                box0.label(text = 'len(self.active_property) : has no len()')

            box0.label(text = 'bpy.context.property:')
            box0.label(text = '    '+repr(self.context_property[0]))
            box0.label(text = '    '+str(self.context_property[1]))
            box0.label(text = '    index: ' + str(self.context_property[2]))
        
        layout.label(text = 'data path from bpy.context.property :')
        box1 = layout.box()
        box1.label(text = self.data_path_string)
        box1.label(text = ' = ' + str(self.active_property))
        
        layout.separator(type='LINE')
        
        layout.prop(self, 'selected_objects', text='bpy.context.selected_objects', toggle=1)
        
        layout.separator(factor=2)
        
        row = layout.row()
        row.prop_tabs_enum(self, "enum_tab")#looks strange when invoke from sidebar.
        row.prop_menu_enum(self, "enum_tab", text='Scale')#So same prop draw diffrent way.
        row.prop_menu_enum(self, 'enum_step', text='STEP')
        row.prop(self, 'clear_enum', text='DEL', toggle=1, icon='KEY_BACKSPACE')
        
        col1 = layout.column(align=True)
        row1 = col1.row()
        row1.prop(self, 'enum1')
        row2 = col1.row()
        row2.prop(self, 'enum2')
        row3 = col1.row()
        row3.prop(self, 'enum3')
        
        layout.separator(factor=2)
        
        sp1 = layout.split(factor=0.85)
        sp1.prop(self, 'input_string', icon='GREASEPENCIL')
        sp1.prop(self, 'clear_textbox', text='DEL', toggle=1, icon='KEY_BACKSPACE')
        
        layout.separator(factor=2)
        
        box4 = layout.box()
        box4.label(text='extract list -> '+ self.list_string)
        
        box2 = layout.box()
        image_file_name = make_image_file_name(*self.context_property, "SET_VALUES")
        box2.label(text = 'image file name : ' + image_file_name)
        
        layout.separator(factor=1)
        
        row4 = layout.row(align=True)
        row4.alignment = "RIGHT"
        row4.prop(self, 'use_blend_file_path')
        row4.prop(self, 'render_INVOKE_DEFAULT')
        
        layout.separator(type='LINE')

        
    def cancel(self, context):
        type(self).enter_invoke = False #for prevent context.property returns None

        
    def invoke(self, context, event):
        type(self).enter_invoke = True #for prevent context.property returns None

        self.render_count = 0
        self.render_cancel = False
        self.jobs = []
        
        self.context_property = bpy.context.property
        if self.context_property:
            datablock, data_path, index = self.context_property
            
            self.active_property = get_active_property(datablock, data_path, index)

            if index==-1:
                self.data_path_string = repr(datablock) + '.' + data_path
            else:
                self.data_path_string = repr(datablock) + '.' + data_path + '[' + str(index) + ']'
            
            update_string(self, context)
            
            self.active_property_size = 0
            if hasattr(self.active_property, '__len__') and callable(getattr(self.active_property, '__len__')):
                self.active_property_size = len(self.active_property)
            
            return context.window_manager.invoke_props_dialog(self, width=600)
        else:
            return {'CANCELLED'}


def the_variable_render_menu_draw_func(self, context):
    self.layout.separator()
    self.layout.operator(Variable_Render_Operator.bl_idname, text = Variable_Render_Operator.bl_label)


def register():
    classes = {'RENDER_OT_variable_render_operator',}
    
    for i in classes:
        op_class = getattr(bpy.types, i, None)
        if op_class:
            bpy.utils.unregister_class(op_class)
    

    bpy.utils.register_class(Variable_Render_Operator)

    for f in bpy.types.UI_MT_button_context_menu._dyn_ui_initialize():
        if f.__name__ == the_variable_render_menu_draw_func.__name__:
            bpy.types.UI_MT_button_context_menu.remove(f)
    
    bpy.types.UI_MT_button_context_menu.append(the_variable_render_menu_draw_func)
    

def unregister():
    bpy.utils.unregister_class(Variable_Render_Operator)
    
    bpy.types.UI_MT_button_context_menu.remove(the_variable_render_menu_draw_func)


if __name__ == "__main__":
    register()

    