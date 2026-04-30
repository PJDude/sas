#!/usr/bin/env python3

####################################################################################
#
#  Copyright (c) 2025-2026 Piotr Jochymek
#
#  MIT License
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
#
####################################################################################


######################################################################################
#                                                                                    #
#                                      Disclaimer                                    #
#                                                                                    #
#    This source code was created with performance in mind (in the Python sense).    #
# It is an anti-pattern for object-oriented programming and even Python programming. #
#                                                                                    #
#                                         😎                                         #
#                                                                                    #
######################################################################################

import dearpygui.dearpygui as dpg
from dearpygui.dearpygui import create_context,get_plot_mouse_pos,set_value,get_value,bind_item_theme,item_handler_registry,plot,add_line_series,theme,configure_item,render_dearpygui_frame,is_dearpygui_running,destroy_context,theme_component,add_item_hover_handler,bind_item_handler_registry,add_mouse_click_handler,add_mouse_release_handler,add_key_press_handler,add_mouse_wheel_handler,handler_registry,add_combo,child_window,table_row,add_checkbox,add_text,add_table_column,window,table,is_item_hovered,tooltip,add_image_button,add_static_texture,texture_registry
from dearpygui.dearpygui import create_viewport,get_viewport_client_width,get_viewport_client_height,set_viewport_height,hide_item,show_item,set_item_height,set_item_width,get_viewport_height,show_viewport,set_item_pos,set_primary_window,mvTooltip
from dearpygui.dearpygui import mvEventType_Enter,mvEventType_Leave,is_key_down,get_item_configuration,group,configure_app,add_spacer,delete_item,add_plot_annotation,set_axis_limits,set_axis_ticks,add_image_series,add_shade_series,add_draw_layer,add_slider_float,add_slider_int,setup_dearpygui
from dearpygui.dearpygui import mvKey_LControl,mvKey_LShift,get_mouse_pos,get_viewport_width,get_viewport_pos,set_viewport_width,mvTable_SizingStretchProp,set_viewport_pos,get_item_rect_size,get_item_pos,output_frame_buffer,set_viewport_min_height,draw_text,move_item,draw_line,get_item_rect_min,get_item_rect_max

from time import strftime,time,localtime,perf_counter,sleep
from gc import collect as gc_collect, freeze as gc_freeze

from numpy import mean as np_mean,square as np_square,float32,ones,hanning,hamming,blackman,bartlett, abs as np_abs,fft as np_fft,log10 as np_log10,__version__ as numpy_version, concatenate as np_concatenate,sum as np_sum, arange, linspace, sin as np_sin,zeros, digitize,bincount,isnan,array as np_array, pad as np_pad, convolve as np_convolve, roll as np_roll, cumsum as np_cumsum,clip,frombuffer,uint8,inf as np_inf,multiply,float64,pi
from numpy.lib.stride_tricks import sliding_window_view
np_fft_rfft=np_fft.rfft

from threading import Thread

from sounddevice import InputStream,OutputStream,query_devices,query_hostapis,__version__ as sounddevice_version,get_portaudio_version,check_input_settings,check_output_settings,_initialize,_terminate

from collections import deque
from itertools import islice

from math import log10, ceil, floor
from PIL import Image
Image_fromarray=Image.fromarray

from pathlib import Path
from json import dumps,loads

import os
from os import name as os_name, system, sep, environ
from os.path import join as path_join,dirname,abspath

import sys
from sys import exit as sys_exit

from images import image
Image_open=Image.open

from heapq import nlargest
import logging

from io import BytesIO

windows = bool(os_name=='nt')

if windows:
    from sounddevice import WasapiSettings

console_buffer=deque()
console_buffer_len=0
console_buffer_last_elem=-1
console_buffer_max_len=1024

console_buffer_append_fun=console_buffer.append
console_buffer_popleft=console_buffer.popleft
console_visible_lines=20
console_visible_chars=40
console_visible_chars_m3=console_visible_chars-3
console_fontsize=13
console_line_height=console_fontsize-1
console_char_width=7

console_shift=console_line_height

l_info = logging.info
l_warning = logging.warning
l_error = logging.error

console_show_end_index=0
console_direction_mod=2

INFO=0
WARN=1
ERR=2
CONST=3
OPT=4

l_func={}
l_func[INFO]=l_info
l_func[WARN]=l_warning
l_func[ERR]=l_error
l_func[CONST]=l_info
l_func[OPT]=l_info

CODES=(INFO,WARN,ERR,CONST,OPT)

NO_SCROLL_CODES=(ERR,WARN,OPT)

lock_frequency=False
two_pi_by_out_samplerate=float64(0.0)
f_current=0

two_pi = pi+pi

phase = float64(0.0)

fmin,fini,fmax=14,442,30000
fmin_audio,fmax_audio=20,20000

logf_min,logf_ini,logf_max=log10(fmin),log10(fini),log10(fmax)
logf_min_audio,logf_max_audio=log10(fmin_audio),log10(fmax_audio)

current_f=fini
current_logf=logf_ini

dbmin_sample=-121.0
dbmin=-122.0
dbmin_display=-122.0
dbmax_display=dbmax=0.0

dbrange=dbmax-dbmin

dbrange_display=dbmax_display-dbmin_display

redraw_recorded_track_line=True
show_tracks=set()

VERSION_FILE='version.txt'

try:
    VER_TIMESTAMP=Path(path_join(dirname(__file__),VERSION_FILE)).read_text(encoding='ASCII').strip()
except Exception as e_ver:
    print(e_ver)
    VER_TIMESTAMP=''

print(f'{VER_TIMESTAMP=}')

title=f"Simple Audio Sweeper {VER_TIMESTAMP}"

create_context()

slider_width=10
yaxis_width=45
xaxis_height=32
plot_upper_margin=18

vw,vh=0,0

theme_text_aura=tuple([(mx,my,bool(mx==0 and my==0)) for mx in (-1,1,0) for my in (-1,1,0)])

exiting=False

ico = {}

for name, data in image.items():
    img = Image_open(BytesIO(data)).convert("RGBA")
    w, h = img.size
    with texture_registry():
        add_static_texture(w, h, [v/255 for px in list(img.get_flattened_data()) for v in px], tag=name)
    ico[name] = name

def console_buffer_append(text,code=0):
    global console_buffer,console_buffer_max_len,console_buffer_append_fun,console_buffer_popleft,console_show_end_index,console_buffer_len,console_buffer_last_elem,NO_SCROLL_CODES,console_direction_mod

    try:
        last_line_text,last_line_code=console_buffer[-1]
    except:
        last_line_text,last_line_code='',-1

    res=True
    if code in NO_SCROLL_CODES and last_line_code in NO_SCROLL_CODES and code==last_line_code and last_line_text.split(':')[0]==text.split(':')[0] :
        console_buffer[-1]=(text,code)
        res=False
    else:
        console_buffer_append_fun((text,code))
        console_direction_mod=2

        console_buffer_len=len(console_buffer)
        if console_buffer_len>console_buffer_max_len:
            popped=console_buffer_popleft()
            console_buffer_len-=1
            console_show_end_index=max(0,console_show_end_index-1)

        console_buffer_last_elem=console_buffer_len-1
    return res

def c_mess(text,code=INFO):
    func=l_func[code]
    for subline in text.split('\n'):
        res=console_buffer_append(subline,code)
        if res and subline:
            func(subline)

def cons_opt(text):
    c_mess(text,OPT)

def cons_const(text):
    c_mess(text,CONST)

def cons_err(text):
    c_mess(text,ERR)

def cons_warn(text):
    c_mess(text,WARN)

def cons_info(text):
    c_mess(text,INFO)

def exit_press(sender=None, app_data=None):
    global exiting
    exiting=True

def widget_tooltip(message,widget=None):
    if not widget:
        widget=dpg.last_item()

    tag = f"{widget}_tooltip"

    if dpg.does_item_exist(tag):
        delete_item(tag)

    with tooltip(widget, delay=0.3, tag=tag):
        add_text(message)

def slide_change(sender):
    val=get_value(sender)
    set_axis_limits("y_axis", dbmin_display*val/100, dbmax_display)

def on_viewport_resize(sender=None, app_data=None):
    global vw,vh,settings_height,cfg,console_visible_lines,console_visible_chars,console_visible_chars_m3

    vw,vh = get_viewport_client_width(),get_viewport_client_height()

    plot_height = max(plot_min_height, vh - (settings_height if cfg['settings'] else 0) -status_height -title_hight)

    set_item_height('slider', plot_height-xaxis_height-plot_upper_margin+5)
    set_item_pos('slider',[5,title_hight+plot_upper_margin+5])

    plot_width = vw-64
    set_item_height('plot', plot_height)
    set_item_width('plot', plot_width)

    set_item_pos('debug_text',[slider_width+yaxis_width+20,title_hight+plot_upper_margin])

    x_offset=80
    y_offset=title_hight+plot_height-xaxis_height-4

    set_item_pos('mark_text_1',[x_offset-1,y_offset])
    set_item_pos('mark_text_2',[x_offset-1,y_offset-1])
    set_item_pos('mark_text_3',[x_offset,y_offset-1])
    set_item_pos('mark_text_4',[x_offset+1,y_offset-1])
    set_item_pos('mark_text_5',[x_offset+1,y_offset])
    set_item_pos('mark_text_6',[x_offset+1,y_offset+1])
    set_item_pos('mark_text_7',[x_offset,y_offset+1])
    set_item_pos('mark_text_8',[x_offset-1,y_offset+1])
    set_item_pos('mark_text',[x_offset,y_offset])

    console_visible_lines = int(floor((plot_height-xaxis_height-plot_upper_margin)/console_line_height))
    console_visible_chars = int(floor((plot_width-yaxis_width)/console_char_width))-2 - (36 if DEBUG else 0)
    console_visible_chars_m3=console_visible_chars-3

COLORS={0:{},1:{}}

COLORS[0]['BG'] = (250,248,240,255)
COLORS[0]['BG_LIGHTER'] = (255,253,245,220)
COLORS[0]['CHILD_BG'] = (245,242,232,255)
COLORS[0]['BORDER'] = (210,200,180,255)
COLORS[0]['FRAME'] = (235,230,220,255)
COLORS[0]['FRAME_HOVER'] = (240,220,180,255)
COLORS[0]['FRAME_ACTIVE'] = (235,210,160,255)

COLORS[0]['INNER_SHADOW']    = (230,228,220,255)
COLORS[0]['OUTER_SHADOW']    = (240,238,230,255)
COLORS[0]['INNER_HIGHLIGHT'] = (255,255,255,255)
COLORS[0]['OUTER_HIGHLIGHT'] = (250,250,250,255)

COLORS[0]['TEXT'] = (40,35,25,255)
COLORS[0]['TEXT_AURA'] = (255,255,255,255)
COLORS[0]['TEXT_PEAKS'] = (40,35,25,150)
COLORS[0]['BUTTON'] = (245,240,230,255)
COLORS[0]['BUTTON_HOVER'] = (240,220,180,255)
COLORS[0]['BUTTON_ACTIVE'] = (230,200,150,255)
COLORS[0]['ACCENT'] = (180,140,90,255)

COLORS[0]['TOOLTIP_BG'] = (246,246,185,255)
COLORS[0]['TOOLTIP_TEXT'] = (40,35,25,255)

COLORS[0]['TRACK_CORE'] = (128,128,128,128)
COLORS[0]['TRACK_BG'] = (128,128,128,128)
COLORS[0]['TRACK_RECORDED_CORE'] = (255,110,40,255)
COLORS[0]['TRACK_RECORDED_BG'] = (255,200,200,40)
COLORS[0]['TRACK_HOVER_CORE'] = (50,200,200,255)
COLORS[0]['TRACK_HOVER_BG'] = (0,200,100,100)
COLORS[0]['FFT_LINE'] = (0,0,0,80)
COLORS[0]['FFT_LINE_AVG'] = (0,0,0,40)
COLORS[0]['FFT_LINE2'] = (245,245,245,100)
COLORS[0]['FFT_FILL'] = (170,170,150,50)
COLORS[0]['FFT_FILL_LINE'] = (180,180,180,150)

COLORS[0]['BG_CONS'] = (255,255,255,50)
COLORS[0]['CONS_INFO'] = (0,40,0,255)
COLORS[0]['CONS_WARN'] = (139,69,19,255)
COLORS[0]['CONS_ERR'] = (255,20,20,255)
COLORS[0]['CONS_CONST'] = (0,40,0,255)
COLORS[0]['CONS_OPT'] = (0,40,0,255)

COLORS[1]['BG'] = (60,60,60,255)
COLORS[1]['BG_LIGHTER'] = (40,40,40,128)
COLORS[1]['CHILD_BG'] = (60,60,65,255)
COLORS[1]['BORDER'] = (90,90,90,255)
COLORS[1]['FRAME'] = (70,70,75,255)
COLORS[1]['FRAME_HOVER'] = (100,100,150,255)
COLORS[1]['FRAME_ACTIVE'] = (120,120,200,255)

COLORS[1]['INNER_SHADOW']    = (40,40,40,255)
COLORS[1]['OUTER_SHADOW']    = (50,50,50,255)
COLORS[1]['INNER_HIGHLIGHT'] = (95,95,95,255)
COLORS[1]['OUTER_HIGHLIGHT'] = (75,75,75,255)

COLORS[1]['TEXT'] = (255,255,255,255)
COLORS[1]['TEXT_AURA'] = (0,0,0,255)
COLORS[1]['TEXT_PEAKS'] = (255,255,255,150)
COLORS[1]['BUTTON'] = COLORS[1]['BG']
COLORS[1]['BUTTON_HOVER'] = (120,120,180,255)
COLORS[1]['BUTTON_ACTIVE'] = (150,150,200,255)
COLORS[1]['ACCENT'] = (150,150,150,255)

COLORS[1]['TOOLTIP_BG'] = (246,246,185,255)
COLORS[1]['TOOLTIP_TEXT'] = (40,35,25,255)

COLORS[1]['TRACK_CORE'] = (128,128,128,128)
COLORS[1]['TRACK_BG'] = (128,128,128,128)
COLORS[1]['TRACK_RECORDED_CORE'] = (255,160,100,255)
COLORS[1]['TRACK_RECORDED_BG'] = (200,100,0,20)
COLORS[1]['TRACK_HOVER_CORE'] = (50,200,200,255)
COLORS[1]['TRACK_HOVER_BG'] = (0,200,100,100)
COLORS[1]['FFT_LINE'] = (255,255,255,130)
COLORS[1]['FFT_LINE_AVG'] = (255,255,255,40)
COLORS[1]['FFT_LINE2'] = (10,10,10,100)
COLORS[1]['FFT_FILL'] = (200,200,200,30)
COLORS[1]['FFT_FILL_LINE'] = (200,200,200,100)

COLORS[1]['BG_CONS'] = (60,60,60,255)
COLORS[1]['CONS_INFO'] = (200,235,200,255)
COLORS[1]['CONS_WARN'] = (255,215,0,255)
COLORS[1]['CONS_ERR'] = (255,170,170,255)
COLORS[1]['CONS_CONST'] = (200,235,200,255)
COLORS[1]['CONS_OPT'] = (200,235,200,255)

TI=1

themes_indexes=(0,1)
themes={}

