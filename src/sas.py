#!/usr/bin/python3

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
from dearpygui.dearpygui import create_context,file_dialog,add_file_extension,get_plot_mouse_pos,set_value,get_value,bind_item_theme,item_handler_registry,plot,add_line_series,theme,configure_item,render_dearpygui_frame,is_dearpygui_running,destroy_context,theme_component,add_item_clicked_handler,add_item_hover_handler,bind_item_handler_registry,add_mouse_click_handler,add_mouse_release_handler,add_key_press_handler,add_mouse_wheel_handler,handler_registry,add_combo,child_window,table_row,add_checkbox,add_text,add_table_column,window,table,is_item_hovered,tooltip,add_image_button,add_static_texture,texture_registry
from dearpygui.dearpygui import create_viewport,get_viewport_client_width,get_viewport_client_height,set_viewport_vsync,set_viewport_height,hide_item,show_item,set_item_height,set_item_width,get_viewport_height,show_viewport,set_item_pos,set_primary_window,add_radio_button,mvMouseButton_Left,popup
from dearpygui.dearpygui import mvEventType_Enter,mvEventType_Leave,is_key_down,get_item_configuration,group,configure_app,add_spacer,delete_item,add_plot_annotation,set_axis_limits,set_axis_ticks,add_image_series,add_shade_series
from dearpygui.dearpygui import mvKey_LControl,mvKey_LShift,get_mouse_pos,get_viewport_width,get_viewport_pos,set_viewport_width,mvTable_SizingStretchProp,set_viewport_pos,get_item_rect_size,get_item_rect_min,get_item_pos,output_frame_buffer,set_viewport_min_height

from time import strftime,time,localtime,perf_counter,sleep
from gc import disable as gc_disable,enable as gc_enable,collect as gc_collect, freeze as gc_freeze

from numpy import mean as np_mean,square as np_square,float32,ones,hanning,hamming,blackman,bartlett, abs as np_abs,fft as np_fft,log10 as np_log10,__version__ as numpy_version, concatenate as np_concatenate,sum as np_sum, arange, sin as np_sin,zeros, append as np_append,digitize,bincount,isnan,array as np_array, pad as np_pad, convolve as np_convolve,sqrt as np_sqrt, argsort as np_argsort, where as np_where,roll as np_roll, cumsum as np_cumsum,clip,frombuffer,uint8
from sounddevice import InputStream,OutputStream,query_devices,default as sd_default,query_hostapis,__version__ as sounddevice_version,get_portaudio_version,check_input_settings,check_output_settings
import numpy as np
from threading import Thread

from collections import deque

from math import pi, log10, ceil, floor
from PIL import Image

Image_fromarray=Image.fromarray

from pathlib import Path
from json import dumps,loads

import os
from os import name as os_name, system, sep, environ
from os.path import join as path_join, normpath,dirname,abspath

import sys
from sys import exit as sys_exit,argv

from images import image
import logging

l_info = logging.info
l_warning = logging.warning
l_error = logging.error

np_fft_rfft=np_fft.rfft

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    EXECUTABLE_DIR = Path(sys._MEIPASS)
else:
    EXECUTABLE_DIR = Path(__file__).parent

if getattr(sys, 'frozen', False):
    EXECUTABLE_DIR_REAL = os.path.dirname(sys.executable)
else:
    EXECUTABLE_DIR_REAL = os.path.dirname(os.path.abspath(__file__))

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

windows = bool(os_name=='nt')
if windows:
    from sounddevice import WasapiSettings

tracks=8

cfg.setdefault('theme','dark')
cfg.setdefault('track_buckets',256)
cfg.setdefault('viewport_pos',[100,100])
cfg.setdefault('settings',False)

cfg.setdefault('help',True)
HELP=cfg['help']

cfg.setdefault('decorated',False)
cfg.setdefault('fft_fill',True)

cfg.setdefault('pause',False)
PAUSE=cfg['pause']

cfg.setdefault('debug',True)
cfg.setdefault('vsync',False)

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
cfg.setdefault('peaks_dist_factor',3.0)
cfg.setdefault('peaks_threshold',15.0)

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

cfg.setdefault("in_latency",'high')
cfg.setdefault("out_latency",'low')

cfg.setdefault("in_blocksize",'128')
cfg.setdefault("out_blocksize",'128')

cfg.setdefault("allow_all_devices",False)
cfg.setdefault("out_wasapi_exclusive",False)
cfg.setdefault("in_wasapi_exclusive",False)

latency_values=('high','low','default')

out_blocksize_values=(1024,512,256,128,64)

in_blocksize_values=(512,256,128,64,0)

track_line_data_y={}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
            logging.FileHandler(log_file, encoding='utf-8')
    ]
)

from io import BytesIO
VERSION_FILE='version.txt'

HOMEPAGE='https://github.com/PJDude/sas'

f_current=0
playing_state=0
'''
2 - on
1 - ramp on
0 - off
-1 - ramp off
'''

if windows:
    from os import startfile
    import ctypes
    ShowCursor = ctypes.windll.user32.ShowCursor
    LoadCursorW = ctypes.windll.user32.LoadCursorW
    SetCursor = ctypes.windll.user32.SetCursor

    IDC_ARROW    = 32512
    IDC_SIZEALL  = 32646
    IDC_CROSS    = 32515
    IDC_HAND     = 32649

    def load_cursor(idc_id):
        l_info('cursor_loaded')
        return LoadCursorW(None, idc_id)

    arrow_cursor = load_cursor(IDC_ARROW)

def catch(func):
    def wrapper(*args,**kwargs):
        try:
            return func(*args,**kwargs)
        except Exception as e:
            l_error(f'catch:{func},{e}')
            print(f'catch:{func},{e}')
            return None
    return wrapper

@catch
def status_set_frequency():
    global cfg,TRACK_BUCKETS
    res_list = []
    res_list_append = res_list.append
    if current_bucket<TRACK_BUCKETS:
        for track in range(tracks):
            if cfg['show_track'][track]:
                db_temp = round(track_line_data_y[track][current_bucket])
                res_list_append(str(track+1) + ':' + str(db_temp))
    else:
        #print(f'{current_bucket=}')
        pass

    if res_list:
        set_value('status',' '.join(res_list) + ' [#buffer:dBFS]')
    else:
        set_value('status',' ')

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
    set_status(f'saving {filename} ...')
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

phase_step=1.0

def change_f(fpar):
    global current_logf,current_bucket,phase_step,two_pi_by_out_samplerate,TRACK_BUCKETS,phase_step_x_phase_i,phase_i

    if fmin_audio<fpar<fmax_audio:
        current_logf=log10(fpar)
        current_f=fpar

        temp_bucket=logf_to_bucket_tracks(current_logf)
        if temp_bucket<TRACK_BUCKETS:
            current_bucket=temp_bucket

        set_value("cursor_f", ((fpar,fpar), (0,dbmin)))
        set_value('cursor_f_txt', (fpar, -3))
        configure_item('cursor_f_txt',label=f'{round(fpar)}Hz')

        phase_step = two_pi_by_out_samplerate * fpar
        phase_step_x_phase_i = phase_step * phase_i

played_bucket=0
played_bucket_callbacks=0

def audio_output_callback(outdata, frames, time, status):
    global phase,playing_state,played_bucket,played_bucket_callbacks,phase_step,two_pi,current_bucket,out_channel_buffer_mod_index,phase_i,DEBUG,volume_ramp,phase_step_x_phase_i

    if DEBUG:
        global output_callbacks_count,samples_chunks_requested_new
        output_callbacks_count+=1
        samples_chunks_requested_new+=len(outdata)

    if playing_state:
        phase_arr=(phase + phase_step_x_phase_i) % two_pi
        outdata[phase_i, out_channel_buffer_mod_index] = np_sin(phase_arr)
        phase = phase_arr[-1]+phase_step

        if playing_state==1:
            playing_state=2
            outdata[:, out_channel_buffer_mod_index] *= volume_ramp
        elif playing_state==-1:
            playing_state=0
            outdata[:, out_channel_buffer_mod_index] *= volume_ramp[::-1]

        if current_bucket!=played_bucket:
            played_bucket_callbacks=1
            played_bucket=current_bucket
        else:
            played_bucket_callbacks+=1
    else:
        outdata.fill(0)

VSYNC_STATE_NAME='OFF'
def vsync_callback(sender=None, app_data=None):
    l_info(f'vsync_callback:{sender},{app_data}')
    set_viewport_vsync(app_data)
    global VSYNC_STATE_NAME,next_fps
    VSYNC_STATE_NAME=('OFF',' ON')[app_data]
    cfg['vsync']=app_data
    next_fps=0

def sweep_abort():
    global sweeping
    sweeping=False
    configure_item('sweep',texture_tag=ico["play"])

def rec_press(sender=None, app_data=None):
    l_info(f'rec_press:{sender},{app_data}')

sweeping_i=0
def sweep_callback(sender=None, app_data=None):
    l_info(f'sweep_callback:{sender},{app_data}')

    global sweeping,lock_frequency,sweeping_i,track_line_data_y_recorded
    sweeping=(True,False)[sweeping]

    if not track_line_data_y_recorded:
        l_info('no recorded')
        set_status('No track selected for recording !')
        sweep_abort()
        return

    lock_frequency=False

    if sweeping:
        configure_item('sweep',texture_tag=ico["play_on"])
        change_f(fmin_audio)
        play_start()
    else:
        play_stop()

    sweeping_i=0

@catch
def play_start():
    global playing_state,track_line_data_y_recorded,redraw_track_line
    bind_item_theme("cursor_f",red_line_theme)
    playing_state=1

    if track_line_data_y_recorded:
        recorded=int(cfg['recorded'])
        #bind_item_theme(f"track{recorded}_bg",track_recorded_bg_theme)
        #bind_item_theme(f"track{recorded}",track_recorded_core_theme)

        #bind_item_theme(f"track{recorded}_bg",track_recorded_bg_theme)
        #bind_item_theme(f"track{recorded}",track_recorded_core_theme)

    redraw_track_line=True

@catch
def play_stop():
    global playing_state,lock_frequency
    if playing_state==2:
        playing_state=-1
    lock_frequency=False

    bind_item_theme("cursor_f",green_line_theme)
    #playing_state=0

    sweep_abort()

exiting=False

current_sample_db=-120

samples_chunks_fifo=deque()
samples_chunks_fifo_put=samples_chunks_fifo.append
samples_chunks_fifo_get=samples_chunks_fifo.popleft

processed_data_fifo=deque()
processed_data_fifo_put=processed_data_fifo.append
processed_data_fifo_get=processed_data_fifo.popleft

output_callbacks_count=0
samples_chunks_requested_new=0
###########################################################

def audio_input_callback(indata, frames, time_info, status):
    samples_chunks_fifo_put(indata[:, 0].copy())

@catch
def go_to_homepage():
    try:
        if windows:
            set_value('status','opening: %s' % HOMEPAGE)
            startfile(HOMEPAGE)
        else:
            set_value('status','executing: xdg-open %s' % HOMEPAGE)
            system("xdg-open " + HOMEPAGE)
    except Exception as e:
        l_error(f'go_to_homepage error:{e}')

default_api_nr=0

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
    l_info('refresh_devices')
    global default_in_dev,default_out_dev,apis,api_name2api,devices,device_name2device,device_index2device

    default_in_dev=query_devices(kind='input')
    default_out_dev=query_devices(kind='output')

    l_info(' ')
    l_info('APIS:')
    apis = query_hostapis()
    for i,api in enumerate(apis):
        l_info(f'  api:{i}')
        for key,val in api.items():
            l_info(f'    :{key}:{val}')

    api_name2api={ api['name']:api for api in apis if api['devices'] }

    devices=query_devices()
    device_name2device={ device['name']:device for device in devices}
    device_index2device={ device['index']:device for device in devices}

    l_info(' ')
    l_info('DEVICES:')
    for i,dev in enumerate(devices):
        l_info(f'  dev:{i}')
        for key,val in dev.items():
            l_info(f'    :{key}:{val}')
    l_info(' ')

    values_str=' - ' + '\n - '.join(api_name2api)
    configure_item('out_api',items=list(api_name2api.keys())); widget_tooltip(f"Available:\n\n{values_str}\n\n{out_api_tooltip}","out_api")
    configure_item('in_api',items=list(api_name2api.keys())); widget_tooltip(f"Available:\n\n{values_str}","in_api")