for ti in themes_indexes:
    themes[ti]={}

    with theme() as theme_temp:
        themes[ti]['text_main']=theme_temp
        with theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_Text, COLORS[ti]['TEXT'])
        with theme_component(dpg.mvPlot):
            dpg.add_theme_color(dpg.mvPlotCol_InlayText,COLORS[ti]['TEXT'],category=dpg.mvThemeCat_Plots)

    with theme() as theme_temp:
        themes[ti]['text_aura']=theme_temp
        with theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_Text, COLORS[ti]['TEXT_AURA'])

    with theme() as theme_temp:
        themes[ti]['track_core']=theme_temp
        with theme_component(dpg.mvLineSeries):
            dpg.add_theme_color(dpg.mvPlotCol_Line,COLORS[ti]['TRACK_CORE'],category=dpg.mvThemeCat_Plots)
            dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,1.0,category=dpg.mvThemeCat_Plots)

    with theme() as theme_temp:
        themes[ti]['track_bg']=theme_temp
        with theme_component(dpg.mvLineSeries):
            dpg.add_theme_color(dpg.mvPlotCol_Line,COLORS[ti]['TRACK_BG'],category=dpg.mvThemeCat_Plots)
            dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,3.0,category=dpg.mvThemeCat_Plots)

    with theme() as theme_temp:
        themes[ti]['track_recorded_core']=theme_temp
        with theme_component(dpg.mvLineSeries):
            dpg.add_theme_color(dpg.mvPlotCol_Line,COLORS[ti]['TRACK_RECORDED_CORE'],category=dpg.mvThemeCat_Plots)
            dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,1.0,category=dpg.mvThemeCat_Plots)

    with theme() as theme_temp:
        themes[ti]['track_recorded_bg']=theme_temp
        with theme_component(dpg.mvLineSeries):
            dpg.add_theme_color(dpg.mvPlotCol_Line,COLORS[ti]['TRACK_RECORDED_BG'],category=dpg.mvThemeCat_Plots)
            dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,4.0,category=dpg.mvThemeCat_Plots)

    with theme() as theme_temp:
        themes[ti]['track_hover_core']=theme_temp
        with theme_component(dpg.mvLineSeries):
            dpg.add_theme_color(dpg.mvPlotCol_Line,COLORS[ti]['TRACK_HOVER_CORE'],category=dpg.mvThemeCat_Plots)
            dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,1.5,category=dpg.mvThemeCat_Plots)

    with theme() as theme_temp:
        themes[ti]['track_hover_bg']=theme_temp
        with theme_component(dpg.mvLineSeries):
            dpg.add_theme_color(dpg.mvPlotCol_Line,COLORS[ti]['TRACK_HOVER_BG'],category=dpg.mvThemeCat_Plots)
            dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,3.0,category=dpg.mvThemeCat_Plots)

    with theme() as theme_temp:
        themes[ti]['fft_line']=theme_temp
        with theme_component(dpg.mvLineSeries):
            dpg.add_theme_color(dpg.mvPlotCol_Line,COLORS[ti]['FFT_LINE'],category=dpg.mvThemeCat_Plots)
            dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,1.0,category=dpg.mvThemeCat_Plots)

    with theme() as theme_temp:
        themes[ti]['fft_line_fill']=theme_temp
        with theme_component(dpg.mvShadeSeries):
            dpg.add_theme_color(dpg.mvPlotCol_Fill,COLORS[ti]['FFT_FILL'],category=dpg.mvThemeCat_Plots)
            dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,1.0,category=dpg.mvThemeCat_Plots)

    with theme() as theme_temp:
        themes[ti]['fft_line_with_fill']=theme_temp
        with theme_component(dpg.mvLineSeries):
            dpg.add_theme_color(dpg.mvPlotCol_Line,COLORS[ti]['FFT_FILL_LINE'],category=dpg.mvThemeCat_Plots)
            dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,1.0,category=dpg.mvThemeCat_Plots)

    with theme() as theme_temp:
        themes[ti]['fft_line2']=theme_temp
        with theme_component(dpg.mvLineSeries):
            dpg.add_theme_color(dpg.mvPlotCol_Line,COLORS[ti]['FFT_LINE2'],category=dpg.mvThemeCat_Plots)
            dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,4.0,category=dpg.mvThemeCat_Plots)

    with theme() as theme_temp:
        themes[ti]['main']=theme_temp
        with theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, COLORS[ti]['BG'])
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, COLORS[ti]['BG'])
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, COLORS[ti]['CHILD_BG'])
            dpg.add_theme_color(dpg.mvThemeCol_Border, COLORS[ti]['BORDER'])
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, COLORS[ti]['FRAME'])
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, COLORS[ti]['FRAME_HOVER'])
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, COLORS[ti]['FRAME_ACTIVE'])

            dpg.add_theme_color(dpg.mvThemeCol_Text, COLORS[ti]['TEXT'])
            dpg.add_theme_color(dpg.mvThemeCol_Button, COLORS[ti]['BUTTON'])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, COLORS[ti]['BUTTON_HOVER'])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, COLORS[ti]['BUTTON_ACTIVE'])

            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, COLORS[ti]['ACCENT'])
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, COLORS[ti]['ACCENT'])
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, COLORS[ti]['BG'])
            dpg.add_theme_color(dpg.mvThemeCol_Header, COLORS[ti]['FRAME'])
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, COLORS[ti]['FRAME_HOVER'])
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, COLORS[ti]['FRAME_ACTIVE'])

            dpg.add_theme_color(dpg.mvThemeCol_Tab, COLORS[ti]['FRAME'])
            dpg.add_theme_color(dpg.mvThemeCol_TabHovered, COLORS[ti]['FRAME_HOVER'])
            dpg.add_theme_color(dpg.mvThemeCol_TabActive, COLORS[ti]['FRAME_ACTIVE'])
            dpg.add_theme_color(dpg.mvThemeCol_TabUnfocused, COLORS[ti]['FRAME'])
            dpg.add_theme_color(dpg.mvThemeCol_TabUnfocusedActive, COLORS[ti]['FRAME_HOVER'])

            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 0, 0, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 0, 0, category=dpg.mvThemeCat_Core)
            #4dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 2, 2, category=dpg.mvThemeCat_Core)
            #dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 0, 0, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 0, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 2, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 2, category=dpg.mvThemeCat_Core)

        with theme_component(dpg.mvChildWindow):
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 3, 3)

        with theme_component(dpg.mvPlot):
            dpg.add_theme_color(dpg.mvPlotCol_PlotBg, COLORS[ti]['BG_LIGHTER'])
            dpg.add_theme_color(dpg.mvPlotCol_InlayText,COLORS[ti]['TEXT_PEAKS'],category=dpg.mvThemeCat_Plots)

        with theme_component(mvTooltip):
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 3, 3, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg,COLORS[ti]['TOOLTIP_BG'],category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Border,COLORS[ti]['TOOLTIP_BG'], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Text, COLORS[ti]['TOOLTIP_TEXT'])
            dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize,2,category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding,4)

    with theme() as theme_temp:
        themes[ti]['fft_avg_line_theme']=theme_temp
        with theme_component(dpg.mvLineSeries):
            dpg.add_theme_color(dpg.mvPlotCol_Line,COLORS[ti]['FFT_LINE_AVG'],category=dpg.mvThemeCat_Plots)
            dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,4.0,category=dpg.mvThemeCat_Plots)

with theme() as red_cursor_theme:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line,(255, 60, 60, 255),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,1.0,category=dpg.mvThemeCat_Plots)

with theme() as green_line_theme:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line,(30, 200, 0, 200),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,1.0,category=dpg.mvThemeCat_Plots)

with theme() as grid_line_theme:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line,(128, 128, 128, 128),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,1.0,category=dpg.mvThemeCat_Plots)


###################################################
def build_gui():
    with window(tag='main',no_title_bar=True,no_scrollbar=True,no_resize=True,no_move=True) as main:
        set_primary_window(main, True)

        add_draw_layer(tag='draw_layer')

        if not decorated:
            with group(tag='decoration',horizontal=True):
                with table(header_row=False,resizable=False, policy=mvTable_SizingStretchProp,borders_outerH=False, borders_innerV=False, borders_outerV=False):
                    add_table_column( width_fixed=True, init_width_or_weight=5)
                    add_table_column( width_fixed=True, init_width_or_weight=16)
                    add_table_column( width_fixed=True, init_width_or_weight=300)
                    add_table_column( width_stretch=True, init_width_or_weight=10)
                    add_table_column( width_fixed=True, init_width_or_weight=16)
                    add_table_column( width_fixed=True, init_width_or_weight=3)

                    with table_row():
                        add_spacer(height=3)

                    with table_row():
                        add_spacer(width=3)
                        add_image_button(ico["sas_small"],callback=None)
                        add_text(title)
                        add_spacer()
                        add_image_button(ico["exit_dark"],tag='exit_button',callback=exit_press)
                        widget_tooltip('Exit')
                        add_spacer(width=3)

                    with table_row():
                        add_spacer(height=3)

        with table(header_row=False, resizable=False, policy=mvTable_SizingStretchProp,
            borders_innerH=False, borders_innerV=False, borders_outerH=False, borders_outerV=False,
            row_background=False, context_menu_in_body=False, freeze_rows=0, freeze_columns=0,
            no_host_extendX=False, no_host_extendY=False, pad_outerX=False, no_pad_outerX=True):

            add_table_column(width_stretch=True, init_width_or_weight=-1)

            with table_row():
                with group(tag='plot_combo',horizontal=True):

                    add_spacer(width=6)

                    add_slider_float(tag='slider',callback=slide_change,vertical=True,max_value=30,min_value=100,default_value=100,format="",width=slider_width,track_offset=0.5)
                    widget_tooltip('Adjust dynamic range')

                    with plot(tag='plot',no_mouse_pos=True,no_menus=True,no_frame=True):
                        yticks = (('dBFS',00),('-10',-10),("-20",-20),('-30',-30),('-40',-40),('-50',-50),('-60',-60),('-70',-70),('-80',-80),('-90',-90), ("-100",-100), ("-110",-110), ("-120",-120))
                        xticks = (('',10),("20Hz",20),('',30),('',40),('',50),('',60),('',70),('',80),('',90), ("100Hz",100),
                            ('',200),('',300),('',400),('',500),('',600),('',700),('',800),('',900),("1kHz",1000),
                            ("",2000),("",3000),("",4000),("",5000),("",6000),("",7000),("",8000),("",9000),("10kHz",10000),("20kHz",20000))
                        add_plot_annotation(tag='cursor_f_txt',label='',default_value=(10, -5), color=(0, 0, 0, 0), offset=(5,0))
                        add_plot_annotation(tag='cursor_db_txt',label='',default_value=(100, -30), color=(0, 0, 0, 0), offset=(0,0))

                        with dpg.plot_axis(dpg.mvXAxis, tag='x_axis',no_highlight=True) as xaxis:
                            configure_item(dpg.last_item(),scale=dpg.mvPlotScale_Log10)
                            set_axis_limits("x_axis", fmin,fmax)
                            set_axis_ticks("x_axis", xticks)

                        with dpg.plot_axis(dpg.mvYAxis, tag = 'y_axis',no_highlight=True):
                            set_axis_limits("y_axis", dbmin_display, dbmax_display)

                            add_image_series(tag='plotbg',texture_tag=ico['bg'],bounds_min=(0, -280),bounds_max=(40000, 0),parent='y_axis')
                            set_axis_ticks("y_axis", yticks)

                            add_line_series((0,0),(dbmin,0),tag="cursor_f")
                            bind_item_theme("cursor_f",red_cursor_theme)

                            add_line_series([20], [-120], tag="fft_line2")

                            add_line_series([20], [-120], tag="fft_line")
                            add_shade_series([20], y1=[-120], tag="fft_line_shade")

                            add_line_series([20], [-120], tag="fft_avg")

                            for lab,val in xticks:
                                if lab:
                                    add_line_series([val,val], [-130,0],tag=f'stick{val}')
                                    bind_item_theme(f'stick{val}',grid_line_theme)

                            for track in range(tracks):
                                add_line_series([20], [-120], tag=f"track{track}_bg",user_data=track,show=False)
                                add_line_series([20], [-120], tag=f"track{track}",user_data=track,show=False)

                    with group(tag='buttons'):
                        add_spacer(height=6)
                        with item_handler_registry(tag="tracks_handlers"):
                            add_item_hover_handler(event_type=mvEventType_Enter,callback=on_mouse_move_tracks_enter)
                            add_item_hover_handler(event_type=mvEventType_Leave,callback=on_mouse_move_tracks_leave)

                        for track_temp in range(tracks):
                            add_image_button(ico[f"{track_temp+1}_off"],tag=f'showcheck{track_temp}',callback=track_action_callback,user_data=track_temp); widget_tooltip(f'Show/Hide track:{track_temp+1}\nwith Ctrl - toggle recording')
                            bind_item_handler_registry(f'showcheck{track_temp}', "tracks_handlers")

                        add_spacer(height=20)
                        add_image_button(ico["reset"],tag='resetrack',callback=reset_track_press); widget_tooltip('Reset selected track samples\n\nkey: Delete')

                        add_spacer(height=20)
                        add_image_button(ico["play"],tag='sweeping',callback=sweep_callback); widget_tooltip('Run frequency sweep\n\nA track must be selected and recording\nmust be enabled before starting the sweep.')
                        add_spacer(height=20)
                        add_image_button(ico["settings"],callback=settings_wrapper_toggle); widget_tooltip("Show settings\n\nkey: F12")

            with table_row():
                with group(horizontal=True,tag='settings_group'):
                    add_spacer(width=5)

                    c0width=80
                    c1width=260
                    with child_window(border=True,autosize_y=False,autosize_x=False,width=c0width+c1width+c1width,no_scrollbar=True,height=settings_height-5):
                        with group(width=-1):
                            with table(header_row=False, resizable=False, policy=mvTable_SizingStretchProp):
                                add_table_column(width_fixed=True, init_width_or_weight=16, width=16)
                                add_table_column(width_fixed=True, init_width_or_weight=120)

                                with table_row():
                                    add_image_button(ico["refresh"],tag='sd_reinit',width=16,callback=sd_reinit_callback); widget_tooltip('Re-Initialize SoundDevice module')
                                    add_text(default_value='AUDIO INTERFACE')

                            dpg.add_separator()

                            with table(header_row=False, resizable=False, policy=mvTable_SizingStretchProp,
                                        borders_innerH=False, borders_innerV=False, borders_outerH=False, borders_outerV=False,
                                        row_background=False, context_menu_in_body=False, freeze_rows=0, freeze_columns=0,
                                        no_host_extendX=False, no_host_extendY=False, pad_outerX=False, no_pad_outerX=True):

                                add_table_column(width_fixed=True, init_width_or_weight=c0width, width=c0width)
                                add_table_column(width_fixed=True, init_width_or_weight=c1width, width=c1width)
                                add_table_column(width_fixed=True, init_width_or_weight=c1width, width=c1width)

                                with table_row():
                                    add_text(default_value=' ')

                                    with table(header_row=False, resizable=False, policy=mvTable_SizingStretchProp):
                                        add_table_column(width_fixed=True, init_width_or_weight=16, width=16)
                                        add_table_column(width_fixed=True, init_width_or_weight=16, width=16)
                                        add_table_column(width_fixed=True, init_width_or_weight=40)
                                        add_table_column(width_fixed=True, init_width_or_weight=240,width=240)

                                        with table_row():
                                            add_image_button(ico["refresh"],tag='out_reinit',width=16,callback=out_reinit_callback); widget_tooltip('Re-Initialize Output Stream')
                                            dpg.add_image(ico["out_off"],tag='out_status',width=16); widget_tooltip('Output Stream status')
                                            add_text(default_value='Output')
                                            add_slider_int(tag='amplitude',callback=amplitude_callback,max_value=100,min_value=0,default_value=cfg['amplitude'],format="%d",track_offset=0.5,width=150); widget_tooltip('Amplitude')

                                    with table(tag='in_tab1',header_row=False, resizable=False, policy=mvTable_SizingStretchProp):
                                        add_table_column(width_fixed=True, init_width_or_weight=16, width=16)
                                        add_table_column(width_fixed=True, init_width_or_weight=16, width=16)
                                        add_table_column(width_fixed=True, init_width_or_weight=80)
                                        with table_row():
                                            add_image_button(ico["refresh"],tag='in_reinit',width=16,callback=in_reinit_callback); widget_tooltip('Re-Initialize Input Stream')
                                            dpg.add_image(ico["in_off"],tag='in_status',width=16); widget_tooltip('Input Stream status')
                                            add_text(default_value='Input')

                                with table_row():
                                    latency_tooltip="The latency of the stream in seconds.\nA value that is too low may\nproduce inaccurate spectrum readings."
                                    blocksize_tooltip="Number of frames per block.\nThe special value 0 means that\nthe blocksize can change between blocks.\nA higher value is more secure, but increases latency."

                                    with group(width=-1):
                                        add_text(default_value='API')
                                        add_text(default_value=' ')
                                        add_text(default_value='Device')
                                        add_text(default_value='Channels')
                                        add_text(default_value='Sample rate')
                                        add_text(default_value='Latency') ; widget_tooltip(latency_tooltip)
                                        add_text(default_value='Block size') ; widget_tooltip(blocksize_tooltip)

                                    with group(width=-1):
                                        add_combo(tag='out_api',default_value='',callback=out_api_callback,width=c1width,user_data=True)
                                        add_checkbox(tag='out_wasapi_exclusive',label='WASAPI Exclusive Mode',callback=out_wasapi_exclusive_callback,default_value=cfg['out_wasapi_exclusive'],user_data=True,enabled=windows); widget_tooltip('WASAPI Exclusive Mode\n\nExclusive mode allows to deliver audio\ndata directly to hardware bypassing software mixing\n\n(Windows only)')

                                        add_combo(tag='out_dev',default_value='',callback=out_dev_changed, height_mode=dpg.mvComboHeight_Largest,user_data=True)
                                        add_combo(tag='out_channel',default_value=cfg['out_channel'],callback=out_channel_changed,user_data=True)
                                        add_combo(tag='out_samplerate',default_value='',callback=out_samplerate_changed,user_data=True)

                                        add_combo(tag='out_latency',label='',callback=out_latency_changed,items=latency_values,default_value=cfg['out_latency'],user_data=True); widget_tooltip(latency_tooltip)
                                        add_combo(tag='out_blocksize',label='',callback=out_blocksize_changed,items=out_blocksize_values,default_value=cfg['out_blocksize'],user_data=True) ; widget_tooltip(blocksize_tooltip)

                                    with group(width=-1):
                                        add_combo(tag='in_api',default_value='',callback=in_api_callback,width=c1width,user_data=True)

                                        with group(horizontal=True):
                                            add_checkbox(tag='allow_all_devices',label='All',callback=in_api_callback,default_value=cfg['allow_all_devices'],user_data=True); widget_tooltip('Show all devices\n(outputs included)')
                                            add_checkbox(tag='in_wasapi_exclusive',label='WASAPI Exclusive',callback=in_wasapi_exclusive_callback,default_value=cfg['in_wasapi_exclusive'],user_data=True,show=False); widget_tooltip('Exclusive mode allows to receive audio\ndata directly to hardware bypassing software mixing')

                                        add_combo(tag='in_dev',default_value='',callback=in_dev_changed,user_data=True, height_mode=dpg.mvComboHeight_Largest)
                                        add_combo(tag='in_channel',default_value='',callback=in_channel_changed,user_data=True)
                                        add_combo(tag='in_samplerate',default_value='',callback=in_samplerate_changed,user_data=True)

                                        add_combo(tag='in_latency',label='',callback=in_latency_changed,items=latency_values,default_value='',user_data=True); widget_tooltip(latency_tooltip)
                                        add_combo(tag='in_blocksize',label='',callback=in_blocksize_changed,items=in_blocksize_values,default_value='',user_data=True) ; widget_tooltip(blocksize_tooltip)

                    with child_window(border=True,autosize_y=False,autosize_x=False,width=220,no_scrollbar=True,height=settings_height-5):
                        with group(width=-1):
                            add_checkbox(tag='fft',label='FFT',callback=fft_callback,default_value=cfg['fft']); widget_tooltip('Calculate and show\nreal-time FFT graph')
                            dpg.add_separator()

                            with table(header_row=False, resizable=False, policy=mvTable_SizingStretchProp,
                                    borders_innerH=False, borders_innerV=False, borders_outerH=False, borders_outerV=False,
                                    row_background=False, context_menu_in_body=False, freeze_rows=0, freeze_columns=0,
                                    no_host_extendX=False, no_host_extendY=False, pad_outerX=False, no_pad_outerX=True):

                                c2width=130
                                add_table_column(width_fixed=True, init_width_or_weight=70, width=70)
                                add_table_column(width_fixed=True, init_width_or_weight=c2width, width=c2width)

                                with table_row():
                                    add_text(default_value='size'); FFT_size_tooltip='FFT size\n\nF3 / Shift+F3'; widget_tooltip(FFT_size_tooltip)
                                    add_combo(tag='fft_size',items=FFT_items,default_value=cfg['fft_size'],callback=fft_size_callback,width=c2width); widget_tooltip(FFT_size_tooltip)
                                with table_row():
                                    add_text(default_value='window'); FFT_window_tooltip='FFT window\n\nF4 / Shift+F4' ; widget_tooltip(FFT_window_tooltip)
                                    add_combo(tag='fft_window',items=['ones','hanning','hamming','blackman','bartlett'],default_value=cfg['fft_window'],callback=fft_window_callback,width=c2width); widget_tooltip(FFT_window_tooltip)

                                FFT_buckets_tooltip='Frequency Bin Aggregation\n(equal frequency "buckets" on log scale)\n\nkey: F5 / Shift+F5, (+Ctrl Toggle)'
                                with table_row():
                                    add_checkbox(tag='fft_fba',label='FBA',callback=fft_fba_callback,default_value=cfg['fft_fba']); widget_tooltip(FFT_buckets_tooltip)
                                    add_combo(tag='fft_fba_size',items=FBA_items,default_value=cfg['fft_fba_size'],callback=fft_fba_size_callback,user_data=True,width=c2width); widget_tooltip(FFT_buckets_tooltip)
                                with table_row():
                                    add_checkbox(tag='fft_smooth',label='Smth',callback=fft_smooth_callback,default_value=cfg['fft_smooth']); FFT_smoothing_tooltip='Smoothing\n\nkey: F6 / Shift+F6 (+Ctrl Toggle)'; widget_tooltip(FFT_smoothing_tooltip)
                                    add_slider_int(tag='fft_smooth_factor',callback=fft_smooth_factor_callback,max_value=12,min_value=1,default_value=cfg['fft_smooth_factor'],format="%d",width=130,track_offset=0.5); widget_tooltip(FFT_smoothing_tooltip)
                                with table_row():
                                    add_checkbox(tag='fft_tda',label='TDA',callback=fft_tda_callback,default_value=cfg['fft_tda']); FFT_tda_tooltip='Time Domain Averaging\n\nkey: F7 / Shift+F7 (+Ctrl Toggle)'; widget_tooltip(FFT_tda_tooltip)
                                    add_slider_float(tag='fft_tda_factor',callback=fft_tda_factor_callback,max_value=0.95,min_value=0.05,default_value=cfg['fft_tda_factor'],format="%.2f",width=130,track_offset=0.5); widget_tooltip(FFT_tda_tooltip)

                                with table_row():
                                    add_checkbox(tag='peaks',label='Peaks',callback=peaks_callback,default_value=cfg['peaks']); widget_tooltip('Peaks detection')

                                with table_row():
                                    add_text(default_value='Avarage')
                                    add_slider_int(tag='peaks_avg_factor',callback=peaks_avg_factor_change,max_value=100,min_value=1,default_value=cfg['peaks_avg_factor'],width=130,track_offset=0.5); widget_tooltip('Reference average - relative length factor')

                                with table_row():
                                    add_text(default_value='Distance')
                                    add_slider_int(tag='peaks_dist_factor',callback=peaks_distance_change,max_value=100,min_value=1,default_value=cfg['peaks_dist_factor'],width=130,track_offset=0.5); widget_tooltip('relative distance of neighbours')

                                with table_row():
                                    add_text(default_value='Limit')
                                    add_slider_int(tag='peaks_limit',callback=peaks_limit_change,max_value=32,min_value=1,default_value=cfg['peaks_limit'],width=130,track_offset=0.5); widget_tooltip('Absolute limit of peaks shown')

                    with group():
                        with child_window(border=True,autosize_y=False,autosize_x=False,width=210,no_scrollbar=True,height=71):
                            with group(width=-1):
                                add_text(default_value='TRACKS')
                                dpg.add_separator()

                                with table(header_row=False, resizable=False, policy=mvTable_SizingStretchProp,
                                        borders_innerH=False, borders_innerV=False, borders_outerH=False, borders_outerV=False,
                                        row_background=False, context_menu_in_body=False, freeze_rows=0, freeze_columns=0,
                                        no_host_extendX=False, no_host_extendY=False, pad_outerX=False, no_pad_outerX=True):

                                    c2width=130
                                    add_table_column(width_fixed=True, init_width_or_weight=60, width=60)
                                    add_table_column(width_fixed=True, init_width_or_weight=c2width, width=c2width)

                                    with table_row():
                                        add_text(default_value='buckets')
                                        add_combo(tag='track_buckets',items=['64','128','256'],default_value=cfg['track_buckets'],callback=tracks_buckets_quant_change,width=c2width)
                                    with table_row():
                                        add_text(default_value='TDA'); FFT_tooltip6='Time domain averaging'; widget_tooltip(FFT_tooltip6)
                                        add_slider_float(tag='tracks_tda_factor',callback=tracks_tda_factor_callback,max_value=0.95,min_value=0.05,default_value=cfg['tracks_tda_factor'],format="%.2f",width=130,track_offset=0.5); widget_tooltip(FFT_tooltip6)

                        with child_window(border=True,autosize_y=False,autosize_x=False,width=210,no_scrollbar=True,height=106):
                            with group():
                                add_text(default_value='DISPLAY SETTINGS')
                                dpg.add_separator()
                                with group(horizontal=True):
                                    with group():
                                        add_checkbox(tag='debug',label='Debug',callback=debug_callback,default_value=cfg['debug']); widget_tooltip('key: F11')
                                        add_checkbox(tag='decorated',label='Decorate',callback=decorated_callback,default_value=cfg['decorated']); widget_tooltip('Restore default window decorations.\nUse if you experience problems with\ndragging or resizing the main window.\n(Requires application restart)')
                                        with group(horizontal=True):
                                            add_text(default_value='Theme:')
                                            add_image_button(ico["light"],callback=lambda : theme_callback(0),width=16); widget_tooltip("Light theme\n\nkey:L")
                                            add_image_button(ico["dark"],callback=lambda : theme_callback(1),width=16); widget_tooltip("Dark theme\n\nkey:D")
                                        add_spacer(width=100)
                                    with group():
                                        add_checkbox(tag='pause',label='Pause',callback=pause_callback,default_value=False); widget_tooltip('key: Space')

                                        add_checkbox(tag='fft_fill',label='FFT Fill',callback=fft_fill_callback,default_value=cfg['fft_fill']); widget_tooltip("Filled graph\n\nkey:G")
                                        add_spacer(width=100)

                    with group(horizontal=True):
                        add_spacer(width=3)

                        with group():
                            add_image_button(ico["save_pic"],tag='save_image',callback=save_image); widget_tooltip("Save .png file\n\nkey: S")
                            add_image_button(ico["save_csv"],tag='save_csv_button',callback=save_csv); widget_tooltip("Save .csv file of selected track\n\nkey: C")
                            add_spacer(height=16)
                            add_image_button(ico["license"],tag='licensex',callback=license_wrapper); widget_tooltip('Show License\n\nkey: F2')
                            add_image_button(ico["about"],tag='aboutx',callback=about_wrapper); widget_tooltip("Show About\n\nkey: F1")
                            add_spacer(height=16)
                            add_image_button(ico["home"],tag='homepage',callback=go_to_homepage); widget_tooltip(f'Visit project homepage ({HOMEPAGE})')

                        add_spacer(width=3)

        add_text(tag='debug_text',default_value='')

        add_text(tag='mark_text_1',default_value=title,show=False)
        add_text(tag='mark_text_2',default_value=title,show=False)
        add_text(tag='mark_text_3',default_value=title,show=False)
        add_text(tag='mark_text_4',default_value=title,show=False)
        add_text(tag='mark_text_5',default_value=title,show=False)
        add_text(tag='mark_text_6',default_value=title,show=False)
        add_text(tag='mark_text_7',default_value=title,show=False)
        add_text(tag='mark_text_8',default_value=title,show=False)
        add_text(tag='mark_text',default_value=title,show=False)

        with handler_registry():
            add_mouse_click_handler(callback=click_callback)
            add_mouse_release_handler(callback=release_callback)
            add_mouse_wheel_handler(callback=wheel_callback)
            add_key_press_handler(callback=key_press_callback)

            dpg.add_mouse_down_handler(button=0, callback=on_mouse_down)
            dpg.add_mouse_move_handler(callback=on_mouse_move)

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    EXECUTABLE_DIR = Path(sys._MEIPASS)
else:
    EXECUTABLE_DIR = Path(__file__).parent