def initial_set_devices():
    global api_name2api,device_name2device,default_in_dev,default_out_dev
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

        if in_dev in device_name2device:
            if device_name2device[in_dev]['index'] in api['devices']:
                set_value('in_dev',in_dev)
                l_info('in set by cfg')
                in_set_by_cfg=True
                set_value('in_samplerate',cfg['in_samplerate'])
        else:
            #in_api_callback(None,None,True)
            cfg['in_dev']=query_devices(device=api_name2api[in_api]['default_input_device'])['name']
            set_value('in_dev',cfg['in_dev'])
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

        if out_dev in device_name2device:
            if device_name2device[out_dev]['index'] in api['devices']:
                set_value('out_dev',out_dev)
                l_info('out set by cfg')
                out_set_by_cfg=True
                set_value('out_samplerate',cfg['out_samplerate'])
        else:
            cfg['out_dev']=query_devices(device=api_name2api[out_api]['default_output_device'])['name']
            set_value('out_dev',cfg['out_dev'])
            #out_api_callback(None,None,True)
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

def out_blocksize_changed(sender=None, out_blocksize_str=None,user_data=False):
    l_info(f'out_blocksize_changed:{sender},{out_blocksize_str},{user_data}')
    play_stop()
    out_stream_stop()

    global volume_ramp,phase_i
    out_blocksize=int(out_blocksize_str)

    #volume_ramp = tuple([(i+1.0)/out_blocksize for i in range(out_blocksize)])
    volume_ramp = arange(1, out_blocksize + 1, dtype=float32) / out_blocksize
    phase_i = arange(out_blocksize)

    cfg['out_blocksize']=get_value('out_blocksize')

    if user_data:
        out_stream_init()

def out_latency_changed(sender=None, app_data=None,user_data=False):
    l_info(f'out_latency_changed:{sender},{app_data},{user_data}')
    play_stop()
    out_stream_stop()

    cfg['out_latency']=get_value('out_latency')
    if user_data:
        out_stream_init()

def in_blocksize_changed(sender=None, app_data=None,user_data=False):
    l_info(f'in_blocksize_changed:{sender},{app_data},{user_data}')

    cfg['in_blocksize']=get_value('in_blocksize')

    if user_data:
        in_stream_init()

def in_latency_changed(sender=None, app_data=None,user_data=False):
    l_info(f'in_latency_changed:{sender},{app_data},{user_data}')

    cfg['in_latency']=get_value('in_latency')
    if user_data:
        in_stream_init()

def out_channel_changed(sender=None, app_data=None,user_data=False):
    l_info(f'out_channel_changed:{sender},{app_data},{user_data}')

    cfg['out_channel']=get_value('out_channel')

    play_stop()
    out_stream_stop()

    if user_data:
        out_stream_init()

def out_samplerate_changed(sender=None, app_data=None,user_data=False):
    l_info(f'out_samplerate_changed:{sender},{app_data},{user_data}')

    play_stop()
    out_stream_stop()

    cfg['out_samplerate']=get_value('out_samplerate')

    global two_pi_by_out_samplerate
    two_pi_by_out_samplerate = two_pi/float(get_value("out_samplerate"))

    if user_data:
        common_precalc()

        out_stream_init()

def in_samplerate_changed(sender=None, app_data=None,user_data=False):
    l_info(f'in_samplerate_changed:{sender},{app_data},{user_data}')

    play_stop()
    stream_in.stop()

    cfg['in_samplerate']=get_value('in_samplerate')

    if user_data:
        common_precalc()
        in_stream_init()

def out_stream_stop():
    if stream_out:
        l_info('OutputStream stop.')
        stream_out.stop()

def latency_for_stream(latency):
    if latency=='default':
        return None
    else:
        return latency

def out_stream_init():
    configure_item('out_status',texture_tag=ico['out_off'])
    global stream_out,device_out_current,out_channel_buffer_mod_index

    if stream_out:
        stream_out.stop()
        stream_out.close()

    if cfg['out_wasapi_exclusive'] and cfg['out_api'] == 'Windows WASAPI':
        extra_settings=WasapiSettings(exclusive=True)
        l_info('out WASAPI Exclusive mode !')
    else:
        extra_settings=None

    try:
        channels=int(get_value('out_channel'))
    except:
        channels=1
    out_channel_buffer_mod_index=channels-1

    device=int(device_out_current['index'])
    samplerate=float(get_value('out_samplerate'))
    latency=latency_for_stream(get_value('out_latency'))
    blocksize=int(get_value('out_blocksize'))

    l_info('')
    l_info(f'OutputStream init {device=},{samplerate=},{latency=},{blocksize=},{channels=},{extra_settings=}')

    try:
        stream_out = OutputStream(callback=audio_output_callback, extra_settings=extra_settings,
            device=device,
            samplerate=samplerate,
            latency=latency,
            blocksize=blocksize,
            channels=channels,
            dither_off=True
        )
        #dtype="float32",
        stream_out.start()
        configure_item('out_status',texture_tag=ico['out_on'])
    except Exception as e:
        set_status(f'OutputStream init error:{e}')
        l_error(f'OutputStream init error:{e}')
    else:
        l_info('OutputStream init DONE.')

in_channel_buffer_mod_index=0

def in_channel_changed(sender=None, app_data=None,user_data=False):
    l_info(f'in_channel_changed:{sender},{app_data},{user_data}')

    cfg['in_channel']=get_value('in_channel')

    if stream_in:
        stream_in.stop()

    if user_data:
        in_stream_init()

def in_stream_init():
    configure_item('in_status',texture_tag=ico['in_off'])
    global stream_in,device_in_current,in_channel_buffer_mod_index

    if stream_in:
        stream_in.stop()
        stream_in.close()

    if cfg['in_wasapi_exclusive'] and cfg['in_api'] == 'Windows WASAPI':
        extra_settings=WasapiSettings(exclusive=True)
        l_info('in WASAPI Exclusive mode !')
    else:
        extra_settings=None

    device=int(device_in_current['index'])

    samplerate=float(get_value('in_samplerate'))
    latency=latency_for_stream(get_value('in_latency'))
    blocksize=int(get_value('in_blocksize'))
    channels=int(get_value('in_channel'))

    in_channel_buffer_mod_index=0

    l_info('')
    l_info(f'InputStream init {device=},{samplerate=},{latency=},{blocksize=},{channels=},{extra_settings}')
    try:
        stream_in = InputStream(callback=audio_input_callback, extra_settings=extra_settings,
            device=device,
            samplerate=samplerate,
            latency=latency,
            blocksize=blocksize,
            channels=channels,
            dither_off=True
        )
        # dtype="float32"
        stream_in.start()
        configure_item('in_status',texture_tag=ico['in_on'])

    except Exception as e:
        set_status(f'InputStream init error:{e}')
        l_error(f'InputStream init error:{e}')
    else:
        l_info('InputStream init DONE.')

def hide_info():
    hide_item('info_window')
    on_viewport_resize()

def show_info(message):
    on_viewport_resize()
    set_value('info_text',normalize_text(message,info_chars))
    show_item('info_window')

@catch
def about_wrapper():
    text1= f'Simple Audio Sweeper {VER_TIMESTAMP}\nAuthor: Piotr Jochymek\n\n{HOMEPAGE}\n\nPJ.soft.dev.x@gmail.com\n'
    text2='\n' + distro_info + '\n'
    show_info('\n' + text1+text2 + '\n\nPress H for help')

def normalize_text(text,width):
    res=[]
    for line in text.split('\n'):
        to_add=' '*int((width-len(line))/2)
        res.append(to_add + line + to_add)
    return '\n'.join(res)

def license_wrapper():
    try:
        license_txt=Path(path_join(EXECUTABLE_DIR,'LICENSE')).read_text(encoding='ASCII')
    except Exception as exception_lic:
        l_info(str(exception_lic))
        try:
            license_txt=Path(path_join(dirname(EXECUTABLE_DIR),'LICENSE')).read_text(encoding='ASCII')
        except Exception as exception_lic_2:
            l_info(str(exception_lic_2))
            sys_exit(1)

    show_info('\n'+ license_txt)

def reset_track_press(sender=None, app_data=None):
    l_info(f'resetrack:{sender},{app_data}')

    global cfg,redraw_track_line,track_line_data_y_recorded

    if cfg['recorded']!=-1:
        track=cfg['recorded']

        sweep_abort()
        track_line_data_y_recorded=track_line_data_y[track]=[dbinit]*TRACK_BUCKETS

        redraw_track_line=True
    else:
        print('recording not enabled')

track_line_data_y_recorded=[]
def track_action_callback(sender=None,app_data=None,track=None):
    l_info(f'track_action_callback:{sender},{app_data},{track}')

    Ctrl = is_key_down(mvKey_LControl)

    global cfg,track_line_data_y_recorded,track_line_data_y

    lock_frequency=False
    sweep_abort()
    play_stop()
    status_set_frequency()

    if Ctrl:
        if int(cfg['recorded'])==track:
            cfg['show_track'][track]=True
            cfg['recorded']=-1
            track_line_data_y_recorded=[]
            dpg.move_item(f"track{track}",parent="y_axis")
        else:
            cfg['show_track'][track]=True
            cfg['recorded']=track
            track_line_data_y_recorded=track_line_data_y[track]
            dpg.move_item(f"track{track}",parent="y_axis")
    else:
        cfg['show_track'][track]=not cfg['show_track'][track]

        dpg.move_item(f"track{track}",parent="y_axis")
        if not cfg['show_track'][track]:
            if cfg['recorded']==track:
                cfg['recorded']=-1
                track_line_data_y_recorded=[]

    refresh_tracks()

try:
    VER_TIMESTAMP=Path(path_join(dirname(__file__),VERSION_FILE)).read_text(encoding='ASCII').strip()
except Exception as e_ver:
    print(e_ver)
    VER_TIMESTAMP=''

print(f'{VER_TIMESTAMP=}')

two_pi = pi+pi

phase = 0.0

fmin,fini,fmax=14,442,30000
fmin_audio,fmax_audio=20,20000

logf_min,logf_ini,logf_max=log10(fmin),log10(fini),log10(fmax)
logf_min_audio,logf_max_audio=log10(fmin_audio),log10(fmax_audio)

current_f=fini
current_logf=logf_ini

current_bucket=logf_to_bucket_tracks(current_logf)

dbmin=-122.0
dbmin_display=-123.0
dbinit=dbmin
dbmax_display=dbmax=0.0

dbrange=dbmax-dbmin

dbrange_display=dbmax_display-dbmin_display

redraw_track_line=True

title=f"Simple Audio Sweeper {VER_TIMESTAMP}"

create_context()

ico = {}
for name, data in image.items():
    img = Image.open(BytesIO(data)).convert("RGBA")
    w, h = img.size
    with texture_registry():
        add_static_texture(w, h, [v/255 for px in list(img.get_flattened_data()) for v in px], tag=name)
    ico[name] = name

out_api_id=None

def in_dev_config_items():
    global apis
    api=api_name2api[get_value('in_api')]

    in_api_devices_indexes=api_name2api[get_value('in_api')]['devices']
    l_info(f'{in_api_devices_indexes=}')

    devices = [query_devices(dev_index) for dev_index in in_api_devices_indexes]

    default_input_device_name = device_index2device[api['default_input_device']]['name']

    if get_value('allow_all_devices'):
        in_values=[ dev['name'] for dev in devices]
    else:
        #in_api_id=[api for api in apis if api['name']==api_name][0]
        in_values=[ dev['name'] for dev in devices if dev['max_input_channels'] > 0 and dev['index']]

    tooltip_str='\n'.join([ ('*' if name==default_input_device_name else '-') + ' ' + name for name in in_values])

    widget_tooltip(f"Available:\n\n{tooltip_str}","in_dev")

    configure_item("in_dev",items=in_values)

    return in_values

def out_dev_config_items():
    global apis

    api=api_name2api[get_value('out_api')]

    out_api_devices_indexes=api['devices']
    l_info(f'{out_api_devices_indexes=}')

    devices = [query_devices(dev_index) for dev_index in out_api_devices_indexes]

    default_output_device_name = device_index2device[api['default_output_device']]['name']

    out_values=[ dev['name'] for dev in devices if dev['max_output_channels'] > 0 and dev['index']]

    tooltip_str='\n'.join([ ('*' if name==default_output_device_name else '-') + ' ' + name for name in out_values])
    widget_tooltip(f"Available:\n\n{tooltip_str}","out_dev")

    configure_item("out_dev",items=out_values)

    return out_values

def out_wasapi_exclusive_callback(sender=None, app_data=None,user_data=False):
    cfg['out_wasapi_exclusive']=get_value('out_wasapi_exclusive')

    if windows and cfg['out_api'] == 'Windows WASAPI':
        out_dev_changed(None,None,user_data)

def in_wasapi_exclusive_callback(sender=None, app_data=None,user_data=False):
    cfg['in_wasapi_exclusive']=get_value('in_wasapi_exclusive')

    if windows and cfg['in_api'] == 'Windows WASAPI':
        in_dev_changed(None,None,user_data)

def in_api_callback(sender=None, app_data=None,user_data=False):
    global in_api_id,apis

    api_name=cfg['in_api']=get_value('in_api')
    l_info(f'in_api_callback:{sender},{app_data},{api_name},{user_data}')

    if user_data:
        cfg['in_dev']=query_devices(device=api_name2api[api_name]['default_input_device'])['name']

    cfg['allow_all_devices'] = get_value('allow_all_devices')
    in_dev_config_items()
    #if default_in_dev['name'] in in_values:
    #    cfg['in_dev']=default_in_dev['name']
    #else:
    #    cfg['in_dev']=in_values[-1]

    set_value('in_dev',cfg['in_dev'])

    in_dev_changed(None,None,user_data)

def out_api_callback(sender=None, app_data=None,user_data=False):
    global out_api_id,apis

    api_name=cfg['out_api']=get_value('out_api')
    l_info(f'out_api_callback:{sender},{app_data},{api_name},{user_data}')

    if user_data:
        cfg['out_dev']=query_devices(device=api_name2api[api_name]['default_output_device'])['name']

    out_dev_config_items()
    #if default_out_dev['name'] in out_values:
    #    cfg['out_dev']=default_out_dev['name']
    #else:
    #    cfg['out_dev']=out_values[-1]

    set_value('out_dev',cfg['out_dev'])

    out_dev_changed(None,None,user_data)

def refresh_tracks():
    for track in range(tracks):
        if track==int(cfg['recorded']):
            configure_item(f'showcheck{track}',texture_tag=ico[f"{track+1}_sel"])

            if cfg['theme']=='dark':
                bind_item_theme(f"track{track}_bg",track_recorded_bg_theme_dark)
                bind_item_theme(f"track{track}",track_recorded_core_theme_dark)
            else:
                bind_item_theme(f"track{track}_bg",track_recorded_bg_theme_light)
                bind_item_theme(f"track{track}",track_recorded_core_theme_light)

            configure_item(f"track{track}_bg",show=True)
            configure_item(f"track{track}",show=True)
        elif cfg['show_track'][track]:
            configure_item(f'showcheck{track}',texture_tag=ico[f"{track+1}_on"])

            bind_item_theme(f"track{track}_bg",track_bg_theme)
            bind_item_theme(f"track{track}",track_core_theme)

            configure_item(f"track{track}_bg",show=True)
            configure_item(f"track{track}",show=True)
        else:
            configure_item(f'showcheck{track}',texture_tag=ico[f"{track+1}_off"])

            configure_item(f"track{track}_bg",show=False)
            configure_item(f"track{track}",show=False)

    global redraw_track_line
    redraw_track_line=True

FFT=cfg['fft']
def fft_callback(sender=None, app_data=None):
    global FFT,fft_ready
    fft_ready=False
    FFT=cfg['fft']=get_value('fft')
    l_info(f'fft_callback:{sender},{app_data},{FFT}')
    fft_size_callback()

    configure_item('fft_size',enabled=FFT)
    configure_item('fft_window',enabled=FFT)

    configure_item('fft_fba',enabled=FFT)
    configure_item('fft_fba_size',enabled=FFT)
    configure_item('fft_tda',enabled=FFT)
    configure_item('fft_tda_factor',enabled=FFT)

    configure_item('peaks',enabled=FFT)
    configure_item('peaks_dist_factor',enabled=FFT)
    configure_item('peaks_threshold',enabled=FFT)

FFT_SIZE=cfg['fft_size']
def fft_size_callback(sender=None, app_data=None):
    global cfg,FFT_POINTS,FFT_SIZE,fft_ready
    fft_ready=False

    l_info(f'fft_size_callback:{sender},{app_data}')

    FFT_SIZE=cfg['fft_size']=int(get_value('fft_size'))
    FFT_POINTS=FFT_SIZE//2+1

    fft_window_changed()

def fft_window_changed(sender=None, app_data=None):
    global FFT,fft_window,fft_window_sum,cfg,fft_ready,FFT_SIZE,fft_window_name
    fft_ready=False

    fft_window_name=cfg['fft_window']=get_value('fft_window')

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

    fft_fill_callback()

    l_info(f'fft_window_changed:{sender},{app_data},{cfg["fft_window"]},{len(fft_window)}')

    common_precalc()

    if DEBUG:
        try:
            if environ['SAS_DEBUG_CSV']:
                save_window()
        except:
            pass

FFT_FBA=cfg['fft_fba']
def fft_fba_callback(sender=None, app_data=None):
    global FFT_FBA,fft_ready,cfg
    fft_ready=False
    FFT_FBA=cfg['fft_fba']=get_value('fft_fba')
    l_info(f'fft_fba_callback:{sender},{app_data},{FFT_FBA}')
    fft_fba_size_callback()

    if not FFT_FBA:
        set_value('fft_smooth',False)

    configure_item('fft_smooth',enabled=FFT_FBA)
    configure_item('fft_smooth_factor',enabled=FFT_FBA)

FFT_FBA_SIZE=cfg['fft_fba_size']
def fft_fba_size_callback(sender=None, app_data=None):
    global cfg,FFT_FBA_SIZE,fft_ready
    fft_ready=False
    FFT_FBA_SIZE=cfg['fft_fba_size']=int(get_value('fft_fba_size'))
    l_info(f'fft_fba_size_callback:{sender},{app_data},{FFT_FBA_SIZE}')
    fft_buckets_quant_change()

FFT_TDA=cfg['fft_tda']
def fft_tda_callback(sender=None, app_data=None):
    global FFT_TDA,fft_ready,cfg
    fft_ready=False
    FFT_TDA=cfg['fft_tda']=get_value('fft_tda')
    l_info(f'fft_tda_callback:{sender},{app_data},{FFT_TDA}')
    fft_tda_factor_callback()

    configure_item('fft_tda_factor',enabled=FFT_TDA)

bucket_fft_freqs=[0]
bucket_fft_edges=[0]

time_to_collect_sample=0.125 #[s]

spectrum_sub_bucket_samples=4
sweeping_delay=time_to_collect_sample*1.5/spectrum_sub_bucket_samples
l_info(f'{sweeping_delay=}')

logf_max_audio_m_logf_min_audio = logf_max_audio-logf_min_audio

def fft_buckets_quant_change(sender=None, app_data=None, call_common=True):
    l_info(f'fft_buckets_quant_change:{sender},{app_data},{call_common}')
    global logf_sweep_step,log_bucket_fft_width,log_bucket_fft_width_by2,cfg,fft_ready
    fft_ready=False

    log_bucket_fft_width=logf_max_audio_m_logf_min_audio/FFT_FBA_SIZE
    log_bucket_fft_width_by2=log_bucket_fft_width*0.5

    if call_common:
        common_precalc()

def tracks_buckets_quant_change(sender=None, app_data=None,try_to_load=False):
    global sweep_steps,scale_factor_logf_to_bucket_tracks,log_bucket_tracks_width,log_bucket_tracks_width_by2,TRACK_BUCKETS,bucket_tracks_freqs,track_line_data_y,track_line_data_y_recorded,redraw_track_line,logf_sweep_step

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
                track_line_data_y[track]=[dbmin]*TRACK_BUCKETS
    else:
        for track in range(tracks):
            track_line_data_y[track]=[dbmin]*TRACK_BUCKETS

    track=int(cfg['recorded'])
    if track!=-1:
        track_line_data_y_recorded=track_line_data_y[track]

    redraw_track_line=True

FFT_TDA_FACTOR=float(cfg['fft_tda_factor'])
FFT_TDA_FACTOR_1m=1.0-FFT_TDA_FACTOR
def fft_tda_factor_callback(sender=None, app_data=None):
    l_info(f'fft_tda_factor_callback:{sender},{app_data}')
    global FFT_TDA_FACTOR,fft_ready,FFT_TDA_FACTOR_1m
    fft_ready=False
    FFT_TDA_FACTOR=cfg['fft_tda_factor']=float(get_value('fft_tda_factor'))
    FFT_TDA_FACTOR_1m=1.0-FFT_TDA_FACTOR
    common_precalc()

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
def common_precalc():
    l_info('common_precalc')

    global in_samplerate_by_fft_size,cfg,fft_duration,log_bucket_fft_width,log_bucket_fft_width_by2,bucket_fft_freqs,fft_values_x_all,fft_line_data_y,bucket_fft_edges,fft_bin_indices,fft_bin_counts,next_fps,current_sample_db_time_samples

    current_sample_db_time=0.1
    current_sample_db_time_samples=int(float(get_value('in_samplerate'))*current_sample_db_time)

    in_samplerate_by_fft_size = float(get_value('in_samplerate')) / FFT_SIZE
    fft_duration= 1.0/in_samplerate_by_fft_size

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

    global fft_bin_indices_selected,fft_values_x_bins,fft_ready,FFT_ACTUAL_BUCKETS,fft_values_y_prev,data
    fft_bin_indices_selected=np_array([i for i,i_n in enumerate(isnan(bincount(fft_bin_indices, weights=dummy_data)[1:] / fft_bin_counts[1:])) if not i_n])
    FFT_ACTUAL_BUCKETS=len(fft_bin_indices_selected)
    fft_values_x_bins=np_array([bucket_fft_freqs[i] for i in fft_bin_indices_selected[:-1]])

    fft_values_y_prev=[0]*len(bucket_fft_freqs)

    data=np_concatenate([zeros(FFT_SIZE),data])[:FFT_SIZE]

    fft_ready=True
    next_fps = 0

rates_to_test = (44100,48000,88200,96000,176400,192000,384000)
def check_sample_rates_input(device_id):
    supported = []
    for rate in rates_to_test:
        try:
            check_input_settings(device=device_id, samplerate=rate)
            supported.append(str(rate))
            l_info(f'try_in:{rate}:ok')
        except Exception as try_e:
            l_error(f'try_in:{rate}:{try_e}')
    return tuple(supported)

def check_sample_rates_output(device_id):
    supported = []
    for rate in rates_to_test:
        try:
            check_output_settings(device=device_id, samplerate=rate)
            supported.append(str(rate))
            l_info(f'try_out:{rate}:ok')
        except Exception as try_e:
            l_error(f'try_out:{rate}:{try_e}')
    return tuple(supported)

device_out_current=None

def out_dev_changed(sender=None, app_data=None,user_data=True):
    l_info(f'out_dev_changed:{sender},{app_data}')

    global device_out_current

    dev_name=cfg["out_dev"]=get_value("out_dev")

    out_api_devices_indexes=api_name2api[get_value('out_api')]['devices']
    devices = [query_devices(dev_index) for dev_index in out_api_devices_indexes]

    device_out_current=device_name2device[dev_name]
    l_info(f'{device_out_current=}')

    output_channels=[str(val) for val in range(1,device_out_current['max_output_channels']+1)]
    l_info(f'{output_channels=}')

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

    out_stream_init()

device_in_current=None

def in_dev_changed(sender=None, app_data=None,user_data=False):
    l_info(f'in_dev_changed:{sender},{app_data},{user_data}')

    global device_in_current,fft_ready
    fft_ready=False

    dev_name=cfg["in_dev"]=get_value("in_dev")

    in_api_devices_indexes=api_name2api[get_value('in_api')]['devices']
    devices = [query_devices(dev_index) for dev_index in in_api_devices_indexes]

    device_in_current=device_name2device[dev_name]
    l_info(f'{device_in_current=}')

    input_channels=[str(val) for val in range(1,device_in_current['max_input_channels']+1)]
    l_info(f'{input_channels=}')

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
    #print('click_callback',sender, button_nr)
    hide_info()

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
        global is_dragging,is_resizing
        is_dragging,is_resizing = False,False
        set_viewport_vsync(cfg['vsync'])

        if is_item_hovered("plot"):
            play_stop()
        #else:
            #global sweeping,lock_frequency
    else:
        l_info(f'another button:{button_nr}')