if getattr(sys, 'frozen', False):
    EXECUTABLE_DIR_REAL = os.path.dirname(sys.executable)
else:
    EXECUTABLE_DIR_REAL = os.path.dirname(abspath(__file__))

print(f'{EXECUTABLE_DIR=}')
print(f'{EXECUTABLE_DIR_REAL=}')

INTERNAL_DIR = sep.join([EXECUTABLE_DIR_REAL,"data"])
INTERNAL_DIR_CSV_DEBUG = sep.join([INTERNAL_DIR,'debug'])
INTERNAL_DIR_CSV = sep.join([INTERNAL_DIR,'csv'])
INTERNAL_DIR_LOGS = sep.join([INTERNAL_DIR,'log'])
INTERNAL_DIR_IMAGES = sep.join([INTERNAL_DIR,'img'])

Path(INTERNAL_DIR_LOGS).mkdir(parents=True,exist_ok=True)

Path(INTERNAL_DIR).mkdir(parents=True,exist_ok=True)

CAPTURE_TIME = 60.0
CAPTURE_FPS = 30
CAPTURE_INTERVAL = 1.0 / CAPTURE_FPS
CAPTURE=False
CAPTURE_saving=False

print(f'{INTERNAL_DIR=}')

def localtime_catched(t):
    try:
        #mtime sometimes happens to be negative (Virtual box ?)
        return localtime(t)
    except:
        return localtime(0)

log_file = path_join(INTERNAL_DIR_LOGS, strftime('%Y_%m_%d-%H_%M_%S',localtime_catched(time()) ) +'.txt')
cfg_file = path_join(INTERNAL_DIR, 'cfg.json')

print(f'{log_file=}')

cfg={}

try:
    with open(cfg_file, "r", encoding="utf-8") as f:
        cfg=loads(f.read())
    print(f'cfg_file "{cfg_file}" opened successfully')
except Exception as e:
    print(f'cfg file "{cfg_file}" opening error {e}')

tracks=8

cfg.setdefault('theme',1)
cfg.setdefault('track_buckets',256)
cfg.setdefault('viewport_pos',None)
cfg.setdefault('settings',False)

cfg.setdefault('decorated',False)
cfg.setdefault('fft_fill',True)

PAUSE=False

cfg.setdefault('debug',False)

cfg.setdefault('fft',True)
cfg.setdefault('fft_size',4096)
cfg.setdefault('fft_window','blackman')
cfg.setdefault('fft_fba',True)
cfg.setdefault('fft_fba_size',1024)

cfg.setdefault('fft_tda',False)
cfg.setdefault('fft_tda_factor',0.1)

cfg.setdefault('fft_smooth',True)
cfg.setdefault('fft_smooth_factor',2)

cfg.setdefault('tracks_tda_factor',0.3)

cfg.setdefault('peaks',False)
cfg.setdefault('peaks_avg_factor',10)
cfg.setdefault('peaks_dist_factor',10)
cfg.setdefault('peaks_limit',3)

cfg.setdefault('show_track',[False]*tracks)
cfg.setdefault('recorded',-1)

cfg.setdefault('in_api','Windows WASAPI' if windows else 'ALSA')
cfg.setdefault('out_api','Windows WASAPI' if windows else 'ALSA')

cfg.setdefault("out_dev",None)
cfg.setdefault("in_dev",None)

cfg.setdefault("in_channel","1")
cfg.setdefault("out_channel","1")

cfg.setdefault("in_samplerate",'44100')
cfg.setdefault("out_samplerate",'44100')

cfg.setdefault("in_latency",'default')
cfg.setdefault("out_latency",'default')

cfg.setdefault("in_blocksize",'default')
cfg.setdefault("out_blocksize",'default')

cfg.setdefault("allow_all_devices",False)
cfg.setdefault("out_wasapi_exclusive",False)
cfg.setdefault("in_wasapi_exclusive",False)
#cfg.setdefault("dithering_off",True)
cfg.setdefault("amplitude",30)

latency_values=('high','low','default')

FFT_items=('512','1024','2048','4096','8192','16384','32768','65536','131072','262144','524288','1048576','2097152')
FBA_items=('512','1024','2048','4096')

out_blocksize_values=(1024,512,256,128,64,'default')
in_blocksize_values=(512,256,128,64,'default')

track_line_data_y={}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
            logging.FileHandler(log_file, encoding='utf-8')
    ]
)

TARGET_FPS=60

if windows:
    from os import startfile
    import ctypes

    user32 = ctypes.windll.user32

    ShowCursor = user32.ShowCursor
    LoadCursorW = user32.LoadCursorW
    SetCursor = user32.SetCursor

    IDC_ARROW    = 32512
    IDC_SIZEALL  = 32646
    IDC_CROSS    = 32515
    IDC_HAND     = 32649

    def load_cursor(idc_id):
        l_info('cursor_loaded')
        return LoadCursorW(None, idc_id)

    arrow_cursor = load_cursor(IDC_ARROW)

    try:
        hdc = user32.GetDC(None)
        rate = ctypes.windll.gdi32.GetDeviceCaps(hdc, 116)
        user32.ReleaseDC(None, hdc)
        if rate > 0:
            TARGET_FPS=float(rate)
            print(f'{TARGET_FPS=}')
    except Exception as fps_e:
        print(f'{fps_e=}')

    import psutil
    try:
        psutil.Process(os.getpid()).nice(psutil.HIGH_PRIORITY_CLASS)
    except Exception as prior_e:
        print(f'{prior_e=}')

    def round_viewport():
        try:
            hwnd = user32.FindWindowW("GLFW30", None) or user32.GetForegroundWindow()
            try:
                dwmapi = ctypes.windll.dwmapi
                val = ctypes.c_int(2)  # DWMWCP_ROUND
                dwmapi.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(val), ctypes.sizeof(val))
            except Exception as r1e:
                print(f'{r1e=}')
                w, h, r = dpg.get_viewport_width(), dpg.get_viewport_height(), 12
                rgn = ctypes.windll.gdi32.CreateRoundRectRgn(0, 0, w + 1, h + 1, r, r)
                user32.SetWindowRgn(hwnd, rgn, True)
        except Exception as r2e:
            print(f'{r2e=}')
else:
    try:
        import subprocess, re
        out = subprocess.check_output(["xrandr"], text=True)
        m = re.search(r"(\d+\.\d+)\*", out)
        if m:
            TARGET_FPS=float(m.group(1))
            print(f'{TARGET_FPS=}')
    except Exception as fps_e:
        print(f'{fps_e=}')

    def round_viewport():
        pass

settings_height=186

decorated=cfg['decorated']
FFT_FILL=cfg['fft_fill']

title_hight=(0 if decorated else 34)
status_height=20
plot_min_height=306

viewport_height_min=(plot_min_height+status_height+title_hight,
                     plot_min_height+status_height+title_hight+settings_height)

viewport_width_min=1110

cfg.setdefault('viewport_height',viewport_height_min[0])
cfg.setdefault('viewport_width',viewport_width_min)

create_viewport(title=title,vsync=False,decorated=decorated)

HOMEPAGE='https://github.com/PJDude/sas'

f_current=0
playing_state=0
'''
2 - on
1 - ramp on
0 - off
-1 - ramp off
'''

sweeping=False

def catch(func):
    def wrapper(*args,**kwargs):
        try:
            return func(*args,**kwargs)
        except Exception as e:
            l_error(f'catch:{func},{e}')
            print(f'catch:{func},{e}')
            return None
    return wrapper

def status_set_frequency():
    pass

def scroll_mod(mod,factor=0.001):
    if lock_frequency:
        global f_current

        logf_current=log10(f_current)
        if mod>0:
            logf_new = logf_current*(1.0+factor)
        else:
            logf_new = logf_current*(1.0-factor)

        f_new=10**logf_new
        if mod>0:
            f_new=ceil(f_new)
        else:
            f_new=floor(f_new)

        if fmin_audio<f_new<fmax_audio:
            change_f(f_new)
            status_set_frequency()
            f_current=f_new

def save_FFT_POINTS():
    file = path_join(INTERNAL_DIR_CSV_DEBUG, f'fft-{cfg["fft_size"]}-{FFT_POINTS}.csv')
    print(file)

    try:
        with open(file,'w',encoding='utf-8') as fh:
            fh.write(f"#fft_size:{cfg['fft_size']},FFT_POINTS:{FFT_POINTS}\n")
            fh.write("#index,frequency[Hz]\n")
            for i,f in enumerate(fft_values_x_all):
                fh.write(f'{i},{f}\n')
    except Exception as e:
        print(f'save_FFT_POINTS_error:{e}')
        #l_error()

def save_window():
    file = path_join(INTERNAL_DIR_CSV_DEBUG, f'fft_window-{cfg["fft_size"]}-{cfg["fft_window"]}.csv')
    print(file)

    try:
        with open(file,'w',encoding='utf-8') as fh:
            fh.write(f"#fft_size:{cfg['fft_size']}\n")
            fh.write("#index,val\n")
            for i,v in enumerate(fft_window):
                fh.write(f'{i},{v}\n')
    except Exception as e:
        print(f'save_fft_window_error:{e}')

def save_buckets_tracks():
    file = path_join(INTERNAL_DIR_CSV_DEBUG, f'buckets-tracks-{cfg["track_buckets"]}.csv')
    print(file)

    try:
        with open(file,'w',encoding='utf-8') as fh:
            fh.write(f"#buckets:{cfg["track_buckets"]}\n")
            fh.write("#index,frequency[Hz]\n")
            for b in range(TRACK_BUCKETS):
                f=bucket_tracks_freqs[b]
                fh.write(f'{b},{f}\n')
    except Exception as e:
        print(f'buckets-save_csv_error:{e}')
        #l_error()

def save_buckets_fft():
    file = path_join(INTERNAL_DIR_CSV_DEBUG, f'buckets-fft-{cfg["fft_fba_size"]}.csv')
    print(file)

    try:
        with open(file,'w',encoding='utf-8') as fh:
            fh.write(f"#buckets:{cfg["fft_fba_size"]}\n")
            fh.write("#index,frequency[Hz]\n")
            for b in range(cfg['fft_fba_size']):
                f=bucket_fft_freqs[b]
                fh.write(f'{b},{f}\n')
    except Exception as e:
        print(f'buckets-save_csv_error:{e}')
        #l_error()

def save_buckets_edges():
    global bucket_fft_edges
    file = path_join(INTERNAL_DIR_CSV_DEBUG, f'bucket_fft_edges-{len(bucket_fft_edges)}.csv')
    print(file)

    try:
        with open(file,'w',encoding='utf-8') as fh:
            fh.write(f"#bucket_fft_edges:{len(bucket_fft_edges)}\n")
            fh.write("#index,frequency[Hz]\n")
            for i,f in enumerate(bucket_fft_edges):
                fh.write(f'{i},{f}\n')
    except Exception as e:
        print(f'bucket_fft_edges-save_csv_error:{e}')
        #l_error()

def save_fft_bin_indices():
    global fft_bin_indices
    file = path_join(INTERNAL_DIR_CSV_DEBUG, f'fft_bin_indices-{len(fft_bin_indices)}.csv')
    print(file)

    try:
        with open(file,'w',encoding='utf-8') as fh:
            fh.write(f"#fft_bin_indices:{len(fft_bin_indices)}\n")
            fh.write("#index,index[Hz]\n")
            for i,j in enumerate(fft_bin_indices):
                fh.write(f'{i},{j}\n')
    except Exception as e:
        print(f'fft_bin_indices-save_csv_error:{e}')
        #l_error()

def save_fft_bin_counts():
    global fft_bin_counts
    file = path_join(INTERNAL_DIR_CSV_DEBUG, f'fft_bin_counts-{len(fft_bin_counts)}.csv')
    print(file)

    try:
        with open(file,'w',encoding='utf-8') as fh:
            fh.write(f"#fft_bin_counts:{len(fft_bin_counts)}\n")
            fh.write("#index,index[Hz]\n")
            for i,j in enumerate(fft_bin_counts):
                fh.write(f'{i},{j}\n')
    except Exception as e:
        print(f'fft_bin_counts-save_csv_error:{e}')
        #l_error()

def save_csv():
    timestamp=strftime('%Y_%m_%d-%H_%M_%S',localtime_catched(time()) )
    filename=path_join(INTERNAL_DIR_CSV,f"sas.{timestamp}.csv")
    cons_info(f'saving {filename} ...')
    Path(INTERNAL_DIR_CSV).mkdir(parents=True,exist_ok=True)

    try:
        with open(filename,'w',encoding='utf-8') as f:
            f.write("# Created with " + title + "\n")
            f.write("#frequency[Hz],level[dBFS]\n")
            f.write("#tracks:" + ','.join([str(track+1) for track in range(tracks) if cfg['show_track'][track]]) + "\n")

            for i in range(cfg["track_buckets"]):
                values=[]

                for track in range(tracks):
                    if cfg['show_track'][track]:
                        db=track_line_data_y[track][i]
                        freq=bucket_tracks_freqs[i]
                        values.append(f"{round(100*freq)/100},{round(1000*db)/1000}")
                f.write(','.join(values) + '\n')
    except Exception as e:
        l_error(f'save_csv_error:{e}')

schedule_screenshot=False
def save_image():
    global schedule_screenshot
    schedule_screenshot=True

scale_factor_logf_to_bucket_tracks=1

def logf_to_bucket_tracks(logf):
    return int(round(scale_factor_logf_to_bucket_tracks * (logf - logf_min_audio)))

current_bucket=logf_to_bucket_tracks(current_logf)

def amplitude_callback(sender=None, app_data=None,user_data=False):
    global AMPLITUDE_LOG
    val=cfg['amplitude']=get_value('amplitude')
    AMPLITUDE_LOG=aplitude_log_calc(val)

def aplitude_log_calc(val):
    return (10.0**(val*0.01) - 1.0)/9.0

AMPLITUDE_LOG=aplitude_log_calc(30)

@catch
def change_f(fpar):
    global current_logf,two_pi_by_out_samplerate,TRACK_BUCKETS,phase_step_x_phase_i,phase_i,current_bucket

    if fmin_audio<fpar<fmax_audio:
        current_logf=log10(fpar)
        current_f=fpar

        temp_bucket=logf_to_bucket_tracks(current_logf)
        if temp_bucket<TRACK_BUCKETS:
            current_bucket=temp_bucket

        set_value("cursor_f", ((fpar,fpar), (0,dbmin)))
        set_value('cursor_f_txt', (fpar, -3))
        configure_item('cursor_f_txt',label=f'{round(fpar)}Hz')

        phase_step_x_phase_i = (two_pi_by_out_samplerate * float64(fpar)) * phase_i

out_callbacks=0
out_errors=0
out_samples=0

AMPLITUDE_FACTOR=0

def audio_output_callback(outdata, frames, time, status):
    global phase,playing_state,two_pi,out_channel_buffer_mod_index,phase_step_x_phase_i,out_callbacks,out_errors,out_samples,AMPLITUDE_FACTOR

    if playing_state==1:
        AMPLITUDE_FACTOR_NEW=AMPLITUDE_LOG
        playing_state=2
    elif playing_state==-1:
        AMPLITUDE_FACTOR_NEW=0
        playing_state=0
    elif playing_state==0:
        AMPLITUDE_FACTOR_NEW=0
    else :
        AMPLITUDE_FACTOR_NEW=AMPLITUDE_LOG

    multiply(np_sin((phase + phase_step_x_phase_i[0:frames]) % two_pi, dtype=float32),linspace(AMPLITUDE_FACTOR, AMPLITUDE_FACTOR_NEW, frames, dtype=float32),out=outdata[:, out_channel_buffer_mod_index], dtype=float32)
    phase = (phase + phase_step_x_phase_i[frames]) % two_pi

    out_callbacks+=1
    out_samples+=frames
    AMPLITUDE_FACTOR=AMPLITUDE_FACTOR_NEW

    if status:
        cons_err(f'Output callback Error:{status},{frames=}')
        out_errors+=1

def sweep_abort():
    global sweeping
    if sweeping:
        cons_info('Sweeping ended.')
        configure_item('sweeping',texture_tag=ico["play"])
        sweeping=False

sweeping_i=0
def sweep_callback(sender=None, app_data=None):
    l_info(f'sweep_callback:{sender},{app_data}')

    global sweeping,lock_frequency,sweeping_i,track_line_data_y_recorded,PAUSE
    lock_frequency=False

    if not track_line_data_y_recorded:
        cons_err('No track selected for recording !')
        sweep_abort()
        return

    sweeping=(True,False)[sweeping]

    if sweeping:
        PAUSE=False
        set_value('pause',False)
        configure_item('sweeping',texture_tag=ico["play_on"])
        change_f(fmin_audio)
        play_start()
    else:
        play_stop()

    sweeping_i=0

@catch
def play_start():
    global playing_state,track_line_data_y_recorded,redraw_recorded_track_line
    bind_item_theme("cursor_f",red_cursor_theme)
    playing_state=1

    if track_line_data_y_recorded:
        recorded=int(cfg['recorded'])
        #bind_item_theme(f"track{recorded}_bg",track_recorded_bg_theme)
        #bind_item_theme(f"track{recorded}",track_recorded_core_theme)

        #bind_item_theme(f"track{recorded}_bg",track_recorded_bg_theme)
        #bind_item_theme(f"track{recorded}",track_recorded_core_theme)

    redraw_recorded_track_line=True

@catch
def play_stop():
    global playing_state,lock_frequency
    if playing_state==2:
        playing_state=-1
    lock_frequency=False

    bind_item_theme("cursor_f",green_line_theme)

    sweep_abort()

current_sample_db=-120

samples_chunks_fifo=deque()
samples_chunks_fifo_put=samples_chunks_fifo.append
samples_chunks_fifo_get=samples_chunks_fifo.popleft

###########################################################

def audio_input_callback(indata, frames, time_info, status):
    samples_chunks_fifo_put( (indata[:, 0].copy(),status) )

def go_to_homepage():
    try:
        if windows:
            cons_info(f'opening: {HOMEPAGE}')
            startfile(HOMEPAGE)
        else:
            cons_info(f'executing: xdg-open {HOMEPAGE}')
            system("xdg-open " + HOMEPAGE)
    except Exception as e:
        l_error(f'go_to_homepage error:{e}')

default_in_dev=None
default_out_dev=None

out_api_tooltip='\n'.join([
    'Select preferred API for test signal generation.',
    ' ',
    'For Windows "Windows WASAPI" or "Windows WDM-KS" are',
    'recommended for the lowest possible latency',
    ' ',
    'Check output latency on debug information (F11)',
    ' ',
    'WARNING: The test signal is generated at full bit depth',
    'therefore, if the selected API bypasses the system mixer,',
    'the sound will be played at FULL VOLUME.'])

def refresh_devices():
    cons_info('Refresh Devices')
    global default_in_dev,default_out_dev,apis,api_name2api,devices

    try:
        apis = query_hostapis()
    except Exception as e:
        l_error(f'query_hostapis error:{e}')
        apis=[]

    try:
        devices=query_devices()
    except Exception as e:
        cons_err(f'query_devices error:{e}')
        devices=[]

    any_inputs=any([ dev['name'] for dev in devices if dev['max_input_channels'] > 0])
    if any_inputs:
        try:
            default_in_dev=query_devices(kind='input')
        except Exception as e:
            l_error(f'query_devices input error:{e}')

    any_outputs=any([ dev['name'] for dev in devices if dev['max_output_channels'] > 0])
    if any_outputs:
        try:
            default_out_dev=query_devices(kind='output')
        except Exception as e:
            l_error(f'query_devices output error:{e}')

    l_info(' ')
    l_info('APIS:')

    for i,api in enumerate(apis):
        l_info(f'  api:{i}:')
        for key,val in api.items():
            l_info(f'    :{key}:{val}:')

    api_name2api={ api['name']:api for api in apis if api['devices'] }

    try:
        l_info(' ')
        l_info('DEVICES:')
        for i,dev in enumerate(devices):
            l_info(f'  dev:{i}:')
            for key,val in dev.items():
                l_info(f'    :{key}:{val}:')
        l_info(' ')
    except Exception as d_e2:
        cons_err(f'd_e2:{d_e2}')

    values_str=' - ' + '\n - '.join(api_name2api)
    configure_item('out_api',items=list(api_name2api.keys())); widget_tooltip(f"Available:\n\n{values_str}\n\n{out_api_tooltip}","out_api")
    configure_item('in_api',items=list(api_name2api.keys())); widget_tooltip(f"Available:\n\n{values_str}","in_api")

def initial_set_devices():
    global api_name2api,default_in_dev,default_out_dev
    ########################################
    in_set_by_cfg=False
    in_api = cfg['in_api']
    l_info(f'{in_api=}')

    if in_api in api_name2api:
        api=api_name2api[in_api]
        set_value('in_api',in_api)
        in_dev_config_items()

        in_dev = cfg['in_dev']
        l_info(f'{in_dev=}')

        devices_of_api=[query_devices(dev_id) for dev_id in api['devices']]

        devices_names_of_api=[dev['name'] for dev in devices_of_api]

        if in_dev in devices_names_of_api:
            set_value('in_dev',in_dev)
            l_info(f'in_dev set by cfg:{in_dev}')
            in_set_by_cfg=True
            set_value('in_samplerate',cfg['in_samplerate'])
        else:
            val=cfg['in_dev']=query_devices(device=api_name2api[in_api]['default_input_device'])['name']
            set_value('in_dev',cfg['in_dev'])
            l_info(f'in_dev set by default:{val}')
            in_set_by_cfg=True

    if not in_set_by_cfg:
        if default_in_dev:
            cfg['in_api']=query_hostapis(index=default_in_dev['hostapi'])['name']
            set_value('in_api',cfg['in_api'])
            in_dev_config_items()
            cfg['in_dev']=default_in_dev['name']
            set_value('in_dev',cfg['in_dev'])
            cfg['in_samplerate']=int(default_in_dev['default_samplerate'])
            set_value('in_samplerate',cfg['in_samplerate'])
            l_info(f"in set by defaults:',{cfg['in_api']},{cfg['in_dev']}")

    set_value('in_channel',cfg['in_channel'])
    set_value('in_latency',cfg['in_latency'])
    set_value('in_blocksize',cfg['in_blocksize'])
    ########################################

    out_set_by_cfg=False
    out_api = cfg['out_api']
    l_info(f'{out_api=}')
    if out_api in api_name2api:
        api=api_name2api[out_api]
        set_value('out_api',out_api)
        out_dev_config_items()

        out_dev = cfg['out_dev']
        l_info(f'{out_dev=}')

        devices_of_api=[query_devices(dev_id) for dev_id in api['devices']]
        devices_names_of_api=[dev['name'] for dev in devices_of_api]

        if out_dev in devices_names_of_api:
            set_value('out_dev',out_dev)
            l_info(f'out_dev set by cfg:{out_dev}')
            out_set_by_cfg=True
            set_value('out_samplerate',cfg['out_samplerate'])
        else:
            val=cfg['out_dev']=query_devices(device=api_name2api[out_api]['default_output_device'])['name']
            set_value('out_dev',cfg['out_dev'])
            l_info(f'out_dev set by default:{val}')
            out_set_by_cfg=True

    if not out_set_by_cfg:
        if default_out_dev:
            cfg['out_api']=query_hostapis(index=default_out_dev['hostapi'])['name']
            set_value('out_api',cfg['out_api'])
            out_dev_config_items()
            cfg['out_dev']=default_out_dev['name']
            set_value('out_dev',cfg['out_dev'])
            cfg['out_samplerate']=int(default_out_dev['default_samplerate'])
            set_value('out_samplerate',cfg['out_samplerate'])
            l_info(f"out set by defaults:'{cfg['out_api']},{cfg['out_dev']}")

    set_value('out_channel',cfg['out_channel'])
    set_value('out_latency',cfg['out_latency'])
    set_value('out_blocksize',cfg['out_blocksize'])
    ########################################

out_channel_buffer_mod_index=0

out_blocksize_max=65536
phase_i = arange(out_blocksize_max,dtype=float64)
phase_step_x_phase_i = float64(0) * phase_i

def out_blocksize_changed(sender=None, out_blocksize_str=None,user_data=False):
    l_info(f'out_blocksize_changed:{sender},{out_blocksize_str},{user_data}')

    play_stop()

    cfg['out_blocksize']=out_blocksize_str

    try:
        out_blocksize=int(out_blocksize_str)
    except:
        out_blocksize=0

    cons_opt(f'Output blocksize:{out_blocksize}/{out_blocksize_max}')

    if user_data:
        out_stream_init()

def in_blocksize_changed(sender=None, in_blocksize_str=None,user_data=False):
    l_info(f'in_blocksize_changed:{sender},{in_blocksize_str},{user_data}')

    val=cfg['in_blocksize']=in_blocksize_str
    cons_opt(f'Output blocksize:{val}')

    if user_data:
        in_stream_init()

def out_latency_changed(sender=None, app_data=None,user_data=False):
    l_info(f'out_latency_changed:{sender},{app_data},{user_data}')

    play_stop()

    val=cfg['out_latency']=get_value('out_latency')
    cons_opt(f'Output latency:{val}')


    if user_data:
        out_stream_init()

def in_latency_changed(sender=None, app_data=None,user_data=False):
    l_info(f'in_latency_changed:{sender},{app_data},{user_data}')

    val=cfg['in_latency']=get_value('in_latency')
    cons_opt(f'Input latency:{val}')

    if user_data:
        in_stream_init()

def out_channel_changed(sender=None, app_data=None,user_data=False):
    l_info(f'out_channel_changed:{sender},{app_data},{user_data}')

    play_stop()

    val=cfg['out_channel']=get_value('out_channel')
    cons_opt(f'Output channell:{val}')

    if user_data:
        out_stream_init()

in_channel_buffer_mod_index=0

def in_channel_changed(sender=None, app_data=None,user_data=False):
    l_info(f'in_channel_changed:{sender},{app_data},{user_data}')

    val=cfg['in_channel']=get_value('in_channel')
    cons_opt(f'Input channell:{val}')

    if user_data:
        in_stream_init()

def out_samplerate_changed(sender=None, app_data=None,user_data=False):
    l_info(f'out_samplerate_changed:{sender},{app_data},{user_data}')

    play_stop()

    val=cfg['out_samplerate']=get_value('out_samplerate')
    cons_opt(f'Output samplerate:{val}')

    global two_pi_by_out_samplerate
    two_pi_by_out_samplerate = two_pi/float64(get_value("out_samplerate"))

    if user_data:
        common_precalc()

        out_stream_init()

def in_samplerate_changed(sender=None, app_data=None,user_data=False):
    l_info(f'in_samplerate_changed:{sender},{app_data},{user_data}')

    val=cfg['in_samplerate']=get_value('in_samplerate')
    cons_opt(f'Input samplerate:{val}')

    if user_data:
        common_precalc()
        in_stream_init()

def out_stream_stop():
    if stream_out:
        stream_out.stop()
        cons_info('OutputStream stop.')
        sleep(0.2)

def in_stream_stop():
    if stream_in:
        stream_in.stop()
        cons_info('InputStream stop.')
        sleep(0.2)

def latency_for_stream(latency):
    if latency=='default':
        return None
    else:
        return latency