def wheel_callback(sender, val):
    global lock_frequency

    if lock_frequency:
        scroll_mod(val)
    else:
        if is_item_hovered("plot") or is_item_hovered("slider"):
            slide_val=get_value('slider')
            slide_val+=-3*val

            if slide_val<30:
                slide_val=30
            elif slide_val>100:
                slide_val=100

            set_value('slider',slide_val)
            slide_change('slider')

def on_mouse_move_tracks_enter(sender, app_data):
    #print('on_mouse_move_tracks:',sender,app_data)
    button_alias=app_data
    track=int(button_alias[-1])
    #print('track_nr:',track)

    #bind_item_theme(f"track{track}",thick_line_theme)

    configure_item(f"track{track}_bg",show=True)
    configure_item(f"track{track}",show=True)

    #bind_item_theme(f"track{track}_bg",sel_track_bg_theme)
    #bind_item_theme(f"track{track}",sel_track_core_theme)

def on_mouse_move_tracks_leave(sender, app_data):
    button_alias=app_data
    track=int(button_alias[-1])

    refresh_tracks()

is_dragging,is_resizing = False,False

def on_mouse_down(sender, app_data):
    global is_dragging, is_resizing, offset_x, offset_y, curr_vp_x, curr_vp_y
    if not is_dragging:
        offset_x, offset_y = get_mouse_pos(local=False)

        vh,vw = get_viewport_height(),get_viewport_width()
        curr_vp_x, curr_vp_y = get_viewport_pos()

        if offset_y<20:
            is_dragging = True
            set_viewport_vsync(False)
            #print('on_mouse_down - start dragging')
            #gc_disable()
        elif offset_x>vw-30 and offset_y>vh-30:
            is_resizing = True
            set_viewport_vsync(False)

set_viewport_pos_scheduled=False
set_viewport_height_scheduled=False
set_viewport_width_scheduled=False
settings_wrapper_scheduled=False

prev_plot_x=0
def on_mouse_move(sender, app_data):
    global is_dragging, is_resizing, offset_x, offset_y, curr_vp_x, curr_vp_y

    #mouse_x, mouse_y = app_data
    if is_dragging:
        mouse_x, mouse_y = get_mouse_pos(local=False)
        curr_vp_x += mouse_x - offset_x
        curr_vp_y += mouse_y - offset_y

        global set_viewport_pos_scheduled
        set_viewport_pos_scheduled=(curr_vp_x, curr_vp_y)

    elif is_resizing:
        global set_viewport_width_scheduled,set_viewport_height_scheduled
        width,height = get_mouse_pos()
        if width>=viewport_width_min:
            set_viewport_width_scheduled=width

        if height>=viewport_height_min[cfg['settings']]:
            set_viewport_height_scheduled=height

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

BG_SEMI = (128, 128, 128, 220)

LIGHT_BG = (240, 240, 240, 255)
LIGHT_CHILD_BG = (255, 255, 255, 255)
LIGHT_BORDER = (200, 200, 200, 255)
LIGHT_FRAME = (230, 230, 230, 255)
LIGHT_FRAME_HOVER = (200, 200, 255, 255)
LIGHT_FRAME_ACTIVE = (180, 180, 255, 255)
LIGHT_TEXT = (0, 0, 0, 255)
LIGHT_BUTTON = LIGHT_BG #(210, 210, 210, 255)
LIGHT_BUTTON_HOVER = (180, 180, 255, 255)
LIGHT_BUTTON_ACTIVE = (150, 150, 255, 255)
LIGHT_ACCENT = (150, 150, 200, 255)  # check, slider grab, etc.

DARK_BG = (60, 60, 60, 255)
DARK_BG_LIGHTER = (40, 40, 40, 128)
DARK_CHILD_BG = (60, 60, 65, 255)
DARK_BORDER = (90, 90, 90, 255)
DARK_FRAME = (70, 70, 75, 255)
DARK_FRAME_HOVER = (100, 100, 150, 255)
DARK_FRAME_ACTIVE = (120, 120, 200, 255)
DARK_TEXT = (255, 255, 255, 255)
DARK_BUTTON = DARK_BG #(90, 90, 100, 255)
DARK_BUTTON_HOVER = (120, 120, 180, 255)
DARK_BUTTON_ACTIVE = (150, 150, 200, 255)
DARK_ACCENT = (150, 150, 200, 255)  # check, slider grab, etc.

#LIGHT_TOOLTIP_BG = (210, 210, 0, 255)
LIGHT_TOOLTIP_BG = (246, 246, 185, 255)
#DARK_TOOLTIP_BG = (160, 160, 0, 255)
DARK_TOOLTIP_BG = (236, 236, 175, 200)

with theme() as semi_bg_theme:
    with theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_WindowBg, BG_SEMI)

with theme() as white_text:
    with theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_Text, DARK_TEXT)

with theme() as black_text:
    with theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_Text, LIGHT_TEXT)

with theme() as theme_light:
    with theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_WindowBg, LIGHT_BG)
        dpg.add_theme_color(dpg.mvThemeCol_ChildBg, LIGHT_BG)
        dpg.add_theme_color(dpg.mvThemeCol_PopupBg, LIGHT_CHILD_BG)
        dpg.add_theme_color(dpg.mvThemeCol_Border, LIGHT_BORDER)
        dpg.add_theme_color(dpg.mvThemeCol_FrameBg, LIGHT_FRAME)
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, LIGHT_FRAME_HOVER)
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, LIGHT_FRAME_ACTIVE)
        dpg.add_theme_color(dpg.mvThemeCol_Separator, LIGHT_BORDER)

        dpg.add_theme_color(dpg.mvThemeCol_Text, LIGHT_TEXT)
        dpg.add_theme_color(dpg.mvThemeCol_Button, LIGHT_BUTTON)
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, LIGHT_BUTTON_HOVER)
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, LIGHT_BUTTON_ACTIVE)

        dpg.add_theme_color(dpg.mvThemeCol_CheckMark, LIGHT_ACCENT)
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, LIGHT_ACCENT)
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, LIGHT_BG)
        dpg.add_theme_color(dpg.mvThemeCol_Header, LIGHT_FRAME)
        dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, LIGHT_FRAME_HOVER)
        dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, LIGHT_FRAME_ACTIVE)

        #dpg.add_theme_color(dpg.mvThemeCol_Tab, LIGHT_FRAME)
        #dpg.add_theme_color(dpg.mvThemeCol_TabHovered, LIGHT_FRAME_HOVER)
        #dpg.add_theme_color(dpg.mvThemeCol_TabActive, LIGHT_FRAME_ACTIVE)
        #dpg.add_theme_color(dpg.mvThemeCol_TabUnfocused, LIGHT_FRAME)
        #dpg.add_theme_color(dpg.mvThemeCol_TabUnfocusedActive, LIGHT_FRAME_HOVER)

        dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 0, 0, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 0, 0, category=dpg.mvThemeCat_Core)
        #dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 2, 2, category=dpg.mvThemeCat_Core)
        #dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 0, 0, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 0, category=dpg.mvThemeCat_Core)

    #with theme_component(dpg.mvTable):
    #    dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 0, 0)
    with theme_component(dpg.mvChildWindow):
        dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 3, 3)

    with theme_component(dpg.mvPlot):
        dpg.add_theme_color(dpg.mvPlotCol_PlotBg, LIGHT_BG)

    #with theme_component(dpg.mvShadeSeries):
    #    dpg.add_theme_color(dpg.mvPlotCol_Fill,(100, 150, 255, 80),category=dpg.mvThemeCat_Plots)
    #    dpg.add_theme_color(dpg.mvPlotCol_Line,(100, 150, 255, 80),category=dpg.mvThemeCat_Plots)

    with theme_component(dpg.mvTable):
        #dpg.add_theme_color(dpg.mvThemeCol_TableHeaderBg, (50,50,60,255))
        #dpg.add_theme_color(dpg.mvThemeCol_TableRowBgAlt, (40,40,45,255))
        #dpg.add_theme_color(dpg.mvThemeCol_Separator, (255, 0, 0, 255))
        #dpg.add_theme_color(dpg.mvThemeCol_SeparatorHovered, (0, 255, 0, 255))
        #dpg.add_theme_color(dpg.mvThemeCol_SeparatorActive, (0, 0, 255, 255))
        dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 0, 0)

    with theme_component(dpg.mvTooltip):
        dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 3, 3, category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_PopupBg,LIGHT_TOOLTIP_BG,category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_Border,LIGHT_TOOLTIP_BG, category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_Text, LIGHT_TEXT)
        dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize,2,category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_WindowRounding,4)

with theme() as theme_dark:
    with theme_component(dpg.mvAll):
        #dpg.add_theme_color(dpg.mvPlotCol_PlotBg, DARK_BG_LIGHTER)
        #dpg.add_theme_color(dpg.mvPlotCol_FrameBg, DARK_BG_LIGHTER)
        dpg.add_theme_color(dpg.mvThemeCol_WindowBg, DARK_BG)
        dpg.add_theme_color(dpg.mvThemeCol_ChildBg, DARK_BG)
        dpg.add_theme_color(dpg.mvThemeCol_PopupBg, DARK_CHILD_BG)
        dpg.add_theme_color(dpg.mvThemeCol_Border, DARK_BORDER)
        dpg.add_theme_color(dpg.mvThemeCol_FrameBg, DARK_FRAME)
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, DARK_FRAME_HOVER)
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, DARK_FRAME_ACTIVE)

        dpg.add_theme_color(dpg.mvThemeCol_Text, DARK_TEXT)
        dpg.add_theme_color(dpg.mvThemeCol_Button, DARK_BUTTON)
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, DARK_BUTTON_HOVER)
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, DARK_BUTTON_ACTIVE)

        dpg.add_theme_color(dpg.mvThemeCol_CheckMark, DARK_ACCENT)
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, DARK_ACCENT)
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, DARK_BG)
        dpg.add_theme_color(dpg.mvThemeCol_Header, DARK_FRAME)
        dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, DARK_FRAME_HOVER)
        dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, DARK_FRAME_ACTIVE)

        dpg.add_theme_color(dpg.mvThemeCol_Tab, DARK_FRAME)
        dpg.add_theme_color(dpg.mvThemeCol_TabHovered, DARK_FRAME_HOVER)
        dpg.add_theme_color(dpg.mvThemeCol_TabActive, DARK_FRAME_ACTIVE)
        dpg.add_theme_color(dpg.mvThemeCol_TabUnfocused, DARK_FRAME)
        dpg.add_theme_color(dpg.mvThemeCol_TabUnfocusedActive, DARK_FRAME_HOVER)

        dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 0, 0, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 0, 0, category=dpg.mvThemeCat_Core)
        #4dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 2, 2, category=dpg.mvThemeCat_Core)
        #dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 0, 0, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 0, category=dpg.mvThemeCat_Core)

    with theme_component(dpg.mvChildWindow):
        dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 3, 3)

    with theme_component(dpg.mvPlot):
        #dpg.add_theme_color(dpg.mvPlotCol_PlotAreaBg, DARK_BG_LIGHTER)
        dpg.add_theme_color(dpg.mvPlotCol_PlotBg, DARK_BG_LIGHTER)
        #dpg.add_theme_color(dpg.mvPlotCol_FrameBg, DARK_BG_LIGHTER)
        #dpg.add_theme_color(dpg.mvThemeCol_WindowBg, DARK_BG)

    with theme_component(dpg.mvShadeSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Fill,(100, 150, 255, 80),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_color(dpg.mvPlotCol_Line,(100, 150, 255, 80),category=dpg.mvThemeCat_Plots)

    with theme_component(dpg.mvTooltip):
        dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 3, 3, category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_PopupBg,LIGHT_TOOLTIP_BG,category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_Border,LIGHT_TOOLTIP_BG, category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_Text, LIGHT_TEXT)
        dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize,2,category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_WindowRounding,4)

#with theme() as text_ok:
 #   with theme_component(dpg.mvText):
 #       dpg.add_theme_color(dpg.mvThemeCol_Text, (220, 220, 220))

#with theme() as text_alert:
#    with theme_component(dpg.mvText):
#        dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 90, 90))