def out_stream_init():
    configure_item('out_status',texture_tag=ico['out_off'])
    global stream_out,device_out_current,out_channel_buffer_mod_index

    out_stream_stop()

    if stream_out:
        stream_out.close()
        cons_info('OutputStream closed.')
        sleep(0.1)

    if cfg['out_wasapi_exclusive'] and cfg['out_api'] == 'Windows WASAPI':
        extra_settings=WasapiSettings(exclusive=True)
        cons_opt('OutputStream WASAPI Exclusive mode')
    else:
        extra_settings=None

    try:
        channels=int(get_value('out_channel'))
    except:
        channels=1
    out_channel_buffer_mod_index=channels-1

    device=int(device_out_current['index'])
    samplerate=int(get_value('out_samplerate'))
    latency=latency_for_stream(get_value('out_latency'))
    #dithering_off=get_value('dithering_off')

    try:
        blocksize=int(get_value('out_blocksize'))
    except:
        blocksize=0

    api=cfg['out_api']

    cons_const('')
    dev_name=cfg["out_dev"]

    cons_const(f'OutputStream init ({api}) - {dev_name}\n  {samplerate=}\n  {latency=}\n  {blocksize=}\n  {channels=}')

    try:
        stream_out = OutputStream(callback=audio_output_callback, extra_settings=extra_settings,
            device=device,
            dtype='float32',
            samplerate=samplerate,
            latency=latency,
            blocksize=blocksize,
            channels=channels
        )
        #dither_off=True

        cons_const('init done.\nStarting output stream...')
        stream_out.start()
        configure_item('out_status',texture_tag=ico['out_on'])
    except Exception as e:
        cons_err(f'OutputStream init error:{e}')

def in_stream_init():
    configure_item('in_status',texture_tag=ico['in_off'])
    global stream_in,device_in_current,in_channel_buffer_mod_index

    in_stream_stop()
    if stream_in:
        stream_in.close()
        cons_info('InputStream closed.')
        sleep(0.1)

    if cfg['in_wasapi_exclusive'] and cfg['in_api'] == 'Windows WASAPI':
        extra_settings=WasapiSettings(exclusive=True)
        l_info('in WASAPI Exclusive mode !')
    else:
        extra_settings=None

    device=int(device_in_current['index'])

    samplerate=int(get_value('in_samplerate'))
    latency=latency_for_stream(get_value('in_latency'))
    try:
        blocksize=int(get_value('in_blocksize'))
    except:
        blocksize=0

    channels=int(get_value('in_channel'))

    in_channel_buffer_mod_index=0

    api=cfg['in_api']

    cons_const('')
    dev_name=cfg["in_dev"]
    cons_const(f'InputStream init ({api}) - {dev_name}\n  {samplerate=}\n  {latency=}\n  {blocksize=}\n  {channels=}')

    try:
        stream_in = InputStream(callback=audio_input_callback, extra_settings=extra_settings,
            device=device,
            samplerate=samplerate,
            latency=latency,
            blocksize=blocksize,
            channels=channels
        )
        #dither_off=True
        cons_const('init done.\nStarting input stream...')
        stream_in.start()
        configure_item('in_status',texture_tag=ico['in_on'])

    except Exception as e:
        cons_err(f'InputStream init error:{e}')

def show_info(message):
    cons_const("")
    for line in normalize_text(message):
        cons_const(line)

def about_wrapper():
    text1= f'Simple Audio Sweeper {VER_TIMESTAMP}\nAuthor: Piotr Jochymek\n\n{HOMEPAGE}\n\nPJ.soft.dev.x@gmail.com\n'
    text2='\n' + distro_info + '\n'
    show_info('\n' + text1+text2 + '\nPress H for help. Press Backspace to clear the console.\n')

def normalize_text(text):
    res=[]
    res_append=res.append
    max_len=max([len(line) for line in text.split('\n')])+1
    for line in text.split('\n'):
        to_add=' '*int((max_len-len(line))/2)
        res_append(f'{to_add}{line}{to_add}')
    return res

def license_wrapper():
    try:
        license_txt=Path(path_join(EXECUTABLE_DIR,'LICENSE')).read_text(encoding='ASCII')
    except Exception as exception_lic:
        cons_warn(str(exception_lic))
        try:
            license_txt=Path(path_join(dirname(EXECUTABLE_DIR),'LICENSE')).read_text(encoding='ASCII')
        except Exception as exception_lic_2:
            cons_err(str(exception_lic_2))
            sys_exit(1)

    show_info(license_txt)

def reset_track_press(sender=None, app_data=None):
    l_info(f'resetrack:{sender},{app_data}')

    global cfg,redraw_recorded_track_line,track_line_data_y_recorded

    if cfg['recorded']!=-1:
        track=cfg['recorded']
        cons_info(f'Track reset:{track}')

        sweep_abort()
        track_line_data_y_recorded=track_line_data_y[track]=[dbmin_sample]*TRACK_BUCKETS

        redraw_recorded_track_line=True
    else:
        cons_warn('recording not enabled')

track_line_data_y_recorded=[]
def track_action_callback(sender=None,app_data=None,track=None):
    l_info(f'track_action_callback:{sender},{app_data},{track}')

    Ctrl = is_key_down(mvKey_LControl)

    global cfg,track_line_data_y_recorded,track_line_data_y,redraw_recorded_track_line

    lock_frequency=False
    sweep_abort()
    play_stop()
    status_set_frequency()

    move_item(f"track{track}",parent="y_axis")

    redraw_recorded_track_line=True
    if Ctrl:
        if int(cfg['recorded'])==track:
            cfg['show_track'][track]=True
            cfg['recorded']=-1
            track_line_data_y_recorded=[]
            cons_info(f'Track {track} recording disabled.')
        else:
            cfg['show_track'][track]=True
            cfg['recorded']=track
            track_line_data_y_recorded=track_line_data_y[track]
            cons_info(f'Track {track} recording enabled.')
    else:
        if cfg['show_track'][track]:
            if int(cfg['recorded'])==track:
                cfg['recorded']=-1
                track_line_data_y_recorded=[]
                cons_info(f'Track {track} recording disabled.')
            else:
                cons_info(f'Track {track} hidden.')
                cfg['show_track'][track]=False
        else:
            cfg['show_track'][track]=True
            if int(cfg['recorded'])==-1:
                cfg['recorded']=track
                track_line_data_y_recorded=track_line_data_y[track]
                cons_info(f'Track {track} shown and recording enabled.')
            else:
                cons_info(f'Track {track} shown.')

    refresh_tracks()

def in_dev_config_items():
    api_name=get_value('in_api')
    print(f'in_dev_config_items:{api_name=}')

    api=api_name2api[api_name]

    try:
        api_devices_indexes=api_name2api[api_name]['devices']
        print(f'in_dev_config_items:{api_devices_indexes=}')

        devices = [query_devices(dev_index) for dev_index in api_devices_indexes]
        default_input_device_name=query_devices(api['default_input_device'])

        if get_value('allow_all_devices'):
            in_values=[ dev['name'] for dev in devices]
        else:
            in_values=[ dev['name'] for dev in devices if dev['max_input_channels'] > 0]
            # and dev['index']

        tooltip_str='\n'.join([ ('*' if name==default_input_device_name else '-') + ' ' + name for name in in_values])

        widget_tooltip(f"Available (API:{api_name}):\n\n{tooltip_str}","in_dev")

        configure_item("in_dev",items=in_values)

        return in_values
    except Exception as e:
        cons_err(f'in_dev_config_items error:{e},api_name:{api_name}')
        return []

def out_dev_config_items():
    api_name=get_value('out_api')
    print(f'out_dev_config_items:{api_name=}')

    api=api_name2api[api_name]

    try:
        api_devices_indexes=api['devices']
        print(f'out_dev_config_items:{api_devices_indexes=}')

        devices = [query_devices(dev_index) for dev_index in api_devices_indexes]

        default_output_device_name=query_devices(api['default_output_device'])

        out_values=[ dev['name'] for dev in devices if dev['max_output_channels'] > 0]
        # and dev['index']

        tooltip_str='\n'.join([ ('*' if name==default_output_device_name else '-') + ' ' + name for name in out_values])
        widget_tooltip(f"Available (API:{api_name}):\n\n{tooltip_str}","out_dev")

        configure_item("out_dev",items=out_values)

        return out_values

    except Exception as e:
        cons_err(f'out_dev_config_items error:{e},api_name:{api_name}')
        return []

#def dithering_off_callback(sender=None, app_data=None,user_data=False):
#    cfg['dithering_off']=get_value('dithering_off')
#    out_dev_changed(None,None,user_data)

def out_wasapi_exclusive_callback(sender=None, app_data=None,user_data=False):
    cfg['out_wasapi_exclusive']=get_value('out_wasapi_exclusive')

    if windows and cfg['out_api'] == 'Windows WASAPI':
        out_dev_changed(None,None,user_data)

def in_wasapi_exclusive_callback(sender=None, app_data=None,user_data=False):
    cfg['in_wasapi_exclusive']=get_value('in_wasapi_exclusive')

    if windows and cfg['in_api'] == 'Windows WASAPI':
        in_dev_changed(None,None,user_data)

def in_api_callback(sender=None, app_data=None,user_data=False):
    api_name=cfg['in_api']=get_value('in_api')
    cons_opt(f'Input API:{api_name}')

    if user_data:
        cfg['in_dev']=query_devices(device=api_name2api[api_name]['default_input_device'])['name']

    cfg['allow_all_devices'] = get_value('allow_all_devices')
    in_dev_config_items()

    set_value('in_dev',cfg['in_dev'])

    in_dev_changed(None,None,user_data)

def out_api_callback(sender=None, app_data=None,user_data=False):
    api_name=cfg['out_api']=get_value('out_api')
    cons_opt(f'Output API:{api_name}')

    if user_data:
        cfg['out_dev']=query_devices(device=api_name2api[api_name]['default_output_device'])['name']

    out_dev_config_items()

    set_value('out_dev',cfg['out_dev'])

    out_dev_changed(None,None,user_data)

def refresh_tracks():
    global cfg,redraw_recorded_track_line
    for track in range(tracks):
        if track==int(cfg['recorded']):
            configure_item(f'showcheck{track}',texture_tag=ico[f"{track+1}_sel"])

            bind_item_theme(f"track{track}_bg",themes[TI]['track_recorded_bg'])
            bind_item_theme(f"track{track}",themes[TI]['track_recorded_core'])

            configure_item(f"track{track}_bg",show=True)
            configure_item(f"track{track}",show=True)

        elif cfg['show_track'][track]:
            configure_item(f'showcheck{track}',texture_tag=ico[f"{track+1}_on"])

            bind_item_theme(f"track{track}_bg",themes[TI]['track_bg'])
            bind_item_theme(f"track{track}",themes[TI]['track_core'])

            configure_item(f"track{track}_bg",show=True)
            configure_item(f"track{track}",show=True)
        else:
            configure_item(f'showcheck{track}',texture_tag=ico[f"{track+1}_off"])

            configure_item(f"track{track}_bg",show=False)
            configure_item(f"track{track}",show=False)

    track=int(cfg['recorded'])
    if track!=-1:
        move_item(f"track{track}",parent="y_axis")

    redraw_recorded_track_line=True

FFT=cfg['fft']
def fft_callback(sender=None, app_data=None):
    global FFT,precalc_ready

    precalc_ready=False

    FFT=cfg['fft']=get_value('fft')
    l_info(f'fft_callback:{sender},{app_data},{FFT}')

    configure_item('fft_size',enabled=FFT,show=FFT)
    configure_item('fft_window',enabled=FFT,show=FFT)

    configure_item('fft_fba',enabled=FFT)
    configure_item('fft_fba_size',enabled=FFT,show=FFT)

    configure_item('fft_smooth',enabled=FFT)
    configure_item('fft_smooth_factor',enabled=FFT,show=FFT)

    configure_item('fft_tda',enabled=FFT)
    configure_item('fft_tda_factor',enabled=FFT,show=FFT)

    configure_item('peaks',enabled=FFT)
    configure_item('peaks_avg_factor',enabled=FFT,show=FFT)
    configure_item('peaks_dist_factor',enabled=FFT,show=FFT)
    configure_item('peaks_limit',enabled=FFT,show=FFT)

    fft_size_callback()

FFT_SIZE=cfg['fft_size']
def fft_size_callback(sender=None, app_data=None):
    global cfg,FFT_POINTS,FFT_SIZE,precalc_ready

    precalc_ready=False

    l_info(f'fft_size_callback:{sender},{app_data}')

    FFT_SIZE=cfg['fft_size']=int(get_value('fft_size'))
    FFT_POINTS=FFT_SIZE//2+1

    fft_window_callback()

def fft_window_callback(sender=None, app_data=None):
    global FFT,fft_window,fft_window_sum,cfg,precalc_ready,FFT_SIZE,fft_window_name

    precalc_ready=False

    fft_window_name=cfg['fft_window']=get_value('fft_window')

    val_str=off_on[FFT]
    cons_opt(f'FFT:{val_str} size:{FFT_SIZE} window:{fft_window_name}' if FFT else f'FFT:{val_str}')

    if fft_window_name=='ones':
        fft_window=ones(FFT_SIZE)
    elif fft_window_name=='hanning':
        fft_window=hanning(FFT_SIZE)
    elif fft_window_name=='hamming':
        fft_window=hamming(FFT_SIZE)
    elif fft_window_name=='blackman':
        fft_window=blackman(FFT_SIZE)
    elif fft_window_name=='bartlett':
        fft_window=bartlett(FFT_SIZE)
    else:
        l_error(f'unknown window:{cfg["fft_window"]}')

    fft_window_sum = np_sum(fft_window)
    l_info(f'{fft_window_sum=}')
    l_info(f'fft_window_callback:{sender},{app_data}')

    common_precalc()

    fft_fill_callback()

    if DEBUG:
        try:
            if environ['SAS_DEBUG_CSV']:
                save_window()
        except:
            pass

FFT_FBA=cfg['fft_fba']
def fft_fba_callback(sender=None, app_data=None):
    global FFT_FBA,precalc_ready,cfg

    precalc_ready=False
    FFT_FBA=cfg['fft_fba']=get_value('fft_fba')
    l_info(f'fft_fba_callback:{sender},{app_data},{FFT_FBA}')
    cons_opt(f'FFT FBA:{FFT_FBA}')

    #if not FFT_FBA:
    #    set_value('fft_smooth',False)

    configure_item('fft_smooth',enabled=FFT_FBA)
    configure_item('fft_smooth_factor',enabled=FFT_FBA,show=FFT_FBA)

    fft_fba_size_callback()

FFT_FBA_SIZE=cfg['fft_fba_size']
def fft_fba_size_callback(sender=None, app_data=None):
    global cfg,FFT_FBA_SIZE,precalc_ready

    precalc_ready=False
    FFT_FBA_SIZE=cfg['fft_fba_size']=int(get_value('fft_fba_size'))
    l_info(f'fft_fba_size_callback:{sender},{app_data},{FFT_FBA_SIZE}')
    cons_opt(f'FFT FBA Size:{FFT_FBA_SIZE}')
    fft_buckets_quant_change()

FFT_TDA_FACTOR=float(cfg['fft_tda_factor'])
FFT_TDA_FACTOR_1m=1.0-FFT_TDA_FACTOR
def fft_tda_factor_callback(sender=None, app_data=None):
    global FFT_TDA_FACTOR,precalc_ready,FFT_TDA_FACTOR_1m,cfg

    precalc_ready=False
    l_info(f'fft_tda_factor_callback:{sender},{app_data}')
    FFT_TDA_FACTOR=cfg['fft_tda_factor']=float(get_value('fft_tda_factor'))
    FFT_TDA_FACTOR_1m=1.0-FFT_TDA_FACTOR
    cons_opt(f'FFT TDA Factor:{FFT_TDA_FACTOR:.2f}')
    common_precalc()

FFT_TDA=cfg['fft_tda']
def fft_tda_callback(sender=None, app_data=None):
    global FFT_TDA,precalc_ready,cfg

    precalc_ready=False
    FFT_TDA=cfg['fft_tda']=get_value('fft_tda')
    l_info(f'fft_tda_callback:{sender},{app_data},{FFT_TDA}')
    val_str=off_on[FFT_TDA]
    cons_opt(f'FFT TDA:{val_str}')

    configure_item('fft_tda_factor',enabled=FFT_TDA,show=FFT_TDA)

    if FFT_TDA:
        fft_tda_factor_callback()
    else:
        common_precalc()

bucket_fft_freqs=[0]
bucket_fft_edges=[0]

time_to_collect_sample=0.125 #[s]

spectrum_sub_bucket_samples=4
sweeping_delay=time_to_collect_sample*1.5/spectrum_sub_bucket_samples
l_info(f'{sweeping_delay=}')

logf_max_audio_m_logf_min_audio = logf_max_audio-logf_min_audio

def fft_buckets_quant_change(sender=None, app_data=None, call_common=True):
    global logf_sweep_step,log_bucket_fft_width,log_bucket_fft_width_by2,cfg,precalc_ready

    precalc_ready=False
    l_info(f'fft_buckets_quant_change:{sender},{app_data},{call_common}')

    log_bucket_fft_width=logf_max_audio_m_logf_min_audio/FFT_FBA_SIZE
    log_bucket_fft_width_by2=log_bucket_fft_width*0.5

    if call_common:
        common_precalc()

def tracks_buckets_quant_change(sender=None, app_data=None,try_to_load=False):
    global sweep_steps,scale_factor_logf_to_bucket_tracks,log_bucket_tracks_width,log_bucket_tracks_width_by2,TRACK_BUCKETS,bucket_tracks_freqs,track_line_data_y,track_line_data_y_recorded,redraw_recorded_track_line,logf_sweep_step

    TRACK_BUCKETS=cfg['track_buckets']=int(get_value('track_buckets'))
    l_info(f'tracks_buckets_quant_change:{sender},{app_data}')

    sweep_steps=TRACK_BUCKETS*spectrum_sub_bucket_samples
    logf_sweep_step=logf_max_audio_m_logf_min_audio/sweep_steps

    scale_factor_logf_to_bucket_tracks=TRACK_BUCKETS/logf_max_audio_m_logf_min_audio
    log_bucket_tracks_width=logf_max_audio_m_logf_min_audio/TRACK_BUCKETS
    log_bucket_tracks_width_by2=log_bucket_tracks_width*0.5

    bucket_tracks_freqs=[0]*TRACK_BUCKETS

    for b in range(TRACK_BUCKETS):
        bucket_tracks_freqs[b]= 10**(logf_min_audio + log_bucket_tracks_width_by2 + log_bucket_tracks_width * b)
    bucket_tracks_freqs=np_array(bucket_tracks_freqs)

    if try_to_load:
        for track in range(tracks):
            try:
                with open(track_file(track,TRACK_BUCKETS), "r", encoding="utf-8") as f:
                    track_line_data_y[track]=loads(f.read())
            except Exception as tl_e:
                l_error(f'Track load error:{tl_e}')
                track_line_data_y[track]=[dbmin_sample]*TRACK_BUCKETS

    else:
        for track in range(tracks):
            track_line_data_y[track]=[dbmin_sample]*TRACK_BUCKETS

    for track in range(tracks):
        set_value(f"track{track}_bg", [bucket_tracks_freqs, track_line_data_y[track]])
        set_value(f"track{track}", [bucket_tracks_freqs, track_line_data_y[track]])

    track=int(cfg['recorded'])
    if track!=-1:
        track_line_data_y_recorded=track_line_data_y[track]

    redraw_recorded_track_line=True

TRACKS_TDA_FACTOR=float(cfg['tracks_tda_factor'])
TRACKS_TDA_FACTOR_1m=1.0-TRACKS_TDA_FACTOR

def tracks_tda_factor_callback(sender=None, app_data=None):
    l_info(f'tracks_tda_factor_callback:{sender},{app_data}')
    global TRACKS_TDA_FACTOR,tracks_ready,TRACKS_TDA_FACTOR_1m
    TRACKS_TDA_FACTOR=cfg['tracks_tda_factor']=float(get_value('tracks_tda_factor'))
    TRACKS_TDA_FACTOR_1m=1.0-TRACKS_TDA_FACTOR
    common_precalc()

data=[0]
FFT_ACTUAL_BUCKETS=0

@catch
def common_precalc():
    l_info('common_precalc')

    global in_samplerate_by_fft_size,cfg,fft_duration,log_bucket_fft_width,log_bucket_fft_width_by2,bucket_fft_freqs,fft_values_x_all,fft_line_data_y,bucket_fft_edges,fft_bin_indices,fft_bin_counts,next_check,current_sample_db_time_samples,fft_bin_indices_selected,fft_values_x_bins,precalc_ready,FFT_ACTUAL_BUCKETS,fft_values_y_prev,data

    samplerate=get_value('in_samplerate')

    current_sample_db_time=0.1
    current_sample_db_time_samples=int(float(samplerate)*current_sample_db_time)

    in_samplerate_by_fft_size = float(samplerate) / FFT_SIZE
    fft_duration= 1.0/in_samplerate_by_fft_size
    l_info(f'{samplerate=},{fft_duration=}')

    dummy_data=[200]*FFT_POINTS
    fft_values_x_all=[0]*FFT_POINTS
    fft_line_data_y=[-110]*FFT_POINTS

    for i_fft in range(FFT_POINTS):
        fft_values_x_all[i_fft]=i_fft * in_samplerate_by_fft_size

    fft_values_x_all=np_array(fft_values_x_all)

    bucket_fft_freqs=[0]*FFT_FBA_SIZE
    bucket_fft_edges=[0]*(FFT_FBA_SIZE+1)

    for b in range(FFT_FBA_SIZE):
        bucket_fft_freqs[b]= 10**(logf_min_audio + log_bucket_fft_width_by2 + log_bucket_fft_width * b)
        bucket_fft_edges[b+1]= 10**(logf_min_audio + log_bucket_fft_width * (b+1))

    fft_bin_indices = digitize(fft_values_x_all, bucket_fft_edges)
    l_info(f'fft_bin_indices={len(fft_bin_indices)}')
    fft_bin_counts = bincount(fft_bin_indices)
    l_info(f'fft_bin_counts={len(fft_bin_counts)}')

    if DEBUG:
        try:
            if environ['SAS_DEBUG_CSV']:
                Path(INTERNAL_DIR_CSV_DEBUG).mkdir(parents=True,exist_ok=True)
                save_buckets_tracks()
                save_buckets_edges()
                save_buckets_fft()
                save_FFT_POINTS()
                save_fft_bin_indices()
                save_fft_bin_counts()
        except:
            pass

    fft_bin_indices_selected=np_array([i for i,i_n in enumerate(isnan(bincount(fft_bin_indices, weights=dummy_data)[1:] / fft_bin_counts[1:])) if not i_n])
    FFT_ACTUAL_BUCKETS=len(fft_bin_indices_selected)
    fft_values_x_bins=np_array([bucket_fft_freqs[i] for i in fft_bin_indices_selected[:-1]])

    fft_values_y_prev=None

    data=np_concatenate([zeros(FFT_SIZE),data])[-FFT_SIZE:]

    precalc_ready=True
    next_check = 0

rates_to_test = (44100,48000,88200,96000,176400,192000,384000)
def check_sample_rates_input(device_id):
    supported = []
    for rate in rates_to_test:
        try:
            check_input_settings(device=device_id, samplerate=rate)
            supported.append(str(rate))
            l_info(f'try_in:{rate}:ok')
        except Exception as try_e:
            l_warning(f'try_in:{rate}:{try_e}')
    return tuple(supported)

def check_sample_rates_output(device_id):
    supported = []
    for rate in rates_to_test:
        try:
            check_output_settings(device=device_id, samplerate=rate)
            supported.append(str(rate))
            l_warning(f'try_out:{rate}:ok')
        except Exception as try_e:
            l_warning(f'try_out:{rate}:{try_e=}')
    return tuple(supported)

device_out_current=None
def out_dev_changed(sender=None, app_data=None,user_data=True):
    l_info(f'out_dev_changed:{sender},{app_data}')

    global device_out_current

    dev_name=cfg["out_dev"]=get_value("out_dev")

    api_name=get_value('out_api')
    api=[api for api in query_hostapis() if api['name']==api_name][0]

    devices_of_api=[query_devices(dev_id) for dev_id in api['devices']]
    devices_names_of_api=[dev['name'] for dev in devices_of_api]

    device_out_current=[dev for dev in devices_of_api if dev['name']==dev_name][0]

    output_channels=[str(val) for val in range(1,device_out_current['max_output_channels']+1)]

    configure_item("out_channel",items=output_channels)

    cfg["out_channel"]=out_channel_value=get_value("out_channel")

    if not out_channel_value or out_channel_value not in output_channels:
        out_channel_value=1
        set_value("out_channel",out_channel_value)

    sel_rates=check_sample_rates_output(device_out_current['index'])
    configure_item("out_samplerate",items=sel_rates)

    values_str=' - ' + '\n - '.join(sel_rates)
    widget_tooltip(f"Available:\n\n{values_str}","out_samplerate")

    prev_out_samplerate = cfg['out_samplerate']
    out_samplerate_to_set = prev_out_samplerate if prev_out_samplerate in sel_rates else str(int(device_out_current['default_samplerate']))
    cfg['out_samplerate']=out_samplerate_to_set

    set_value("out_samplerate",out_samplerate_to_set)

    out_samplerate_changed()
    out_channel_changed(None,out_channel_value)
    out_latency_changed(None,cfg['out_latency'])
    out_blocksize_changed(None,cfg['out_blocksize'])

    if user_data:
        out_stream_init()

device_in_current=None
def in_dev_changed(sender=None, app_data=None,user_data=False):
    global device_in_current,precalc_ready
    precalc_ready=False

    l_info(f'in_dev_changed:{sender},{app_data},{user_data}')

    dev_name=cfg["in_dev"]=get_value("in_dev")

    api_name=get_value('in_api')
    api=[api for api in query_hostapis() if api['name']==api_name][0]

    devices_of_api=[query_devices(dev_id) for dev_id in api['devices']]
    device_in_current=[dev for dev in devices_of_api if dev['name']==dev_name][0]

    input_channels=[str(val) for val in range(1,device_in_current['max_input_channels']+1)]

    configure_item("in_channel",items=input_channels)
    cfg['in_channel']=in_channel_value=get_value("in_channel")

    if not in_channel_value or in_channel_value not in input_channels:
        in_channel_value=1
        set_value("in_channel",in_channel_value)

    sel_rates=check_sample_rates_input(device_in_current['index'])
    configure_item("in_samplerate",items=sel_rates)

    values_str=' - ' + '\n - '.join(sel_rates)
    widget_tooltip(f"Available:\n\n{values_str}","in_samplerate")

    prev_in_samplerate = cfg['in_samplerate']
    in_samplerate_to_set = prev_in_samplerate if prev_in_samplerate in sel_rates else str(int(device_in_current['default_samplerate']))
    cfg['in_samplerate']=in_samplerate_to_set
    set_value("in_samplerate",in_samplerate_to_set)

    in_channel_changed(None,in_channel_value)
    in_latency_changed(None,cfg['in_latency'])
    in_blocksize_changed(None,cfg['in_blocksize'])

    if user_data:
        common_precalc()

        in_stream_init()

def click_callback(sender, button_nr):
    if is_item_hovered("plot"):
        global sweeping,lock_frequency
        if button_nr==0:
            sweep_abort()

            if lock_frequency:
                lock_frequency=False
                play_stop()
            else:
                play_start()
                status_set_frequency()

        elif button_nr==1:
            if sweeping:
                sweep_abort()
            elif lock_frequency:
                lock_frequency=False
                play_stop()
            else:
                lock_frequency=True
                play_start()
                status_set_frequency()

def release_callback(sender, button_nr):
    if button_nr==0:
        global dragging,resizing
        dragging,resizing = False,False

        if is_item_hovered("plot"):
            play_stop()
        #else:
            #global sweeping,lock_frequency
    else:
        l_info(f'another button:{button_nr}')

def wheel_callback(sender, val):
    global lock_frequency
    global console_show_end_index,console_direction_mod,next_redraw

    if lock_frequency:
        scroll_mod(val)
    else:
        if is_item_hovered("plot"):
            if val>0:
                console_show_end_index=max(console_visible_lines,console_show_end_index-2)
                console_direction_mod=-1
                next_redraw=0.0
            else:
                console_show_end_index=min(console_buffer_last_elem,console_show_end_index+2)
                console_direction_mod=1
                next_redraw=0.0

        elif is_item_hovered("slider"):
            slide_val=get_value('slider')
            slide_val+=-3*val

            if slide_val<30:
                slide_val=30
            elif slide_val>100:
                slide_val=100

            set_value('slider',slide_val)
            slide_change('slider')

def on_mouse_move_tracks_enter(sender, app_data):
    button_alias=app_data
    track=int(button_alias[-1])

    configure_item(f"track{track}_bg",show=True)
    configure_item(f"track{track}",show=True)

    bind_item_theme(f"track{track}_bg",themes[TI]['track_hover_bg'])
    bind_item_theme(f"track{track}",themes[TI]['track_hover_core'])

def on_mouse_move_tracks_leave(sender, app_data):
    button_alias=app_data
    track=int(button_alias[-1])

    refresh_tracks()

dragging,resizing = False,False
def on_mouse_down(sender, app_data):
    global dragging, resizing, offset_x, offset_y
    if not dragging:
        offset_x, offset_y = get_mouse_pos(local=False)

        vh,vw = get_viewport_height(),get_viewport_width()

        if offset_y<title_hight:
            dragging = True
        elif offset_x>vw-30 and offset_y>vh-30:
            resizing = True

set_viewport_pos_scheduled=False
set_viewport_resize_scheduled=False
settings_wrapper_scheduled=False

prev_plot_x=0
def on_mouse_move(sender, app_data):
    global dragging, resizing, set_viewport_pos_scheduled,set_viewport_resize_scheduled

    if dragging and not decorated and not set_viewport_pos_scheduled:
        set_viewport_pos_scheduled=True

    elif resizing:
        width,height = get_mouse_pos()
        if width<viewport_width_min:
            width=viewport_width_min
        if height<viewport_height_min[cfg['settings']]:
            height=viewport_height_min[cfg['settings']]

        set_viewport_resize_scheduled=(width,height)

    elif is_item_hovered("plot"):
        plot_x, plot_y = get_plot_mouse_pos()

        if plot_x is not None:
            global prev_plot_x,f_current

            if plot_x != prev_plot_x:
                prev_plot_x = plot_x

                if not sweeping and not lock_frequency:
                    f_current=plot_x
                    status_set_frequency()
                    change_f(f_current)
    else:
        if not lock_frequency and not sweeping:
            play_stop()

def key_press_callback(sender, app_data):
    global precalc_ready,next_redraw,console_show_end_index,console_direction_mod,console_buffer_last_elem,lock_frequency

    Shift = is_key_down(mvKey_LShift)
    Ctrl = is_key_down(mvKey_LControl)

    for delay in range(1024):
        if precalc_ready:
            break
        else:
            sleep(0.001)

    if app_data==dpg.mvKey_Spacebar:
        set_value('pause',(True,False)[get_value('pause')])
        pause_callback()
    if app_data==dpg.mvKey_1:
        track_action_callback(None,None,0)
    elif app_data==dpg.mvKey_2:
        track_action_callback(None,None,1)
    elif app_data==dpg.mvKey_3:
        track_action_callback(None,None,2)
    elif app_data==dpg.mvKey_4:
        track_action_callback(None,None,3)
    elif app_data==dpg.mvKey_5:
        track_action_callback(None,None,4)
    elif app_data==dpg.mvKey_6:
        track_action_callback(None,None,5)
    elif app_data==dpg.mvKey_7:
        track_action_callback(None,None,6)
    elif app_data==dpg.mvKey_8:
        track_action_callback(None,None,7)
    elif app_data==dpg.mvKey_Left:
        scroll_mod(-1,0.001)
    elif app_data==dpg.mvKey_Right:
        scroll_mod(1,0.001)
    elif app_data==dpg.mvKey_Up:
        if lock_frequency:
            scroll_mod(1,0.0001)
        else:
            console_show_end_index=max(console_visible_lines,console_show_end_index-1)
            console_direction_mod=-1
            next_redraw=0.0
    elif app_data==dpg.mvKey_Prior or app_data==517:
        console_show_end_index=max(console_visible_lines,console_show_end_index-10)
        console_direction_mod=-1
        next_redraw=0.0
    elif app_data==dpg.mvKey_Down:
        if lock_frequency:
            scroll_mod(-1,0.0001)
        else:
            console_show_end_index=min(console_buffer_last_elem,console_show_end_index+1)
            console_direction_mod=1
            next_redraw=0.0
    elif app_data==dpg.mvKey_Next or app_data==518:
        console_show_end_index=min(console_buffer_last_elem,console_show_end_index+10)
        console_direction_mod=1
        next_redraw=0.0
    elif app_data==dpg.mvKey_F1:
        about_wrapper()
    elif app_data==dpg.mvKey_F2:
        license_wrapper()
    elif app_data==dpg.mvKey_Back:
        cons_const('\n'*console_visible_lines)
    elif app_data==dpg.mvKey_F:
        fft=get_value('fft')
        fft=(True,False)[fft]
        set_value('fft',fft)
        fft_callback()
    elif app_data==dpg.mvKey_G:
        fft_fill=get_value('fft_fill')
        fft_fill=(True,False)[fft_fill]
        set_value('fft_fill',fft_fill)
        fft_fill_callback()
    elif app_data==dpg.mvKey_F3:
        items=get_item_configuration('fft_size')['items']
        configure_item('fft_size',default_value=items[(items.index(get_value('fft_size'))+(1,-1)[Shift]) % len(items)])
        fft_size_callback()
    elif app_data==dpg.mvKey_F4:
        items=get_item_configuration('fft_window')['items']
        configure_item('fft_window',default_value=items[(items.index(get_value('fft_window'))+(1,-1)[Shift]) % len(items)])
        fft_window_callback()
    elif app_data==dpg.mvKey_F5:
        fft_fba=get_value('fft_fba')
        if Ctrl:
            fft_fba=(True,False)[fft_fba]
            set_value('fft_fba',fft_fba)
        else:
            items=get_item_configuration('fft_fba_size')['items']
            configure_item('fft_fba_size',default_value=items[(items.index(get_value('fft_fba_size'))+(1,-1)[Shift]) % len(items)])
        fft_fba_callback()
    elif app_data==dpg.mvKey_F6:
        fft_smooth=get_value('fft_smooth')
        if Ctrl:
            fft_smooth=(True,False)[fft_smooth]
            set_value('fft_smooth',fft_smooth)
        else:
            minv=get_item_configuration('fft_smooth_factor')['min_value']
            maxv=get_item_configuration('fft_smooth_factor')['max_value']
            items=list(range(minv,maxv+1))
            configure_item('fft_smooth_factor',default_value=items[(items.index(get_value('fft_smooth_factor'))+(1,-1)[Shift]) % len(items)])
        fft_smooth_callback()
        fft_smooth_factor_callback()
    elif app_data==dpg.mvKey_F7:
        fft_tda=get_value('fft_tda')
        if Ctrl:
            fft_tda=(True,False)[fft_tda]
            set_value('fft_tda',fft_tda)
        else:
            maxv=get_item_configuration('fft_tda_factor')['max_value']
            minv=get_item_configuration('fft_tda_factor')['min_value']
            curr=get_value('fft_tda_factor')

            nextv=curr+(-0.01 if Shift else 0.01)
            if nextv<minv:
                nextv=maxv
            elif nextv>maxv:
                nextv=minv

            configure_item('fft_tda_factor',default_value=nextv)
        fft_tda_callback(None,get_value('fft_tda'))
    elif app_data==dpg.mvKey_F12:
        settings_wrapper_toggle()
    elif app_data==dpg.mvKey_F11:
        set_value('debug',(True,False)[get_value('debug')])
        debug_callback()
    elif app_data==dpg.mvKey_L:
        theme_callback(0)
    elif app_data==dpg.mvKey_D:
        theme_callback(1)
    elif app_data==dpg.mvKey_S:
        save_image()
    elif app_data==dpg.mvKey_C:
        save_csv()
    elif app_data==dpg.mvKey_H:
        help_callback()
    elif app_data==dpg.mvKey_P:
        peaks_val=get_value('peaks')
        peaks_val=(True,False)[peaks_val]
        set_value('peaks',peaks_val)
        peaks_callback()
    elif app_data==dpg.mvKey_Pause:
        global CAPTURE,CAPTURE_saving,vw,vh
        if CAPTURE:
            CAPTURE=0
        elif not CAPTURE_saving:
            CAPTURE=int(CAPTURE_TIME*CAPTURE_FPS)
            cons_info('-')
            Thread(target=capture_loop,daemon=True).start()

    elif app_data==dpg.mvKey_Delete:
        reset_track_press()
    elif app_data==dpg.mvKey_Escape:
        global sweeping
        play_stop()
        sweeping=False
    else:
        #print(app_data)
        pass