with theme() as thick_line_theme:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,2.0,category=dpg.mvThemeCat_Plots)

with theme() as thin_line_theme:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,1.0,category=dpg.mvThemeCat_Plots)

with theme() as red_line_theme:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line,(255, 60, 60, 255),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,1.0,category=dpg.mvThemeCat_Plots)
with theme() as sel_track_core_theme:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line,(255, 200, 100, 255),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,1.0,category=dpg.mvThemeCat_Plots)

with theme() as sel_track_bg_theme:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line,(255, 200, 10, 128),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,3.0,category=dpg.mvThemeCat_Plots)
with theme() as track_bg_theme:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line,(128, 128, 128, 128),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,3.0,category=dpg.mvThemeCat_Plots)

########################
with theme() as track_theme_light:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line,(255, 255, 0, 255),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,1.0,category=dpg.mvThemeCat_Plots)

with theme() as track_theme_bg_light:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line,(190, 250, 250, 100),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,5.0,category=dpg.mvThemeCat_Plots)

with theme() as fft_line_theme_light:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line,(0, 0, 0, 130),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,1.0,category=dpg.mvThemeCat_Plots)

    with theme_component(dpg.mvShadeSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Fill,(20, 20, 20, 30),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_color(dpg.mvPlotCol_Line,(0, 0, 0, 130),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,1.0,category=dpg.mvThemeCat_Plots)


with theme() as fft_line2_theme_light:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line,(245, 245, 245, 100),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,5.0,category=dpg.mvThemeCat_Plots)
########################

########################
with theme() as track_theme_dark:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line,(255, 255, 255, 130),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,1.0,category=dpg.mvThemeCat_Plots)

with theme() as track_theme_bg_dark:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line,(60, 10, 10, 100),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,4.0,category=dpg.mvThemeCat_Plots)

with theme() as fft_line_theme_dark:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line,(255, 255, 255, 130),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,1.0,category=dpg.mvThemeCat_Plots)

    with theme_component(dpg.mvShadeSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Fill,(200, 200, 200, 30),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_color(dpg.mvPlotCol_Line,(255, 255, 255, 130),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,1.0,category=dpg.mvThemeCat_Plots)


with theme() as fft_line2_theme_dark:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line,(10, 10, 10, 100),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,5.0,category=dpg.mvThemeCat_Plots)
########################

with theme() as track_core_theme:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line,(128, 128, 128, 128),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,1.0,category=dpg.mvThemeCat_Plots)

with theme() as track_recorded_core_theme_dark:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line,(255, 160, 100, 255),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,1.0,category=dpg.mvThemeCat_Plots)

with theme() as track_recorded_bg_theme_dark:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line,(100,0, 0, 60),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,4.0,category=dpg.mvThemeCat_Plots)

with theme() as track_recorded_core_theme_light:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line,(255, 110, 40, 255),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,1.0,category=dpg.mvThemeCat_Plots)

with theme() as track_recorded_bg_theme_light:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line,(200,100, 0, 20),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,4.0,category=dpg.mvThemeCat_Plots)
########################

with theme() as green_line_theme:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line,(30, 200, 0, 200),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,1.0,category=dpg.mvThemeCat_Plots)

with theme() as grid_line_theme:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line,(128, 128, 128, 128),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,1.0,category=dpg.mvThemeCat_Plots)

def widget_tooltip(message,widget=None):
    if not widget:
        widget=dpg.last_item()

    tag = f"{widget}_tooltip"

    if dpg.does_item_exist(tag):
        dpg.delete_item(tag)

    with dpg.tooltip(widget, delay=0.3, tag=tag):
        dpg.add_text(message)

def key_press_callback(sender, app_data):
    set_status('')
    hide_info()

    Shift = is_key_down(mvKey_LShift)
    Ctrl = is_key_down(mvKey_LControl)

    if app_data==dpg.mvKey_Spacebar:
        pause_val=get_value('pause')
        pause_val=(True,False)[pause_val]
        set_value('pause',pause_val)
        pause_callback()
    else:
        set_value('pause',False)
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
        scroll_mod(1,0.0001)
    elif app_data==dpg.mvKey_Down:
        scroll_mod(-1,0.0001)
    elif app_data==dpg.mvKey_F1:
        about_wrapper()
    elif app_data==dpg.mvKey_F2:
        license_wrapper()
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
        fft_window_changed()
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
            maxv=get_item_configuration('fft_smooth_factor')['max_value']
            minv=get_item_configuration('fft_smooth_factor')['min_value']
            items=list(range(minv,maxv))
            configure_item('fft_smooth_factor',default_value=items[(items.index(get_value('fft_smooth_factor'))+(1,-1)[Shift]) % len(items)])
        fft_smooth_callback()
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
        theme_light_callback()
    elif app_data==dpg.mvKey_D:
        theme_dark_callback()
    elif app_data==dpg.mvKey_S:
        save_image()
    elif app_data==dpg.mvKey_C:
        save_csv()
    elif app_data==dpg.mvKey_V:
        vsync=get_value('vsync')
        vsync=(True,False)[vsync]
        set_value('vsync',vsync)
        vsync_callback(None,vsync)
    elif app_data==dpg.mvKey_H:
        help_val=get_value('help')
        help_val=(True,False)[help_val]
        set_value('help',help_val)
        help_callback()
    elif app_data==dpg.mvKey_P:
        peaks_val=get_value('peaks')
        peaks_val=(True,False)[peaks_val]
        set_value('peaks',peaks_val)
        peaks_callback()
    elif app_data==dpg.mvKey_Pause:
        global CAPTURE,CAPTURE_saving,curr_vp_x,curr_vp_y,vw,vh,viewport_rect
        if CAPTURE:
            CAPTURE=0
        elif not CAPTURE_saving:
            CAPTURE=int(CAPTURE_TIME*CAPTURE_FPS)
            viewport_rect = (curr_vp_x, curr_vp_y, curr_vp_x + vw, curr_vp_y + vh)
            set_status('~')
            Thread(target=capture_loop,daemon=True).start()

    elif app_data==dpg.mvKey_Delete:
        reset_track_press()
    elif app_data==dpg.mvKey_Escape:
        global lock_frequency,sweeping
        play_stop()
        sweeping=False
    else:
        pass

def slide_change(sender):
    val=get_value(sender)
    set_axis_limits("y_axis", dbmin_display*val/100, dbmax_display)

settings_height=190

decorated=cfg['decorated']
FFT_FILL=cfg['fft_fill']

title_hight=(0 if decorated else 26)
status_height=80
plot_min_height=270
plot_axis_height=40

viewport_height_min=(plot_min_height+status_height+title_hight,
                     plot_min_height+status_height+title_hight+settings_height)

viewport_width_min=1080

cfg.setdefault('viewport_height',viewport_height_min[0])
cfg.setdefault('viewport_width',viewport_width_min)

def theme_light_callback():
    l_info('theme_light_callback')
    dpg.bind_theme(theme_light)

    bind_item_theme("fft_line2",fft_line2_theme_light)
    bind_item_theme("fft_line",fft_line_theme_light)

    bind_item_theme("fft_line_shade",fft_line_theme_light)

    for track in range(tracks):
        bind_item_theme(f"track{track}_bg",track_theme_bg_light)
        bind_item_theme(f"track{track}",track_theme_light)

    configure_item('plotbg',texture_tag=ico['bg'])
    if not decorated:
        configure_item('exit_button',texture_tag=ico['exit_light'])

    cfg['theme']='light'
    refresh_tracks()

    bind_item_theme('mark_text_1',white_text)
    bind_item_theme('mark_text_2',white_text)
    bind_item_theme('mark_text_3',white_text)
    bind_item_theme('mark_text_4',white_text)
    bind_item_theme('mark_text_5',white_text)
    bind_item_theme('mark_text_6',white_text)
    bind_item_theme('mark_text_7',white_text)
    bind_item_theme('mark_text_8',white_text)
    bind_item_theme('mark_text',black_text)

def theme_dark_callback():
    l_info('theme_dark_callback')
    dpg.bind_theme(theme_dark)

    bind_item_theme("fft_line2",fft_line2_theme_dark)
    bind_item_theme("fft_line",fft_line_theme_dark)

    bind_item_theme("fft_line_shade",fft_line_theme_dark)

    for track in range(tracks):
        bind_item_theme(f"track{track}_bg",track_theme_bg_dark)
        bind_item_theme(f"track{track}",track_theme_dark)

    configure_item('plotbg',texture_tag=ico['bg_dark'])
    if not decorated:
        configure_item('exit_button',texture_tag=ico['exit_dark'])
    cfg['theme']='dark'
    refresh_tracks()

    bind_item_theme('mark_text_1',black_text)
    bind_item_theme('mark_text_2',black_text)
    bind_item_theme('mark_text_3',black_text)
    bind_item_theme('mark_text_4',black_text)
    bind_item_theme('mark_text_5',black_text)
    bind_item_theme('mark_text_6',black_text)
    bind_item_theme('mark_text_7',black_text)
    bind_item_theme('mark_text_8',black_text)
    bind_item_theme('mark_text',white_text)

PEAKS=cfg['peaks']
def peaks_callback():
    global PEAKS
    cfg['peaks']=PEAKS=get_value('peaks')

    configure_item('peaks_dist_factor',enabled=PEAKS)
    configure_item('peaks_threshold',enabled=PEAKS)

    if PEAKS:
        configure_item("fft_line_fast",show=DEBUG)
        configure_item("fft_line_slow",show=DEBUG)
    else:
        configure_item("fft_line_fast",show=False)
        configure_item("fft_line_slow",show=False)

FFT_SMOOTH=cfg['fft_smooth']
def fft_smooth_callback():
    global FFT_SMOOTH
    cfg['fft_smooth']=FFT_SMOOTH=get_value('fft_smooth')

FFT_SMOOTH_FACTOR=cfg['fft_smooth_factor']
def fft_smooth_factor_change():
    global FFT_SMOOTH_FACTOR
    cfg['fft_smooth_factor']=FFT_SMOOTH_FACTOR=get_value('fft_smooth_factor')

PEAKS_DIST_FACTOR=cfg['peaks_dist_factor']
def peaks_dist_factor_change():
    global PEAKS_DIST_FACTOR
    cfg['peaks_dist_factor']=PEAKS_DIST_FACTOR=get_value('peaks_dist_factor')

PEAKS_THRESHOLD=cfg['peaks_threshold']
def peaks_threshold_change():
    global PEAKS_THRESHOLD
    cfg['peaks_threshold']=PEAKS_THRESHOLD=get_value('peaks_threshold')

DEBUG=cfg['debug']
def debug_callback():
    set_value('debug_text','')
    global DEBUG,next_fps
    cfg['debug']=DEBUG=get_value('debug')
    next_fps=0

    if DEBUG:
        configure_item("fft_line_fast",show=PEAKS)
        configure_item("fft_line_slow",show=PEAKS)
    else:
        configure_item("fft_line_fast",show=False)
        configure_item("fft_line_slow",show=False)

def pause_callback():
    global PAUSE
    cfg['pause']=PAUSE=get_value('pause')

def decorated_callback():
    cfg['decorated']=get_value('decorated')

def fft_fill_callback():
    global FFT_FILL
    FFT_FILL=cfg['fft_fill']=get_value('fft_fill')

    configure_item('fft_line_shade',show=FFT_FILL and FFT)

    configure_item('fft_line',show=FFT)
    configure_item('fft_line2',show=not FFT_FILL and FFT)

def help_off():
    set_value('help',False)
    help_callback()

def help_callback():
    l_info('help_callback')
    global HELP,next_fps
    cfg['help']=HELP=get_value('help')

    if HELP:
        set_value('help_text1',
            "H   - this help\n\n"
            "F1  - about\n"
            "F2  - license\n"
            "-----------------------\n"
            "F12 - settings\n"
            "F11 - debug info\n"
            "-----------------------\n"
            "F   - FFT\n"
            "F3  - FFT size\n"
            "F4  - FFT window\n"
            "F5  - FFT FBA\n"
            "F6  - FFT Smoothing\n"
            "F7  - FFT TDA\n"
            "P - peaks detection\n"
            "G - Filled chart\n"
            "-----------------------\n"
            "\n"
            "L / D - light / dark theme\n"
            )

        set_value('help_text2',
            "1-8 - toggle track visibility\n"
            "       (recording with Ctrl)\n"
            "Del - Reset recorded track\n"
            "\n"
            "------ chart actions ------\n"
            " Left MB - generate specified frequency\n"
            "Right MB - lock frequency\n"
            "   Wheel - reduce value range\n"
            "         - modify locked frequency\n"
            "\n"
            "Arrows - modify locked frequency\n"
            "Space  - pause FFT chart refreshing\n"
            "\n"
            "S / C  - save screenshot / csv\n"
            "pause  - start stop frames capture\n"
            "\n"
            "V - toggle VSync\n"
            )

    else:
        set_value('help_text1','')
        set_value('help_text2','')

    next_fps=0