def theme_callback(ti):
    global TI
    TI=ti

    l_info(f'theme_callback:{TI}')
    dpg.bind_theme(themes[TI]['main'])

    bind_item_theme("fft_line_shade",themes[TI]['fft_line_fill'])
    bind_item_theme("fft_line2",themes[TI]['fft_line2'])
    bind_item_theme("fft_line",themes[TI]['fft_line_with_fill' if FFT_FILL else 'fft_line'])

    bind_item_theme('fft_avg',themes[TI]['fft_avg_line_theme'])

    for track in range(tracks):
        bind_item_theme(f"track{track}_bg",themes[TI]['track_bg'])
        bind_item_theme(f"track{track}",themes[TI]['track_core'])

    configure_item('plotbg',texture_tag=ico['bg' if ti==0 else 'bg_dark'])

    if not decorated:
        configure_item('exit_button',texture_tag=ico['exit_light' if ti==0 else 'exit_dark'])

    bind_item_theme('cursor_db_txt',themes[TI]['text_main'])
    bind_item_theme('cursor_f_txt',themes[TI]['text_main'])

    cfg['theme']=ti
    refresh_tracks()

    bind_item_theme('mark_text_1',themes[TI]['text_aura'])
    bind_item_theme('mark_text_2',themes[TI]['text_aura'])
    bind_item_theme('mark_text_3',themes[TI]['text_aura'])
    bind_item_theme('mark_text_4',themes[TI]['text_aura'])
    bind_item_theme('mark_text_5',themes[TI]['text_aura'])
    bind_item_theme('mark_text_6',themes[TI]['text_aura'])
    bind_item_theme('mark_text_7',themes[TI]['text_aura'])
    bind_item_theme('mark_text_8',themes[TI]['text_aura'])
    bind_item_theme('mark_text',themes[TI]['text_main'])

    res=[]
    res_append=res.append
    #INFO=0
    res_append( (COLORS[TI]['BG_CONS'],COLORS[TI]['CONS_INFO']) )
    #WARN=1
    res_append( (COLORS[TI]['BG_CONS'],COLORS[TI]['CONS_WARN']) )
    #ERR=2
    res_append( (COLORS[TI]['BG_CONS'],COLORS[TI]['CONS_ERR']) )
    #CONST=3
    res_append( (COLORS[TI]['BG_CONS'],COLORS[TI]['CONS_CONST']) )
    #OPT=4
    res_append( (COLORS[TI]['BG_CONS'],COLORS[TI]['CONS_OPT']) )

    global console_color_tab,INNER_SHADOW,OUTER_SHADOW,INNER_HIGHLIGHT,OUTER_HIGHLIGHT
    console_color_tab=tuple(res)

    INNER_SHADOW=COLORS[TI]['INNER_SHADOW']
    OUTER_SHADOW=COLORS[TI]['OUTER_SHADOW']
    INNER_HIGHLIGHT=COLORS[TI]['INNER_HIGHLIGHT']
    OUTER_HIGHLIGHT=COLORS[TI]['OUTER_HIGHLIGHT']

PEAKS=cfg['peaks']
def peaks_callback():
    global PEAKS
    val=cfg['peaks']=PEAKS=get_value('peaks')

    configure_item('peaks_avg_factor',enabled=PEAKS,show=PEAKS)
    configure_item('peaks_dist_factor',enabled=PEAKS,show=PEAKS)
    configure_item('peaks_limit',enabled=PEAKS,show=PEAKS)

    if PEAKS:
        configure_item("fft_avg",show=DEBUG)
    else:
        configure_item("fft_avg",show=False)

    val_str=off_on[val]
    cons_opt(f'Peaks detection:{val_str}')

off_on=('OFF','ON')
FFT_SMOOTH=cfg['fft_smooth']
def fft_smooth_callback():
    global FFT_SMOOTH
    val=cfg['fft_smooth']=FFT_SMOOTH=get_value('fft_smooth')
    val_str=off_on[val]
    cons_opt(f'FFT Smoothing:{val_str}')

def smooth_window_calc():
    global FFT_SMOOTH_WINDOW
    FFT_SMOOTH_WINDOW=hanning(1+2*FFT_SMOOTH_FACTOR)
    FFT_SMOOTH_WINDOW /= FFT_SMOOTH_WINDOW.sum()

FFT_SMOOTH_FACTOR=cfg['fft_smooth_factor']
smooth_window_calc()

def fft_smooth_factor_callback():
    global FFT_SMOOTH_FACTOR
    if cfg['fft_smooth']:
        val=cfg['fft_smooth_factor']=FFT_SMOOTH_FACTOR=get_value('fft_smooth_factor')
        cons_opt(f'FFT Smoothing factor:{val}')

        smooth_window_calc()
    else:
        set_value('fft_smooth_factor',cfg['fft_smooth_factor'])

PEAKS_AVG_FACTOR=cfg['peaks_avg_factor']
def peaks_avg_factor_change():
    global PEAKS_AVG_FACTOR
    cfg['peaks_avg_factor']=PEAKS_AVG_FACTOR=get_value('peaks_avg_factor')
    cons_opt(f'Peaks Avarage Factor:{PEAKS_AVG_FACTOR}')

PEAKS_DIST_FACTOR=cfg['peaks_dist_factor']
def peaks_distance_change():
    global PEAKS_DIST_FACTOR
    cfg['peaks_dist_factor']=PEAKS_DIST_FACTOR=get_value('peaks_dist_factor')
    cons_opt(f'Peaks Distance Factor:{PEAKS_DIST_FACTOR}')

PEAKS_LIMIT=cfg['peaks_limit']
def peaks_limit_change():
    global PEAKS_LIMIT
    cfg['peaks_limit']=PEAKS_LIMIT=get_value('peaks_limit')
    cons_opt(f'Peaks number limit:{PEAKS_LIMIT}')

DEBUG=cfg['debug']
def debug_callback():
    set_value('debug_text','')
    global DEBUG,next_check
    cfg['debug']=DEBUG=get_value('debug')
    next_check=0

    if DEBUG:
        configure_item("fft_avg",show=PEAKS)
        l_info(f'DEB:\tframes/changes\tmain_ratio/proc_ratio\tfft_calc_mean:fft_proc_mean:fft_peaks_mean\tout_samples:in_samples\tout_callbacks:in_callbacks\tout_errors:in_errors\tstream_out.cpu_load:stream_in.cpu_load\tstream_out.latency:stream_in.latency')
    else:
        configure_item("fft_avg",show=False)

    on_viewport_resize()

def pause_callback():
    global PAUSE
    PAUSE=get_value('pause')
    if not PAUSE:
        cons_info('Resumed.')

def decorated_callback():
    cfg['decorated']=get_value('decorated')

def fft_fill_callback():
    global FFT_FILL
    FFT_FILL=cfg['fft_fill']=get_value('fft_fill')

    configure_item('fft_line_shade',show=FFT_FILL and FFT)
    configure_item('fft_line2',show=not FFT_FILL and FFT)
    configure_item('fft_line',show=FFT)

    theme_callback(TI)

def help_callback():
    l_info('help_callback')
    global next_check

    vals= [ "--------------------------------------------------------------------------------------------------------",
            "H   - this help                      F   - FFT Toggle                1-8 - toggle track visibility      ",
            "F1  - about                          F3  - FFT size                         (recording with Ctrl)       ",
            "F2  - license                        F4  - FFT window                Del - Reset recorded track         ",
            "F11 - debug info                     F5  - FFT FBA                   LMB - generate specified frequency ",
            "F12 - settings                       F6  - FFT Smoothing             RMB -lock frequency                ",
            "G   - Filled chart                   F7  - FFT TDA                   Mouse Wheel, Arrows,PgUp,PgDown -  ",
            "L / D  - light/dark theme            P - peaks detection                     modify locked frequency,   ",
            "Space  - pause refreshing                                                    console scroll             ",
            "S / C  - save file (png/csv)                                                                            ",
            "Pause  - frames capture (gif)                                                                           ",
            "Backspace - clear the console                                                                           ",
            "--------------------------------------------------------------------------------------------------------"]

    for line in vals:
        cons_const(line)

    next_check=0

def in_reinit_callback():
    in_stream_init()

def out_reinit_callback():
    out_stream_init()

def sd_reinit_callback():
    cons_info('Terminating...')

    try:
        _terminate()
    except Exception as t_e:
        cons_err(f'error:{t_e}')

    cons_info('Reinitializing...')
    try:
        _initialize()
    except Exception as i_e:
        cons_err(f'error:{i_e}')

    refresh_devices()

    in_stream_init()
    out_stream_init()

def settings_wrapper_toggle():
    global cfg
    cfg['settings']=(True,False)[cfg['settings']]
    settings_wrapper()

def settings_wrapper():
    global cfg,settings_wrapper_scheduled
    l_info(f'settings_wrapper:' + str(cfg['settings']))

    if cfg['settings']:
        settings_wrapper_scheduled=(max(viewport_height_min[1],get_viewport_height()+settings_height),viewport_height_min[1])
    else:
        settings_wrapper_scheduled=(max(viewport_height_min[0],get_viewport_height()-settings_height),viewport_height_min[0])

build_gui()

if cfg['settings']:
    show_item('settings_group')
    set_viewport_min_height(viewport_height_min[1])
else:
    hide_item('settings_group')
    set_viewport_min_height(viewport_height_min[0])

if cfg['viewport_height']:
    set_viewport_height(cfg['viewport_height'])

if cfg['viewport_width']:
    set_viewport_width(cfg['viewport_width'])

if cfg['viewport_pos']:
    set_viewport_pos(cfg['viewport_pos'])

dpg.set_viewport_small_icon(Path(path_join(EXECUTABLE_DIR,"./icons/sas_small.png")))
dpg.set_viewport_large_icon(Path(path_join(EXECUTABLE_DIR,"./icons/sas.png")))

dpg.set_viewport_resize_callback(callback=on_viewport_resize)

########################################################################
setup_dearpygui()
show_viewport()
render_dearpygui_frame()
########################################################################

THEME_INDEX=1
try:
    if cfg['theme']==1:
        theme_callback(1)
    else:
        theme_callback(0)
        THEME_INDEX=0
except:
    theme_callback(1)

try:
    distro_info=Path(path_join(EXECUTABLE_DIR,'distro.info.txt')).read_text(encoding='utf-8')
except Exception as exception_1:
    print(exception_1)
    distro_info = 'Error. No distro.info.txt file.'

portaudio_release,portaudio_descr=get_portaudio_version()
distro_info+= "\nnumpy       " + str(numpy_version) + "\nsounddevice " + str(sounddevice_version) + "\nportaudio release " + str(portaudio_release) + "\n" + portaudio_descr + "\n\nDearPyGui   " + str(dpg.get_dearpygui_version()) + "\n\n"

print(distro_info)
l_info(distro_info)

def track_file(track,tlen):
    return path_join(INTERNAL_DIR, f'track{track}_{tlen}.json')

stream_in=None
stream_out=None

fft_duration=0

refresh_devices()

initial_set_devices()

precalc_ready=False

fft_buckets_quant_change(None,None,False)
tracks_buckets_quant_change(None,None,True)

in_api_callback()
out_api_callback()
fft_callback()

#konieczne ponowienie po fft
out_dev_changed(None,None,True)
in_dev_changed(None,None,True)

next_check = 0
status_shown=True
status_hide_time=0

round_viewport()

if not decorated:
    try:
        dec_width, dec_height = get_item_rect_size("decoration")
        print(f'{dec_width=},{dec_height=}')
    except Exception as decor_exception:
        print(f"{decor_exception=}")
        cons_err(f'{decor_exception=}')

try:
    configure_app(anti_aliased_lines=True,anti_aliased_lines_use_tex=True,anti_aliased_fill=True,docking=False,mouse_draw_cursor=True)
except:
    configure_app(anti_aliased_lines=True,anti_aliased_lines_use_tex=True,anti_aliased_fill=True,docking=False)

on_viewport_resize()
cons_info('\n'*console_visible_lines + 'Press H for help. Press Backspace to clear the console.\n')

def output_frame_buffer_callback_gif(sender, app_data):
    global capture_frames,CAPTURE
    try:
        w,h = app_data.get_width(),app_data.get_height()
        x, y = get_item_pos('plot')
        iw, ih = get_item_rect_size('plot')

        rgba_u8 = (clip(frombuffer(app_data, dtype=float32, count=w*h*4).reshape(h, w, 4), 0.0, 1.0) * 255.0).astype(uint8)

        capture_frames[CAPTURE]=(Image_fromarray(rgba_u8, mode="RGBA").convert("RGB"),Image_fromarray(rgba_u8[y:y+ih, x:x+iw, :], mode="RGBA").convert("RGB"))

    except Exception as ofbce:
        cons_err(f'{ofbce=}')

def capture_loop():
    global CAPTURE,CAPTURE_saving,CAPTURE_INTERVAL,capture_frames

    capture_frames={}

    while CAPTURE:
        output_frame_buffer(callback=output_frame_buffer_callback_gif)

        CAPTURE-=1
        sleep(CAPTURE_INTERVAL)

    if capture_frames:
        CAPTURE_saving=True
        timestamp=str(round(time()))
        duration=int(1000 / CAPTURE_FPS)

        max_frame=max(capture_frames.keys())

        Path(INTERNAL_DIR_IMAGES).mkdir(parents=True,exist_ok=True)

        sorted_keys_but_first=list(sorted(capture_frames.keys(),reverse=True))[1:]

        for i in (1,2,3,4,5):
            filename=f"recording_{timestamp}_{i}_v.gif"
            cons_info(f'saving {filename}...')
            capture_frames[max_frame][0].save(path_join(INTERNAL_DIR_IMAGES,filename),save_all=True,append_images=[capture_frames[key][0] for key in sorted_keys_but_first if not key%i],duration=duration,loop=1)
            filename=f"recording_{timestamp}_{i}_p.gif"
            cons_info(f'saving {filename}...')
            capture_frames[max_frame][1].save(path_join(INTERNAL_DIR_IMAGES,filename),save_all=True,append_images=[capture_frames[key][1] for key in sorted_keys_but_first if not key%i],duration=duration,loop=1)

        CAPTURE_saving=False
        cons_info('')

frames=0
changes=0
fft_calcs=0

fft_calc_sum_time=0.0
fft_proc_sum_time=0.0
fft_peaks_sum_time=0.0

in_errors=0

processing_inside=1.0
processing_outside=1.0