def settings_wrapper_toggle():
    global cfg
    cfg['settings']=(True,False)[cfg['settings']]
    settings_wrapper()

def settings_wrapper():
    global cfg,settings_wrapper_scheduled
    l_info(f'settings_wrapper:' + str(cfg['settings']))

    if cfg['settings']:
        h=max(viewport_height_min[1],get_viewport_height()+settings_height)
        set_viewport_min_height(viewport_height_min[1])
    else:
        h=max(viewport_height_min[0],get_viewport_height()-settings_height)
        set_viewport_min_height(viewport_height_min[0])

    settings_wrapper_scheduled=h

status_text=''
def set_status(text,alert=False,timeout=2):
    global status_text,status_timeout
    if text!=status_text:
        set_value('status',text)
        status_text=text

        if timeout:
            status_timeout=perf_counter()+timeout

        #if alert:
        #    bind_item_theme("status_text", text_alert)
        #else:
        #    bind_item_theme("status_text", text_ok)

info_chars=0
def plot_drag_callback(sender=None, app_data=None):
    print('plot_drag_callback')

def plot_drop_callback(sender=None, app_data=None):
    print('plot_drop_callback')

vw,vh=0,0
def on_viewport_resize(sender=None, app_data=None):
    global vw,vh,curr_vp_x, curr_vp_y
    vw,vh = get_viewport_client_width(),get_viewport_client_height()
    curr_vp_x, curr_vp_y = get_viewport_pos()

    global info_chars,settings_height,cfg

    info_chars=int(vw/7)

    #30 -magic factor ...
    plot_height  = max(plot_min_height, vh - (settings_height if cfg['settings'] else 0) - status_height - title_hight + 30)

    set_item_height('slider', plot_height-plot_axis_height)
    set_item_pos('slider',[5,title_hight+23])

    set_item_height('plot', plot_height)
    set_item_width('plot', vw-64)

    set_item_pos('info_window',[0,title_hight])
    set_item_pos('debug_text',[85,30+title_hight])
    set_item_pos('help_text1',[385,30+title_hight])
    set_item_pos('help_text2',[700,30+title_hight])

    set_item_pos('central_info',[(vw-64-100)/2,(plot_height)/2])

    title_hight_p_plot_height = title_hight+plot_height
    set_item_pos('mark_text_1',[80-1,title_hight_p_plot_height-30])
    set_item_pos('mark_text_2',[80-1,title_hight_p_plot_height-30-1])
    set_item_pos('mark_text_3',[80,title_hight_p_plot_height-30-1])
    set_item_pos('mark_text_4',[80+1,title_hight_p_plot_height-30-1])
    set_item_pos('mark_text_5',[80+1,title_hight_p_plot_height-30])
    set_item_pos('mark_text_6',[80+1,title_hight_p_plot_height-30+1])
    set_item_pos('mark_text_7',[80,title_hight_p_plot_height-30+1])
    set_item_pos('mark_text_8',[80-1,title_hight_p_plot_height-30+1])
    set_item_pos('mark_text',[80,title_hight_p_plot_height-30])

    set_item_width('info_window', vw)
    set_item_height('info_window', vh)

def exit_press(sender=None, app_data=None):
    global exiting
    exiting=True

create_viewport(title=title,vsync=cfg['vsync'],decorated=decorated)

###################################################
with window(tag='main',no_title_bar=True,no_scrollbar=True,no_resize=True,no_move=True) as main:
    set_primary_window(main, True)

    dpg.add_draw_layer(tag='draw_layer')

    if not decorated:
        with table(header_row=False,resizable=False, policy=mvTable_SizingStretchProp,borders_outerH=False, borders_innerV=False, borders_outerV=False):
            dpg.add_table_column( width_fixed=True, init_width_or_weight=5)
            dpg.add_table_column( width_fixed=True, init_width_or_weight=16)
            dpg.add_table_column( width_fixed=True, init_width_or_weight=300)
            dpg.add_table_column( width_stretch=True, init_width_or_weight=10)
            dpg.add_table_column( width_fixed=True, init_width_or_weight=16)
            dpg.add_table_column( width_fixed=True, init_width_or_weight=3)

            with table_row():
                add_spacer(height=3)

            with table_row():
                add_spacer(width=3)
                add_image_button(ico["sas_small"],callback=None)
                dpg.add_text(title)
                add_spacer()
                add_image_button(ico["exit_dark"],tag='exit_button',callback=exit_press)
                widget_tooltip('Exit')
                add_spacer(width=3)

            with table_row():
                add_spacer(height=3)

    with window(tag='info_window',no_close=True,menubar=False,no_title_bar=True,autosize=False,no_scrollbar=True):
        add_text(tag='info_text')
        hide_item('info_window')


    with table(header_row=False, resizable=False, policy=mvTable_SizingStretchProp,
        borders_innerH=False, borders_innerV=False, borders_outerH=False, borders_outerV=False,
        row_background=False, context_menu_in_body=False, freeze_rows=0, freeze_columns=0,
        no_host_extendX=False, no_host_extendY=False, pad_outerX=False, no_pad_outerX=True):

        add_table_column(width_stretch=True, init_width_or_weight=-1)

        with table_row():
            #with group(tag='plot_combo',horizontal=True,cursor_on_hover=dpg.mvMouseCursor_Arrow):

            with group(tag='plot_combo',horizontal=True):

                add_spacer(width=6)

                dpg.add_slider_float(tag='slider',callback=slide_change,vertical=True,max_value=30,min_value=100,default_value=100,format="",width=10,track_offset=0.5)
                widget_tooltip('Adjust dynamic range')

                with plot(tag='plot',no_mouse_pos=True,no_menus=True,no_frame=True,drag_callback=plot_drag_callback,drop_callback=plot_drop_callback):
                    yticks = (('dBFS',00),('-10',-10),("-20",-20),('-30',-30),('-40',-40),('-50',-50),('-60',-60),('-70',-70),('-80',-80),('-90',-90), ("-100",-100), ("-110",-110), ("-120",-120))
                    xticks = (('',10),("20Hz",20),('',30),('',40),('',50),('',60),('',70),('',80),('',90), ("100Hz",100),
                        ('',200),('',300),('',400),('',500),('',600),('',700),('',800),('',900),("1kHz",1000),
                        ("",2000),("",3000),("",4000),("",5000),("",6000),("",7000),("",8000),("",9000),("10kHz",10000),("20kHz",20000))
                    add_plot_annotation(tag='cursor_f_txt',label='',parent='y_axis',default_value=(10, -5), color=(0, 0, 0, 0), offset=(5,0))
                    add_plot_annotation(tag='cursor_db_txt',label='',parent='y_axis',default_value=(100, -30), color=(0, 0, 0, 0), offset=(0,0))


                    with dpg.plot_axis(dpg.mvXAxis, tag='x_axis',no_highlight=True) as xaxis:
                        configure_item(dpg.last_item(),scale=dpg.mvPlotScale_Log10)
                        set_axis_limits("x_axis", fmin,fmax)
                        set_axis_ticks("x_axis", xticks)

                    with dpg.plot_axis(dpg.mvYAxis, tag = 'y_axis',no_highlight=True):
                        set_axis_limits("y_axis", dbmin_display, dbmax_display)

                        add_image_series(tag='plotbg',texture_tag=ico['bg'],bounds_min=(0, -280),bounds_max=(40000, 0),parent='y_axis')
                        set_axis_ticks("y_axis", yticks)

                        add_line_series((0,0),(dbmin,0),tag="cursor_f")
                        bind_item_theme("cursor_f",red_line_theme)

                        add_line_series([20], [-120], tag="fft_line2")

                        add_line_series([20], [-120], tag="fft_line")
                        add_shade_series([20], y1=[-120], tag="fft_line_shade")

                        add_line_series([20], [-120], tag="fft_line_fast")
                        add_line_series([20], [-120], tag="fft_line_slow")

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

                    add_spacer(height=32)
                    add_image_button(ico["play"],tag='sweep',callback=sweep_callback); widget_tooltip('Run frequency sweep\n\nA track must be selected and recording\nmust be enabled before starting the sweep.')

        with table_row():
            with table(header_row=False, resizable=True, policy=mvTable_SizingStretchProp,
                borders_innerH=False, borders_innerV=False, borders_outerH=False, borders_outerV=False,
                row_background=False, context_menu_in_body=False, freeze_rows=0, freeze_columns=0,
                no_host_extendX=False, no_host_extendY=False, pad_outerX=False, no_pad_outerX=True):

                add_table_column(width_fixed=True, init_width_or_weight=6, width=6)
                #add_table_column(width_fixed=True, init_width_or_weight=18, width=18)
                add_table_column(width_stretch=True, init_width_or_weight=-1)
                add_table_column(width_fixed=True)

                with table_row():
                    add_spacer(height=6)
                    #add_spacer(height=6)

                    with group(width=-1):
                        add_text(tag='status',default_value='')

                    with group(horizontal=True):
                        add_image_button(ico["save_pic"],tag='save_image',callback=save_image); widget_tooltip("Save .png file\n\nkey: S")
                        add_image_button(ico["save_csv"],tag='save_csv_button',callback=save_csv); widget_tooltip("Save .csv file of selected track\n\nkey: C")
                        add_spacer(width=16)
                        add_image_button(ico["home"],tag='homepage',callback=go_to_homepage); widget_tooltip(f'Visit project homepage ({HOMEPAGE})')
                        add_image_button(ico["license"],tag='licensex',callback=license_wrapper); widget_tooltip('Show License\n\nkey: F2')
                        add_image_button(ico["about"],tag='aboutx',callback=about_wrapper); widget_tooltip("Show About\n\nkey: F1")
                        add_spacer(width=16)
                        add_image_button(ico["settings"],tag='settingsx',callback=settings_wrapper_toggle); widget_tooltip("Show settings\n\nkey: F12")
                        add_spacer(width=8)

        with table_row():
            with group(horizontal=True,tag='settings_group'):
                add_spacer(width=5)

                c0width=100
                c1width=250
                with child_window(border=True,autosize_y=False,autosize_x=False,width=c0width+c1width+c1width,no_scrollbar=True,height=settings_height-5):
                    with group(width=-1):
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
                                    add_table_column(width_fixed=True, init_width_or_weight=66)

                                    with table_row():
                                        dpg.add_image(ico["out_off"],tag='out_status',width=16); widget_tooltip('Output Stream status')
                                        add_text(default_value='Output')

                                with table(tag='in_tab1',header_row=False, resizable=False, policy=mvTable_SizingStretchProp):
                                    add_table_column(width_fixed=True, init_width_or_weight=16, width=16)
                                    add_table_column(width_fixed=True, init_width_or_weight=66)
                                    with table_row():
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
                                    add_checkbox(tag='out_wasapi_exclusive',label='WASAPI Exclusive',callback=out_wasapi_exclusive_callback,default_value=cfg['out_wasapi_exclusive'],user_data=True); widget_tooltip('Exclusive mode allows to deliver audio\ndata directly to hardware bypassing software mixing')

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
                                add_combo(tag='fft_size',items=['64','128','256','512','1024','2048','4096','8192','16384','32768','65536','131072','262144','524288'],default_value=cfg['fft_size'],callback=fft_size_callback,width=c2width); widget_tooltip(FFT_size_tooltip)
                            with table_row():
                                add_text(default_value='window'); FFT_window_tooltip='FFT window\n\nF4 / Shift+F4' ; widget_tooltip(FFT_window_tooltip)
                                add_combo(tag='fft_window',items=['ones','hanning','hamming','blackman','bartlett'],default_value=cfg['fft_window'],callback=fft_window_changed,width=c2width); widget_tooltip(FFT_window_tooltip)

                            FFT_buckets_tooltip='Frequency Bin Aggregation\n(equal frequency "buckets" on log scale)\n\nkey: F5 / Shift+F5, (+Ctrl Toggle)'
                            with table_row():
                                add_checkbox(tag='fft_fba',label='FBA',callback=fft_fba_callback,default_value=cfg['fft_fba']); widget_tooltip(FFT_buckets_tooltip)
                                add_combo(tag='fft_fba_size',items=['64','128','256','512','1024','2048','4096'],default_value=cfg['fft_fba_size'],callback=fft_fba_size_callback,user_data=True,width=c2width); widget_tooltip(FFT_buckets_tooltip)
                            with table_row():
                                add_checkbox(tag='fft_smooth',label='Smth',callback=fft_smooth_callback,default_value=cfg['fft_smooth']); widget_tooltip('Smoothing\n\nkey: F6 / Shift+F6 (+Ctrl Toggle)')
                                dpg.add_slider_int(tag='fft_smooth_factor',callback=fft_smooth_factor_change,max_value=12,min_value=1,default_value=cfg['fft_smooth_factor'],format="%d",width=130,track_offset=0.5)
                            with table_row():
                                add_checkbox(tag='fft_tda',label='TDA',callback=fft_tda_callback,default_value=cfg['fft_tda']); FFT_tda_tooltip='Time Domain Averaging\n\nkey: F7 / Shift+F7 (+Ctrl Toggle)'; widget_tooltip(FFT_tda_tooltip)
                                dpg.add_slider_float(tag='fft_tda_factor',callback=fft_tda_factor_callback,max_value=0.95,min_value=0.05,default_value=cfg['fft_tda_factor'],format="%.2f",width=130,track_offset=0.5); widget_tooltip(FFT_tda_tooltip)

                            with table_row():
                                add_checkbox(tag='peaks',label='Peaks',callback=peaks_callback,default_value=cfg['peaks']); widget_tooltip('Peaks detection')

                            with table_row():
                                add_text(default_value='S.L.F.')
                                dpg.add_slider_float(tag='peaks_dist_factor',callback=peaks_dist_factor_change,max_value=5.0,min_value=1.0,default_value=cfg['peaks_dist_factor'],format="%.1f",width=130,track_offset=0.5); widget_tooltip('Short Length Factor\n... that\'s complicated ...')

                            with table_row():
                                add_text(default_value='Threshold')
                                dpg.add_slider_float(tag='peaks_threshold',callback=peaks_threshold_change,max_value=40.0,min_value=1.0,default_value=cfg['peaks_threshold'],format="%.3f",width=130,track_offset=0.5); widget_tooltip('Peak Detection Threshold.')

                with group():
                    with child_window(border=True,autosize_y=False,autosize_x=False,width=220,no_scrollbar=True,height=65):
                        with group(width=-1):
                            add_text(default_value='TRACKS')
                            dpg.add_separator()

                            with table(header_row=False, resizable=False, policy=mvTable_SizingStretchProp,
                                    borders_innerH=False, borders_innerV=False, borders_outerH=False, borders_outerV=False,
                                    row_background=False, context_menu_in_body=False, freeze_rows=0, freeze_columns=0,
                                    no_host_extendX=False, no_host_extendY=False, pad_outerX=False, no_pad_outerX=True):

                                c2width=130
                                add_table_column(width_fixed=True, init_width_or_weight=70, width=70)
                                add_table_column(width_fixed=True, init_width_or_weight=c2width, width=c2width)

                                with table_row():
                                    add_text(default_value='buckets')
                                    add_combo(tag='track_buckets',items=['64','128','256'],default_value=cfg['track_buckets'],callback=tracks_buckets_quant_change,width=c2width)
                                with table_row():
                                    add_text(default_value='TDA'); FFT_tooltip6='Time domain averaging'; widget_tooltip(FFT_tooltip6)
                                    dpg.add_slider_float(tag='tracks_tda_factor',callback=tracks_tda_factor_callback,max_value=0.95,min_value=0.05,default_value=cfg['tracks_tda_factor'],format="%.2f",width=130,track_offset=0.5); widget_tooltip(FFT_tooltip6)

                    with child_window(border=True,autosize_y=False,autosize_x=False,width=220,no_scrollbar=True,height=116):
                        with group():
                            add_text(default_value='DISPLAY SETTINGS')
                            dpg.add_separator()
                            with group(horizontal=True):
                                with group():
                                    add_checkbox(tag='vsync',label='VSync',callback=vsync_callback,default_value=cfg['vsync']); widget_tooltip('When disabled, the graph will be refreshed as fast\nas possible, consuming more CPU power. When enabled,\nrefreshing may lag in some cases.\n\nkey: V')
                                    add_checkbox(tag='debug',label='Debug',callback=debug_callback,default_value=cfg['debug']); widget_tooltip('key: F11')
                                    add_checkbox(tag='decorated',label='Decorate',callback=decorated_callback,default_value=cfg['decorated']); widget_tooltip('Restore default window decorations.\nUse if you experience problems with\ndragging or resizing the main window.\n(Requires application restart)')
                                    with group(horizontal=True):
                                        add_text(default_value='Theme:')
                                        add_image_button(ico["light"],callback=theme_light_callback,width=16); widget_tooltip("Light theme\n\nkey:L")
                                        add_image_button(ico["dark"],callback=theme_dark_callback,width=16); widget_tooltip("Dark theme\n\nkey:D")
                                    add_spacer(width=100)
                                with group():
                                    add_checkbox(tag='help',label='Help',callback=help_callback,default_value=cfg['help']); widget_tooltip('key: H')
                                    add_checkbox(tag='pause',label='Pause',callback=pause_callback,default_value=cfg['pause']); widget_tooltip('key: Space')

                                    add_checkbox(tag='fft_fill',label='FFT Fill',callback=fft_fill_callback,default_value=cfg['fft_fill']); widget_tooltip("Filled graph\n\nkey:G")
                                    add_spacer(width=100)
                add_spacer(width=5)

    add_text(tag='debug_text',default_value='')
    add_text(tag='help_text1',default_value='')
    add_text(tag='help_text2',default_value='')
    add_text(tag='central_info',default_value='')

    add_text(tag='mark_text_1',default_value=title,show=False)
    add_text(tag='mark_text_2',default_value=title,show=False)
    add_text(tag='mark_text_3',default_value=title,show=False)
    add_text(tag='mark_text_4',default_value=title,show=False)
    add_text(tag='mark_text_5',default_value=title,show=False)
    add_text(tag='mark_text_6',default_value=title,show=False)
    add_text(tag='mark_text_7',default_value=title,show=False)
    add_text(tag='mark_text_8',default_value=title,show=False)
    add_text(tag='mark_text',default_value=title,show=False);

    with dpg.handler_registry():
        add_mouse_click_handler(callback=click_callback)
        add_mouse_release_handler(callback=release_callback)
        add_mouse_wheel_handler(callback=wheel_callback)
        add_key_press_handler(callback=key_press_callback)

        #dpg.add_mouse_drag_handler(button=0, threshold=0.0, callback=drag_viewport)
        dpg.add_mouse_down_handler(button=0, callback=on_mouse_down)
        dpg.add_mouse_move_handler(callback=on_mouse_move)

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

on_viewport_resize()

dpg.set_viewport_small_icon(Path(path_join(EXECUTABLE_DIR,"./icons/sas_small.png")))
dpg.set_viewport_large_icon(Path(path_join(EXECUTABLE_DIR,"./icons/sas.png")))

dpg.set_viewport_resize_callback(callback=on_viewport_resize)

dpg.setup_dearpygui()

########################################################################

try:
    if cfg['theme']=='dark':
        theme_dark_callback()
    else:
        theme_light_callback()
except:
    theme_dark_callback()

try:
    distro_info=Path(path_join(EXECUTABLE_DIR,'distro.info.txt')).read_text(encoding='utf-8')
except Exception as exception_1:
    print(exception_1)
    distro_info = 'Error. No distro.info.txt file.'

distro_info+= "\nnumpy       " + str(numpy_version) + "\nsounddevice " + str(sounddevice_version) + "\nportaudio " + str(get_portaudio_version()) + "\n\nDearPyGui   " + str(dpg.get_dearpygui_version()) + "\n\n"

print(distro_info)
l_info(distro_info)

def track_file(track,tlen):
    return path_join(INTERNAL_DIR, f'track{track}_{tlen}.json')

sweeping=False

stream_in=None
stream_out=None

fft_duration=0

refresh_devices()

initial_set_devices()

show_viewport()

fft_ready=False

fft_buckets_quant_change(None,None,False)
tracks_buckets_quant_change(None,None,True)

in_api_callback()
out_api_callback()
fft_callback()

#konieczne ponowienie po fft
out_dev_changed(None,None,True)
in_dev_changed(None,None,True)

status_timeout=0

next_fps = 0
status_shown=True
status_hide_time=0

hide_info()
frames = 0

output_callbacks_all = 0
output_samples = 0

try:
    configure_app(anti_aliased_lines=True,anti_aliased_lines_use_tex=True,anti_aliased_fill=True,docking=False,mouse_draw_cursor=True)
except:
    configure_app(anti_aliased_lines=True,anti_aliased_lines_use_tex=True,anti_aliased_fill=True,docking=False)

help_callback()

gc_collect()
gc_freeze()

def output_frame_buffer_callback_gif(sender, app_data):
    global capture_frames,capture_frames,CAPTURE
    try:
        w,h = app_data.get_width(),app_data.get_height()
        x, y = get_item_pos('plot')
        iw, ih = get_item_rect_size('plot')

        rgba_u8 = (clip(frombuffer(app_data, dtype=float32, count=w*h*4).reshape(h, w, 4), 0.0, 1.0) * 255.0).astype(uint8)

        capture_frames[CAPTURE]=(Image_fromarray(rgba_u8, mode="RGBA").convert("RGB"),Image_fromarray(rgba_u8[y:y+ih, x:x+iw, :], mode="RGBA").convert("RGB"))

    except Exception as ofbce:
        l_error(f"output_frame_buffer_callback error: {ofbce}")

def capture_loop():
    global CAPTURE,CAPTURE_saving,CAPTURE_INTERVAL,viewport_rect,capture_frames

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
            set_status(f'saving gif {i} v...')
            capture_frames[max_frame][0].save(path_join(INTERNAL_DIR_IMAGES,f"recording_{timestamp}_{i}_v.gif"),save_all=True,append_images=[capture_frames[key][0] for key in sorted_keys_but_first if not key%i],duration=duration,loop=1)
            set_status(f'saving gif {i} p...')
            capture_frames[max_frame][1].save(path_join(INTERNAL_DIR_IMAGES,f"recording_{timestamp}_{i}_p.gif"),save_all=True,append_images=[capture_frames[key][1] for key in sorted_keys_but_first if not key%i],duration=duration,loop=1)

        CAPTURE_saving=False
        set_status('')