def processing():
    peaks_annos={}
    peaks_count_max=15
    peaks_count_max_m1=14

    global sweeping,processing_inside,processing_outside,fft_values_y_prev,FFT_TDA_FACTOR,FFT_TDA_FACTOR_1m,FFT_SMOOTH_WINDOW
    global redraw_recorded_track_line,frames,track_line_data_y_recorded,sweeping_i,logf_sweep_step,dragging,resizing,samples_chunks_fifo,current_sample_db
    global exiting,PEAKS,changes,fft_calcs,fft_calc_sum_time,in_samples,in_callbacks,current_sample_db_time_samples,data,precalc_ready,fft_proc_sum_time,fft_peaks_sum_time,in_errors,np_fft_rfft

    next_sweep_time=0
    in_callbacks=-1
    in_samples=-1

    new_data=False

    processing_begin=0
    processing_end=0

    do_sleep=False
    next_mic_check=0

    smooth_window=ones(3)/3.0

    while not exiting:
        processing_begin=perf_counter()
        processing_outside+=processing_begin-processing_end

        if precalc_ready:
            while True:
                data_new_chunk_len=0
                data_len=0
                try:
                    data_len=len(data)

                    data_new_chunk,status = samples_chunks_fifo_get()

                    if status:
                        cons_err(f'Input callback Error:{status}')
                        in_errors+=1

                    data_new_chunk_len=len(data_new_chunk)
                    if data_new_chunk_len>data_len:
                        data = data_new_chunk[-data_len:]
                    else:
                        data = np_roll(data,-data_new_chunk_len)
                        data[-data_new_chunk_len:]=data_new_chunk

                    in_callbacks+=1
                    in_samples+=data_new_chunk_len
                    new_data=True
                except IndexError:
                    break
                except Exception as dnc_e:
                    cons_err(f'{dnc_e=}')
                    cons_err(f'{data_new_chunk_len=}')
                    cons_err(f'{data_len=}')

                    break

            if new_data and not PAUSE:
                #dragging or resizing
                new_data=False
                changes+=1

                current_sample_db = float64(10.0) * np_log10( np_mean(np_square(data[-current_sample_db_time_samples:])) + 1e-12)

                new_dict={}
                for fint,(i,v) in peaks_annos.items():
                    tag=f'p{fint}'

                    im1=i-1
                    if im1>0:
                        new_dict[fint]=(im1,v)

                        try:
                            delete_item(tag)
                            col=10
                            add_plot_annotation(tag=tag,label=f'{fint}Hz',parent='plot',default_value=(fint,v),  offset=(10,-10), color=(0,0,0,0))
                        except Exception as ae:
                            print(ae)
                    else :
                        delete_item(tag)

                peaks_annos=new_dict

                if FFT and precalc_ready:
                    try:
                        t1=perf_counter()
                        fft_values_y=float64(20.0)*np_log10( np_abs( np_fft_rfft(data[-FFT_SIZE:]*fft_window)) / FFT_SIZE + 1e-12 )
                        fft_calcs+=1

                        t2=perf_counter()
                        fft_calc_sum_time+=t2-t1

                        if PEAKS:
                            fft_values_y_org=fft_values_y

                        if FFT_FBA:
                            fft_values_means_in_buckets = bincount(fft_bin_indices, weights=fft_values_y)[1:] / fft_bin_counts[1:]

                            fft_values_y=np_array([fft_values_means_in_buckets[i] for i in fft_bin_indices_selected[:-1]])
                            fft_values_x = fft_values_x_bins

                            if FFT_SMOOTH:
                                fft_values_y = np_convolve(np_pad(fft_values_y,FFT_SMOOTH_FACTOR,'reflect'), FFT_SMOOTH_WINDOW, mode='valid')
                        else:
                            fft_values_x = fft_values_x_all

                        if FFT_TDA:
                            if fft_values_y_prev is not None:
                                fft_values_y=FFT_TDA_FACTOR_1m*np_array(fft_values_y) + FFT_TDA_FACTOR*np_array(fft_values_y_prev)
                            fft_values_y_prev=fft_values_y

                        t3=perf_counter()
                        fft_proc_sum_time+=t3-t2

                        if PEAKS:
                            points=len(fft_values_y)

                            dist_half=int(PEAKS_AVG_FACTOR*points/100.0)
                            dist=dist_half*2

                            cumsum = np_cumsum(np_pad(fft_values_y,dist_half,'reflect'))
                            fft_values_y_avg = (cumsum[dist:] - cumsum[:-dist]) / dist
                            if DEBUG:
                                set_value("fft_avg", [fft_values_x, fft_values_y_avg])

                            diffs=fft_values_y-fft_values_y_avg

                            margin=int(1+(PEAKS_AVG_FACTOR/100.0)*PEAKS_DIST_FACTOR*points/100.0)

                            diffs_padded_windows = sliding_window_view( np_pad(diffs, margin, mode="constant", constant_values=-np_inf) , window_shape=2 * margin + 1)

                            maxs=diffs_padded_windows[:, margin] == diffs_padded_windows.max(axis=1)

                            peaks_annos_get = peaks_annos.get

                            for d,fint,v in nlargest(PEAKS_LIMIT,[(d,int(f),v) for m,d,f,v in zip(maxs,diffs,fft_values_x,fft_values_y) if m],key=lambda x: x[0]):
                                curr_i,curr_v=peaks_annos_get(fint,(0,v))
                                peaks_annos[fint]=(min(peaks_count_max,curr_i+2),(v+curr_v*peaks_count_max_m1)/peaks_count_max)

                            t4=perf_counter()
                            fft_peaks_sum_time+=t4-t3

                        if FFT_FILL:
                            set_value("fft_line_shade", [fft_values_x, fft_values_y,[dbmin]*len(fft_values_y)])
                        else:
                            set_value("fft_line2", [fft_values_x, fft_values_y])

                        set_value("fft_line", [fft_values_x, fft_values_y])

                    except Exception as exception_fft:
                        cons_err(f'{exception_fft=}')

                if playing_state==2 and track_line_data_y_recorded:
                    track_line_data_y_recorded[current_bucket]*=TRACKS_TDA_FACTOR
                    track_line_data_y_recorded[current_bucket]+=current_sample_db*TRACKS_TDA_FACTOR_1m
                    redraw_recorded_track_line=True

                set_value('cursor_db_txt', (25000, current_sample_db))
                configure_item('cursor_db_txt',label=f'{round(current_sample_db)}dB')

                if current_sample_db<-110:
                    if processing_begin>next_mic_check:
                        cons_err(f'No signal / Mic not connected ({current_sample_db}dB)')
                        next_mic_check=processing_begin+1

                if redraw_recorded_track_line:
                    track=int(cfg['recorded'])
                    if track!=-1:
                        if cfg['show_track'][track]:
                            set_value(f"track{track}_bg", [bucket_tracks_freqs, track_line_data_y[track]])
                            set_value(f"track{track}", [bucket_tracks_freqs, track_line_data_y[track]])

                    redraw_recorded_track_line=False
            else:
                do_sleep=True
        else:
            do_sleep=True

        processing_end=perf_counter()
        processing_inside+=processing_end-processing_begin
        if do_sleep:
            sleep(0.00001)
            do_sleep=False

Thread(target=processing,daemon=True).start()

def output_frame_buffer_callback(sender, app_data):
    try:
        w,h = app_data.get_width(),app_data.get_height()
        x, y = get_item_pos('plot')
        iw, ih = get_item_rect_size('plot')

        timestamp=strftime('%Y_%m_%d-%H_%M_%S',localtime_catched(time()) )

        Path(INTERNAL_DIR_IMAGES).mkdir(parents=True,exist_ok=True)

        rgba_u8 = (clip(frombuffer(app_data, dtype=float32, count=w*h*4).reshape(h, w, 4), 0.0, 1.0) * 255.0).astype(uint8)

        filename1=f"img{timestamp}.png"
        filename2=f"img{timestamp}-crop.png"

        cons_info(f'saving:{filename1} ...')
        Image_fromarray(rgba_u8, mode="RGBA").save(path_join(INTERNAL_DIR_IMAGES,filename1))

        cons_info(f'saving:{filename2} ...')
        Image_fromarray(rgba_u8[y:y+ih, x:x+iw, :], mode="RGBA").save(path_join(INTERNAL_DIR_IMAGES,filename2))

    except Exception as ofbce:
        cons_err(f'{ofbce=}')

next_redraw=0
def main_loop():
    global sweeping,out_callbacks,out_samples,set_viewport_pos_scheduled,set_viewport_resize_scheduled,schedule_screenshot
    global frames,next_check,sweeping_i,logf_sweep_step,dragging,resizing,samples_chunks_fifo
    global CAPTURE,changes,settings_wrapper_scheduled,in_samples,in_callbacks,cfg,playing_state,lock_frequency,next_redraw
    global console_shift,console_buffer,console_show_end_index,console_buffer_len,themes,fft_calc_sum_time,fft_calcs,console_color_tab,out_errors,in_errors,console_direction_mod,fft_proc_sum_time,fft_peaks_sum_time
    global offset_x,offset_y,processing_inside,processing_outside

    next_sweep_time=0

    frame_time=0.9/TARGET_FPS
    now_end=0

    main_loop_outside=0
    main_loop_inside=0

    dl_tag='draw_layer'

    while is_dearpygui_running():
        now=perf_counter()
        main_loop_outside+=now-now_end

        if set_viewport_pos_scheduled:
            try:
                vp_x, vp_y = get_viewport_pos()
                mouse_x, mouse_y = get_mouse_pos()
                set_viewport_pos((vp_x + mouse_x - offset_x,vp_y + mouse_y - offset_y))
                render_dearpygui_frame()
                set_viewport_pos_scheduled=False
            except Exception as e_pos:
                cons_err(f'{e_pos=}')

        if set_viewport_resize_scheduled:
            try:
                x_resize,y_resize=set_viewport_resize_scheduled
                set_viewport_width(x_resize)
                set_viewport_height(y_resize)
                on_viewport_resize()
                render_dearpygui_frame()
                set_viewport_resize_scheduled=False
            except Exception as e_res:
                cons_err(f'{e_res=}')

        if schedule_screenshot:
            try:
                hide_item('cursor_db_txt')
                hide_item('cursor_f_txt')
                hide_item('cursor_f')

                configure_item('mark_text_1',show=True)
                configure_item('mark_text_2',show=True)
                configure_item('mark_text_3',show=True)
                configure_item('mark_text_4',show=True)
                configure_item('mark_text_5',show=True)
                configure_item('mark_text_6',show=True)
                configure_item('mark_text_7',show=True)
                configure_item('mark_text_8',show=True)
                configure_item('mark_text',show=True)

                render_dearpygui_frame()
                output_frame_buffer(callback=output_frame_buffer_callback)
                render_dearpygui_frame()

                schedule_screenshot=False

                show_item('cursor_db_txt')
                show_item('cursor_f_txt')
                show_item('cursor_f')

                configure_item('mark_text_1',show=False)
                configure_item('mark_text_2',show=False)
                configure_item('mark_text_3',show=False)
                configure_item('mark_text_4',show=False)
                configure_item('mark_text_5',show=False)
                configure_item('mark_text_6',show=False)
                configure_item('mark_text_7',show=False)
                configure_item('mark_text_8',show=False)
                configure_item('mark_text',show=False)
            except Exception as ss_e:
                cons_err(f'{ss_e=}')

        if settings_wrapper_scheduled:
            try:
                height,height_min = settings_wrapper_scheduled
                render_dearpygui_frame()
                if cfg['settings']:
                    set_viewport_min_height(height_min)
                    render_dearpygui_frame()
                    set_viewport_height(height)
                    render_dearpygui_frame()
                    show_item('settings_group')
                else:
                    hide_item('settings_group')
                    render_dearpygui_frame()
                    set_viewport_min_height(height_min)
                    render_dearpygui_frame()
                    set_viewport_height(height)

                render_dearpygui_frame()
                settings_wrapper_scheduled=None
                continue
            except Exception as settings_e:
                cons_err(f'{settings_e=}')

        if now >= next_check :
            next_check = now+1.0

            if DEBUG and not (dragging or resizing or PAUSE):
                try:
                    try:
                        proc_ratio=processing_inside/(processing_inside+processing_outside)
                    except:
                        proc_ratio="Nan"

                    try:
                        main_ratio=main_loop_inside/(main_loop_inside+main_loop_outside)
                    except:
                        main_ratio="Nan"

                    stream_out_cpu_load = stream_out.cpu_load if stream_out else 0
                    stream_in_cpu_load = stream_in.cpu_load if stream_in else 0

                    stream_out_latency = stream_out.latency if stream_out else 0
                    stream_in_latency = stream_in.latency if stream_in else 0
                    part1 = [f"FPS:{frames}/{changes}  sat:{main_ratio:.5f}/{proc_ratio:.5f}\n",
                            f"             Output       Input",
                            f"samples/s  {out_samples:8d}    {in_samples:8d}",
                            f"blocks/s   {out_callbacks:8d}    {in_callbacks:8d}",
                            f"errors/s   {out_errors:8d}    {in_errors:8d}",
                            " ",
                            f"CPU        {stream_out_cpu_load:.6f}    {stream_in_cpu_load:.6f}",
                            f"latency[s] {stream_out_latency:.6f}    {stream_in_latency:.6f}",
                            " ",
                            " "]

                    fft_calc_mean=fft_calc_sum_time/fft_calcs if fft_calcs else 0
                    fft_calc_in_sec=int(1.0/fft_calc_mean) if fft_calc_mean else 0

                    fft_proc_mean=fft_proc_sum_time/fft_calcs if fft_calcs else 0
                    fft_proc_in_sec=int(1.0/fft_proc_mean) if fft_proc_mean and (FFT_TDA or FFT_FBA or FFT_SMOOTH) else 0

                    fft_peaks_mean=fft_peaks_sum_time/fft_calcs if fft_calcs else 0
                    fft_peaks_in_sec=int(1.0/fft_peaks_mean) if fft_peaks_mean and PEAKS else 0

                    fft_proc_sum_time=0
                    fft_calc_sum_time=0
                    fft_peaks_sum_time=0
                    fft_calcs=0

                    part_fft = [f"FFT Window: {round(fft_duration,3)}s",
                                f"FFT Calcs: {fft_calc_mean:.5f}s / {fft_calc_in_sec:5d}/s",
                                f"FFT Procs: {fft_proc_mean:.5f}s / {fft_proc_in_sec:5d}/s",
                                f"FFT Peaks: {fft_peaks_mean:.5f}s / {fft_peaks_in_sec:5d}/s",
                                "",
                                f"   FFT /  FBA  /  act",
                                f"{FFT_POINTS:6d} / {FFT_FBA_SIZE:5d} /{FFT_ACTUAL_BUCKETS:5d}" if FFT_FBA else f"{FFT_POINTS:6d} / ---- / ----",
                                ] if FFT else []

                    list_sum=part1 + part_fft
                    set_value('debug_text','\n'.join(list_sum))

                    l_info(f'DEB:\t{frames}/{changes}\t{main_ratio:.5f}/{proc_ratio:.5f}\t{fft_calc_mean:.5f}:{fft_proc_mean:.5f}:{fft_peaks_mean:.5f}\t{out_samples:}:{in_samples:}\t{out_callbacks:}:{in_callbacks:}\t{out_errors:}:{in_errors:}\t{stream_out_cpu_load:.6f}:{stream_in_cpu_load:.6f}\t{stream_out_latency:.6f}:{stream_in_latency:.6f}')

                except Exception as debug_e:
                    cons_err(f'{debug_e=}')

            if not stream_in and not stream_out:
                cons_err('Output stream not initialized / Input stream not initialized !')
            elif not stream_in:
                cons_err('Input stream not initialized !')
            elif not stream_out:
                cons_warn('Output stream not initialized !')
            elif in_callbacks==0 and in_samples==0:
                cons_err('No Input signal !')
            elif PAUSE:
                cons_warn('Paused.')

            out_samples=0
            out_callbacks=0
            out_errors=0

            frames = 0
            changes = 0
            in_samples = 0
            in_callbacks = 0
            in_errors=0

            main_loop_inside=0
            main_loop_outside=0

            processing_inside=0
            processing_outside=0

        if windows:
            try:
                if playing_state and not (sweeping or lock_frequency) and is_item_hovered("plot"):
                    while ShowCursor(False) >= 0:
                        pass
                else:
                    while ShowCursor(True) < 0:
                        pass
            except Exception as win_cur_e:
                cons_err(f'{win_cur_e=}')

        ##################################
        if sweeping:
            try:
                if now>next_sweep_time:
                    if not PAUSE:
                        sweeping_i+=1
                        if sweeping_i<sweep_steps:
                            f=10**(logf_min_audio+sweeping_i*logf_sweep_step)
                            change_f(f)
                            cons_opt(f'Sweeping:{f:.0f}Hz, hit Esc or click on the graph to abort ...')

                            next_sweep_time=now+sweeping_delay
                        else:
                            sweeping=False
                            play_stop()
            except Exception as sweep_e:
                cons_err(f'{sweep_e=}')

        ##################################

        if exiting:
            break

        if now>next_redraw:
            delete_item('draw_layer', children_only=True)

            mn,mx = get_item_rect_min('plot'),get_item_rect_max('plot')
            x0,y0,x1,y1 = float(mn[0])+41, float(mn[1]+8),float(mx[0])-8, float(mx[1])-27

            x0p1=x0+1
            y0p1=y0+1
            x1m1=x1-1
            y1m1=y1-1

            # left / up
            draw_line((x0p1,y0p1),(x1m1,y0p1), color=INNER_SHADOW, thickness=2, parent=dl_tag)
            draw_line((x0p1,y0p1),(x0p1,y1m1), color=INNER_SHADOW, thickness=2, parent=dl_tag)
            draw_line((x0,y0),(x1,y0),color=OUTER_SHADOW, thickness=1, parent=dl_tag)
            draw_line((x0,y0),(x0,y1),color=OUTER_SHADOW, thickness=1, parent=dl_tag)

            # right / down
            draw_line((x0p1,y1m1),(x1m1,y1m1),color=INNER_HIGHLIGHT, thickness=2, parent=dl_tag)
            draw_line((x1m1,y0p1),(x1m1,y1m1),color=INNER_HIGHLIGHT, thickness=2, parent=dl_tag)
            draw_line((x0,y1),(x1,y1),color=OUTER_HIGHLIGHT, thickness=1, parent=dl_tag)
            draw_line((x1,y0),(x1,y1),color=OUTER_HIGHLIGHT, thickness=1, parent=dl_tag)

            try:
                if console_direction_mod==2:
                    if console_shift<=0:
                        if console_show_end_index<console_buffer_last_elem:
                            console_show_end_index+=1
                            console_shift+=console_line_height

                line_x_pos=330 if DEBUG else slider_width+yaxis_width+20

                for l,(text,code) in enumerate(list(islice(console_buffer,max(0,console_show_end_index-console_visible_lines),console_show_end_index+1))):
                    text_trimmed=text if len(text)<console_visible_chars else text[0:console_visible_chars_m3] + '...'

                    for (mx,my,center) in theme_text_aura:
                        draw_text(pos=(line_x_pos + mx,title_hight + plot_upper_margin + l*console_line_height + console_shift + my),text=text_trimmed,color=console_color_tab[code][center],parent=dl_tag,size=console_fontsize)

                lines_to_show=console_buffer_len-console_show_end_index

                if console_direction_mod==2:
                    if console_shift>0:
                        if lines_to_show>1:
                            console_shift-=int(np_log10(lines_to_show)*console_line_height)
                        else:
                            console_shift-=1

            except Exception as console_e:
                cons_err(f'{console_e=}')

            render_dearpygui_frame()
            next_redraw=now+frame_time
            frames += 1
        else:
            now_end=perf_counter()
            main_loop_inside+=now_end-now
            sleep(0.0001)

gc_collect()
gc_freeze()

main_loop()

cfg['viewport_pos']=get_viewport_pos()
cfg['viewport_height']=get_viewport_height()
cfg['viewport_width']=get_viewport_width()

print('exiting')
sweeping=False
lock_frequency=False

play_stop()
out_stream_stop()

exiting=True

in_stream_stop()

if stream_in:
    stream_in.close()

with open(cfg_file, "w", encoding="utf-8") as f:
    f.write(dumps(cfg,sort_keys=True,indent=4))

for track in range(tracks):
    with open(track_file(track,TRACK_BUCKETS), "w", encoding="utf-8") as f:
        f.write(dumps(track_line_data_y[track],sort_keys=True,indent=4))

destroy_context()
l_info('Exiting.')
sys_exit(0)