frames_change=0
def processing():
    peaks_annos=set()
    peaks_annos_clear = peaks_annos.clear

    CENTRAL_INFO_SHOWN=False

    global sweeping,output_callbacks_all,output_callbacks_count,output_samples,samples_chunks_requested_new,status_timeout,fft_window_sum
    global redraw_track_line,frames,next_fps,track_line_data_y_recorded,sweeping_i,logf_sweep_step,is_dragging,is_resizing,samples_chunks_fifo,current_sample_db
    global exiting,PEAKS,frames_change,rec_samples,input_callbacks_all,current_sample_db_time_samples,data

    next_sweep_time=0
    input_callbacks_all=0
    rec_samples=0

    new_data=False

    while not exiting:
        if DEBUG :
            output_callbacks_all+=output_callbacks_count
            output_callbacks_count=0

            output_samples+=samples_chunks_requested_new
            samples_chunks_requested_new=0

        while True:
            try:
                data_new_chunk=samples_chunks_fifo_get()
                data_new_chunk_len=len(data_new_chunk)
                data = np_roll(data,-data_new_chunk_len)
                data[-data_new_chunk_len:]=data_new_chunk
                input_callbacks_all+=1
                rec_samples+=data_new_chunk_len
                new_data=True
            except IndexError:
                break
            except Exception as data_new_chunk_error:
                l_error(f'{data_new_chunk_error=}')
                break

        if new_data and not (is_dragging or is_resizing or PAUSE):
            new_data=False
            frames_change+=1

            #from numpy.random import randn
            #data = randn(cfg['fft_size'])

            current_sample_db = 10 * log10( np_mean(np_square(data[-current_sample_db_time_samples:])) + 1e-12)

            if not PEAKS:
                for fint in peaks_annos:
                    delete_item(f'peak{fint}')
                peaks_annos_clear()

            if FFT and fft_ready:
                try:
                    fft_values_y=20*np_log10( np_abs( np_fft_rfft(data[-FFT_SIZE:]*fft_window)) / FFT_SIZE + 1e-12 )

                    if FFT_FBA:
                        fft_values_means_in_buckets = bincount(fft_bin_indices, weights=fft_values_y)[1:] / fft_bin_counts[1:]
                        fft_values_y=np_array([fft_values_means_in_buckets[i] for i in fft_bin_indices_selected[:-1]])
                        fft_values_x = fft_values_x_bins

                        if FFT_SMOOTH:
                            for i_smooth in range(FFT_SMOOTH_FACTOR):
                                csum = np_cumsum(np_pad(fft_values_y,2,'reflect'))
                                fft_values_y = (csum[3:] - csum[:-3])/3

                    else:
                        fft_values_x = fft_values_x_all

                    if FFT_TDA:
                        try:
                            fft_values_y=FFT_TDA_FACTOR_1m*np_array(fft_values_y) + FFT_TDA_FACTOR*np_array(fft_values_y_prev)
                        except:
                            pass

                    if PEAKS:
                        points=len(fft_values_y)

                        dist_fast_half=int(PEAKS_DIST_FACTOR*points/64)
                        dist_fast=dist_fast_half*2

                        csum_fast = np_cumsum(np_pad(fft_values_y,dist_fast_half,'reflect'))
                        window_sum_fast = csum_fast[dist_fast:] - csum_fast[:-dist_fast]
                        fft_values_y_avg_fast = window_sum_fast / dist_fast

                        dist_slow_half=points//16
                        dist_slow=dist_slow_half*2

                        csum_slow = np_cumsum(np_pad(fft_values_y_avg_fast,dist_slow_half,'reflect'))
                        window_sum_slow = csum_slow[dist_slow:] - csum_slow[:-dist_slow]
                        fft_values_y_avg_slow = window_sum_slow / dist_slow

                        if DEBUG:
                            set_value("fft_line_fast", [fft_values_x, fft_values_y_avg_fast])
                            set_value("fft_line_slow", [fft_values_x, fft_values_y_avg_slow])

                        area_len_threshold=PEAKS_DIST_FACTOR*points/64

                        peaks_annos_new=set()
                        peaks_annos_new_add=peaks_annos_new.add
                        area_len=0

                        min_val=0
                        max_val=-200
                        max_val_f=-1

                        for i,(f,v,mask) in enumerate(zip(fft_values_x,fft_values_y,fft_values_y_avg_fast > fft_values_y_avg_slow)):
                            if mask:
                                area_len+=1
                                if v<min_val:
                                    min_val=v
                                if v>max_val:
                                    max_val=v
                                    max_val_f=f

                            else:
                                if area_len>1:
                                    if area_len>area_len_threshold:
                                        ratio=max_val-min_val
                                        if ratio>PEAKS_THRESHOLD:
                                            peaks_annos_new_add((ratio,int(max_val_f),max_val))

                                    area_len=0
                                    max_val=-999
                                    min_val=0
                                    max_val_f=0

                        if peaks_annos_new:
                            peaks_annos_new_fints={fint for ratio,fint,v in peaks_annos_new}

                            for ratio,fint,v in peaks_annos_new:
                                if fint not in peaks_annos:
                                    add_plot_annotation(tag=f'peak{fint}',label=f'{fint}Hz',parent='plot',default_value=(fint,v), color=(100, 100, 100, 130), offset=(16,-10))
                        else:
                            peaks_annos_new_fints={}

                        for fint in peaks_annos:
                            if fint not in peaks_annos_new_fints:
                                delete_item(f'peak{fint}')

                        if peaks_annos_new:
                            peaks_annos=peaks_annos_new_fints

                    if FFT_FILL:
                        set_value("fft_line_shade", [fft_values_x, fft_values_y,[dbmin]*len(fft_values_y)])
                    else:
                        set_value("fft_line2", [fft_values_x, fft_values_y])

                    set_value("fft_line", [fft_values_x, fft_values_y])

                    if FFT_TDA:
                        fft_values_y_prev=fft_values_y

                except Exception as exception_fft:
                    l_error(f'FFT Exception:{exception_fft}')
                    print('FFT Exception:',exception_fft)

            if playing_state==2 and track_line_data_y_recorded and current_bucket<TRACK_BUCKETS:
                track_line_data_y_recorded[current_bucket]*=TRACKS_TDA_FACTOR
                track_line_data_y_recorded[current_bucket]+=current_sample_db*TRACKS_TDA_FACTOR_1m
                redraw_track_line=True

            set_value('cursor_db_txt', (25000, current_sample_db))
            configure_item('cursor_db_txt',label=f'{round(current_sample_db)}dB')

            if current_sample_db<-110:
                set_status('No signal / Mic not connected ...',1)
                CENTRAL_INFO_SHOWN=True
                set_value('central_info',""
                            "     No signal !    \n"
                            "(Mic not connected ?)")
                help_off()
            elif status_timeout!=0:
                now = perf_counter()
                if now>status_timeout:
                    status_timeout=0
            elif CENTRAL_INFO_SHOWN :
                set_value('central_info','')
                CENTRAL_INFO_SHOWN=False

            if redraw_track_line:
                track=int(cfg['recorded'])
                if track!=-1:
                    if cfg['show_track'][track]:
                        set_value(f"track{track}_bg", [bucket_tracks_freqs, track_line_data_y[track]])
                        set_value(f"track{track}", [bucket_tracks_freqs, track_line_data_y[track]])

                redraw_track_line=False
        else:
            sleep(0.0001)

Thread(target=processing,daemon=True).start()

def output_frame_buffer_callback(sender, app_data):
    try:
        w,h = app_data.get_width(),app_data.get_height()
        x, y = get_item_pos('plot')
        iw, ih = get_item_rect_size('plot')

        timestamp=strftime('%Y_%m_%d-%H_%M_%S',localtime_catched(time()) )

        Path(INTERNAL_DIR_IMAGES).mkdir(parents=True,exist_ok=True)

        rgba_u8 = (clip(frombuffer(app_data, dtype=float32, count=w*h*4).reshape(h, w, 4), 0.0, 1.0) * 255.0).astype(uint8)

        Image_fromarray(rgba_u8, mode="RGBA").save(path_join(INTERNAL_DIR_IMAGES,f"img{timestamp}.png"))
        Image_fromarray(rgba_u8[y:y+ih, x:x+iw, :], mode="RGBA").save(path_join(INTERNAL_DIR_IMAGES,f"img{timestamp}-crop.png"))

    except Exception as ofbce:
        l_error(f"output_frame_buffer_callback error: {ofbce}")

def main_loop():
    global sweeping,output_callbacks_all,output_callbacks_count,output_samples,samples_chunks_requested_new,set_viewport_pos_scheduled,set_viewport_width_scheduled,set_viewport_height_scheduled,schedule_screenshot,status_timeout,fft_window_sum
    global redraw_track_line,frames,next_fps,track_line_data_y_recorded,sweeping_i,logf_sweep_step,is_dragging,is_resizing,samples_chunks_fifo
    global CAPTURE,frames_change,settings_wrapper_scheduled,rec_samples,input_callbacks_all,cfg,playing_state,lock_frequency
    next_sweep_time=0

    while is_dearpygui_running():
        if set_viewport_pos_scheduled:
            try:
                set_viewport_pos(set_viewport_pos_scheduled)
                render_dearpygui_frame()
                set_viewport_pos_scheduled=False
                sleep(0.0001)
                continue
            except Exception as pos_e:
                l_error(f'{pos_e=}')
                set_status(f'{pos_e=}')

        if set_viewport_width_scheduled:
            try:
                set_viewport_width(set_viewport_width_scheduled)
                on_viewport_resize()
                render_dearpygui_frame()
                set_viewport_width_scheduled=False
                sleep(0.0001)
                continue
            except Exception as width_e:
                l_error(f'{width_e=}')
                set_status(f'{width_e=}')

        if set_viewport_height_scheduled:
            try:
                set_viewport_height(set_viewport_height_scheduled)
                set_viewport_height_scheduled=False
                on_viewport_resize()
                render_dearpygui_frame()
                sleep(0.0001)
                continue
            except Exception as heigth_e:
                l_error(f'{heigth_e=}')
                set_status(f'{heigth_e=}')

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
                l_error(f'{ss_e=}')
                set_status(f'{ss_e=}')

        if settings_wrapper_scheduled:
            try:
                if cfg['settings']:
                    set_viewport_height(settings_wrapper_scheduled)
                    on_viewport_resize()
                    show_item('settings_group')
                else:
                    hide_item('settings_group')
                    set_viewport_height(settings_wrapper_scheduled)
                    on_viewport_resize()

                settings_wrapper_scheduled=None
                render_dearpygui_frame()
                continue
            except Exception as settings_e:
                l_error(f'{settings_e=}')
                set_status(f'{settings_e=}')

        if DEBUG and not (is_dragging or is_resizing or PAUSE):
            try:
                now = perf_counter()

                if now >= next_fps :
                    part1 = [f"VSync:{VSYNC_STATE_NAME}   FPS:{frames} / (real:{frames_change}) \n",
                            f"             Output       Input",
                            f"samples/s  {output_samples:8d}    {rec_samples:8d}",
                            f"blocks/s   {output_callbacks_all:8d}    {input_callbacks_all:8d}",
                            f"CPU        {stream_out.cpu_load if stream_out else '':.6f}    {stream_in.cpu_load if stream_in else '':.6f}",
                            f"latency[s] {stream_out.latency if stream_out else '':.6f}    {stream_in.latency if stream_in else '':.6f}",
                            f"type        {stream_out.dtype if stream_out else ''}     {stream_in.dtype if stream_in else ''}\n"]

                    part_fft = [f"FFT Window: {round(fft_duration,3)}s ({fft_window_name})",
                                "",
                                f"   FFT /  FBA  /  act",
                                f"{FFT_POINTS:6d} / {FFT_FBA_SIZE:5d} /{FFT_ACTUAL_BUCKETS:5d}"  if FFT_FBA else f"{FFT_POINTS:6d} / ---- / ----",
                                f"TDA_FACTOR: {FFT_TDA_FACTOR:.2f}" if FFT_TDA else ""
                                ] if FFT else []

                    set_value('debug_text','\n'.join(part1 + part_fft))
                    frames = 0
                    frames_change = 0
                    input_callbacks_all = 0
                    rec_samples = 0

                    output_callbacks_all = 0
                    output_samples = 0

                    next_fps = now+1.0
            except Exception as debug_e:
                l_error(f'{debug_e=}')
                set_status(f'{debug_e=}')

        render_dearpygui_frame()

        if windows:
            try:
                if playing_state and not (sweeping or lock_frequency) and is_item_hovered("plot"):
                    while ShowCursor(False) >= 0:
                        pass
                else:
                    while ShowCursor(True) < 0:
                        pass
            except Exception as win_cur_e:
                l_error(f'{win_cur_e=}')
                set_status(f'{win_cur_e=}')

        frames += 1

        ##################################
        if sweeping:
            try:
                now = perf_counter()
                if now>next_sweep_time:
                    sweeping_i+=1
                    if sweeping_i<sweep_steps:
                        f=10**(logf_min_audio+sweeping_i*logf_sweep_step)
                        change_f(f)
                        set_value('status','Sweeping (' + str(round(f))+ ' Hz), Click on the graph to abort ...')

                        next_sweep_time=now+sweeping_delay
                    else:
                        sweeping=False
                        play_stop()
            except Exception as sweep_e:
                l_error(f'{sweep_e=}')
                set_status(f'{sweep_e=}')
        ##################################

        if exiting:
            break

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

if stream_in:
    stream_in.stop()
    stream_in.close()

with open(cfg_file, "w", encoding="utf-8") as f:
    f.write(dumps(cfg,sort_keys=True,indent=4))

for track in range(tracks):
    with open(track_file(track,TRACK_BUCKETS), "w", encoding="utf-8") as f:
        f.write(dumps(track_line_data_y[track],sort_keys=True,indent=4))

destroy_context()
l_info('Exiting.')
sys_exit(0)
