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

import dearpygui.dearpygui as dpg
from dearpygui.dearpygui import create_context,file_dialog,add_file_extension,get_plot_mouse_pos,set_value,get_value,bind_item_theme,item_handler_registry,plot,add_line_series,theme,configure_item,render_dearpygui_frame,is_dearpygui_running,destroy_context,theme_component,add_item_clicked_handler,add_item_hover_handler,bind_item_handler_registry,add_mouse_click_handler,add_mouse_release_handler,add_key_press_handler,add_mouse_wheel_handler,handler_registry,add_combo,child_window,table_row,add_checkbox,add_text,add_table_column,window,table,is_item_hovered,tooltip,add_image_button,add_static_texture,texture_registry,output_frame_buffer
from dearpygui.dearpygui import create_viewport,get_viewport_client_width,get_viewport_client_height,set_viewport_vsync,set_viewport_height,hide_item,show_item,set_item_height,set_item_width,get_viewport_height,show_viewport,set_item_pos,set_primary_window,add_radio_button,mvMouseButton_Left,popup
from dearpygui.dearpygui import mvEventType_Enter,mvEventType_Leave,is_key_down,get_item_configuration,group,configure_app,add_spacer,delete_item,add_plot_annotation,set_axis_limits,set_axis_ticks,add_image_series,add_shade_series,theme,theme_component
from dearpygui.dearpygui import mvKey_LControl,get_mouse_pos,get_viewport_width,get_viewport_pos,set_viewport_width,mvTable_SizingStretchProp,set_viewport_pos

from time import strftime,time,localtime,perf_counter
from gc import disable as gc_disable,enable as gc_enable,collect as gc_collect, freeze as gc_freeze

from numpy import mean as np_mean,square as np_square,float32,ones,hanning,hamming,blackman,bartlett, abs as np_abs,fft as np_fft,log10 as np_log10,__version__ as numpy_version, concatenate as np_concatenate,sum as np_sum, arange, sin as np_sin,zeros, append as np_append,digitize,bincount,isnan,array as np_array, pad as np_pad, convolve as np_convolve,sqrt as np_sqrt, argsort as np_argsort, where as np_where,roll as np_roll, cumsum as np_cumsum
from sounddevice import InputStream,OutputStream,query_devices,default as sd_default,query_hostapis,__version__ as sounddevice_version
import numpy as np

from collections import deque

from math import pi, log10, ceil, floor
from PIL import Image

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

#EXECUTABLE_FILE = normpath(abspath(sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]))
#EXECUTABLE_DIR = dirname(EXECUTABLE_FILE)

INTERNAL_DIR = sep.join([EXECUTABLE_DIR_REAL,"sas-internal"])
INTERNAL_DIR_CSV_DEBUG = sep.join([EXECUTABLE_DIR_REAL,"sas-internal",'csv-debug'])
INTERNAL_DIR_LOGS = sep.join([EXECUTABLE_DIR_REAL,"sas-internal",'logs'])
INTERNAL_DIR_IMAGES = sep.join([EXECUTABLE_DIR_REAL,"sas-internal",'images'])

Path(INTERNAL_DIR_CSV_DEBUG).mkdir(parents=True,exist_ok=True)
Path(INTERNAL_DIR_LOGS).mkdir(parents=True,exist_ok=True)
Path(INTERNAL_DIR_IMAGES).mkdir(parents=True,exist_ok=True)

Path(INTERNAL_DIR).mkdir(parents=True,exist_ok=True)

print(f'{INTERNAL_DIR=}')

def localtime_catched(t):
    try:
        #mtime sometimes happens to be negative (Virtual box ?)
        return localtime(t)
    except:
        return localtime(0)

log_file = path_join(INTERNAL_DIR_LOGS, strftime('%Y_%m_%d-%H_%M_%S',localtime_catched(time()) ) +'.txt')
cfg_file = path_join(INTERNAL_DIR, 'sas.cfg')

print(f'{log_file=}')

cfg={}
cfg_setdefault=cfg.setdefault

try:
    with open(cfg_file, "r", encoding="utf-8") as f:
        cfg=loads(f.read())
    print(f'cfg_file "{cfg_file}" opened successfully')
except Exception as e:
    print(f'cfg file "{cfg_file}" opening error {e}')

cfg_setdefault('theme','dark')

#TRACK_BUCKETS=256
tracks=8

cfg_setdefault('track_buckets',256)

cfg_setdefault('viewport_pos',[100,100])
cfg_setdefault('viewport_size',[1300,400])

cfg_setdefault('help',True)
HELP=cfg['help']

cfg_setdefault('debug',True)

cfg_setdefault('vsync',True)

cfg_setdefault('fft',True)
cfg_setdefault('fft_size',8192)
cfg_setdefault('fft_window','blackman')
cfg_setdefault('fft_fba',True)
cfg_setdefault('fft_fba_size',1024)
cfg_setdefault('fft_tda',False)
cfg_setdefault('fft_tda_factor',0.1)

cfg_setdefault('fft_smooth',False)
cfg_setdefault('fft_smooth_factor',1)

cfg_setdefault('peaks',False)
cfg_setdefault('peaks_dist_factor',1.0)
cfg_setdefault('peaks_threshold',5.0)

cfg_setdefault('show_track',[False]*tracks)
cfg_setdefault('recorded',-1)

print(f'{cfg=}')

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

windows = bool(os_name=='nt')
if windows:
    from sounddevice import WasapiSettings

np_fft_rfft=np_fft.rfft

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
    filename='sas.csv'
    set_status(f'saving {filename} ...')

    try:
        with open(filename,'w',encoding='utf-8') as f:
            f.write("# Created with " + title + "\n")
            f.write("#frequency[Hz],level[dBFS]\n")
            f.write(f"#tracks:" + ','.join([str(track) for track in range(tracks) if cfg['show_track'][track]]) + "\n")

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
    global schedule_screenshot,filename_full_screenshot
    filename_full_screenshot = path_join(INTERNAL_DIR_IMAGES, 'sas.png')

    if os.path.isfile(filename_full_screenshot):
        os.remove(filename_full_screenshot)

    output_frame_buffer(filename_full_screenshot)

    schedule_screenshot=True

scale_factor_logf_to_bucket_fft=1
scale_factor_logf_to_bucket_tracks=1

def logf_to_bucket_fft(logf):
    return int(round(scale_factor_logf_to_bucket_fft * (logf - logf_min_audio)))

def logf_to_bucket_tracks(logf):
    return int(round(scale_factor_logf_to_bucket_tracks * (logf - logf_min_audio)))

phase_step=1.0

def change_f(fpar):
    global current_logf,current_bucket,phase_step,two_pi_by_out_samplerate,schedule_screenshot,TRACK_BUCKETS

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

played_bucket=0
played_bucket_callbacks=0

def audio_output_callback(outdata, frames, time, status):
    global phase,playing_state,played_bucket,played_bucket_callbacks,phase_step,two_pi,current_bucket,out_channel_buffer_mod_index,phase_i,DEBUG

    if DEBUG:
        global output_callbacks_count,samples_chunks_requested_new
        output_callbacks_count+=1
        samples_chunks_requested_new+=len(outdata)

    if playing_state:
        phase_arr=(phase + phase_step * phase_i) % two_pi
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
    VSYNC_STATE_NAME=('OFF','ON')[app_data]
    cfg['vsync']=app_data
    next_fps=0

def sweep_abort():
    global sweeping
    sweeping=False
    configure_item('sweep',texture_tag=ico["play"])

def rec_press(sender=None, app_data=None):
    l_info(f'rec_press:{sender},{app_data}')

sweeping_i=0
def sweep_press(sender=None, app_data=None):
    l_info(f'sweep_press:{sender},{app_data}')

    global sweeping,lock_frequency,sweeping_i,track_line_data_y_recorded
    sweeping=(True,False)[sweeping]

    if not track_line_data_y_recorded:
        l_info('no recorded')
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
        bind_item_theme(f"track{recorded}_bg",track_recorded_bg_theme)
        bind_item_theme(f"track{recorded}",track_recorded_core_theme)

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

device_default_input=None
device_default_output=None

@catch
def refresh_devices():
    l_info('refresh_devices')
    global apis,default_api_nr,devices,device_default_input,device_default_output

    apis = query_hostapis()
    default_api_nr=-1
    l_info(f'')
    l_info(f'Host APIs:')
    for i,api in enumerate(apis):
        l_info('')
        for key,val in api.items():
            l_info(f'  {key}:{val}')
            if api['devices']:
                default_api_nr=i

    device_default_input_index,device_default_output_index = sd_default.device

    l_info('')
    l_info('Query Devices ...')
    devices=query_devices()

    for dev in devices:
        if dev['index']==device_default_input_index:
            device_default_input=dev
            default_api_nr=dev['hostapi']
        if dev['index']==device_default_output_index:
            device_default_output=dev
            default_api_nr=dev['hostapi']

    l_info(f'{default_api_nr=}')
    l_info(f'{device_default_input=}')
    l_info(f'{device_default_output=}')

    if default_api_nr!=-1:
        l_info(f'Defaults:{apis[default_api_nr]["name"]},{device_default_input["name"]},{device_default_output["name"]}')
        set_value('api_in',apis[default_api_nr]['name'])
        set_value('api_out',apis[default_api_nr]['name'])
    else:
        l_error(f'No default API !')

    l_info('Devices:')
    for dev in devices:
        l_info('')
        for key,val in dev.items():
            l_info(f'  {key}:{val}')

latency_values=('high','low',0.01,0.02,0.03,0)

out_blocksize_values=(2048,1024,512,256)
out_blocksize_default=256
out_latency_default='low'

in_blocksize_values=(512,256,128,64,0)
in_blocksize_default=64 if windows else 256
in_latency_default='low' if windows else 'high'

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

    if user_data:
        out_stream_init()

def out_latency_changed(sender=None, app_data=None,user_data=False):
    l_info(f'out_latency_changed:{sender},{app_data},{user_data}')
    play_stop()
    out_stream_stop()

    if user_data:
        out_stream_init()

def in_blocksize_changed(sender=None, app_data=None,user_data=False):
    l_info(f'in_blocksize_changed:{sender},{app_data},{user_data}')

    if user_data:
        in_stream_init()

def in_latency_changed(sender=None, app_data=None,user_data=False):
    l_info(f'in_latency_changed:{sender},{app_data},{user_data}')

    if user_data:
        in_stream_init()

def out_channel_changed(sender=None, app_data=None,user_data=False):
    l_info(f'out_channel_changed:{sender},{app_data},{user_data}')

    play_stop()
    out_stream_stop()

    if user_data:
        out_stream_init()

def out_stream_stop():
    if stream_out:
        l_info('OutputStream stop.')
        stream_out.stop()

def latency_for_stream(latency):
    if not latency in ('low','high'):
        try:
            latency=float(latency)
        except:
            latency=0
            set_value('out_latency',0)
    return latency

def out_stream_init():
    global stream_out,device_out_current,out_channel_buffer_mod_index

    if stream_out:
        stream_out.stop()
        stream_out.close()

    extra_settings=None
    try:
        if environ['SAS_WASAPI_EXCLUSIVE']:
            extra_settings=WasapiSettings(exclusive=True)
            print('WASAPI Exclusive mode !')
    except:
        pass

    try:
        channels=int(get_value('out_channel'))
    except:
        channels=1
    out_channel_buffer_mod_index=channels-1

    device=int(device_out_current['index'])
    samplerate=float(device_out_current['default_samplerate'])
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
        l_error(f'OutputStream init error:{e}')
        configure_item('out_status',texture_tag=ico['out_off'])
    else:
        l_info('OutputStream init DONE.')

in_channel_buffer_mod_index=0
@catch
def in_channel_changed(sender=None, app_data=None,user_data=False):
    l_info(f'in_channel_changed:{sender},{app_data},{user_data}')

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

    device=int(device_in_current['index'])

    samplerate=float(device_in_current['default_samplerate'])
    latency=latency_for_stream(get_value('in_latency'))
    blocksize=int(get_value('in_blocksize'))
    channels=1
    in_channel_buffer_mod_index=0

    l_info('')
    l_info(f'InputStream init {device=},{samplerate=},{latency=},{blocksize=},{channels=}')
    try:
        stream_in = InputStream(callback=audio_input_callback,
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
    #bind_item_theme('info_window', semi_bg_theme)

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
    if track_line_data_y_recorded:
        sweep_abort()
        track_line_data_y_recorded=[dbinit]*TRACK_BUCKETS
        redraw_track_line=True
    else:
        print('recording not enabled for track',track)

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
        else:
            cfg['show_track'][track]=True
            cfg['recorded']=track
            track_line_data_y_recorded=track_line_data_y[track]
    else:
        cfg['show_track'][track]=not cfg['show_track'][track]
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

#TODO
#in_samplerate = 44100
two_pi = pi+pi

phase = 0.0

fmin,fini,fmax=10,442,30000
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

api_out_id=None

def api_in_callback(sender=None, app_data=None):
    global api_in_id,apis,devices

    api_name=get_value('api_in')
    l_info(f'api_in_changed:{sender},{app_data},{api_name}')

    api_in_id=[api for api in apis if api['name']==api_name][0]
    in_values=[ dev['name'] for dev in devices if dev['max_input_channels'] > 0 and dev['index'] in api_in_id['devices'] ]
    in_dev_name=get_value("in_dev")

    configure_item("in_dev",items=in_values)

    device_default_input_name=device_default_input['name']
    l_info(f'defaults:{device_default_input_name}')

    if in_values:
        if in_dev_name not in in_values:
            if device_default_input_name in in_values:
                set_value("in_dev",device_default_input_name)
            else:
                set_value("in_dev",in_values[0])

    in_dev_changed(None,None)

def api_out_callback(sender=None, app_data=None):
    global api_out_id,apis,devices

    api_name=get_value('api_out')
    l_info(f'api_out_changed:{sender},{app_data},{api_name}')

    api_out_id=[api for api in apis if api['name']==api_name][0]
    out_values=[ dev['name'] for dev in devices if dev['max_output_channels'] > 0 and dev['index'] in api_out_id['devices'] ]

    out_dev_name=get_value("out_dev")

    configure_item("out_dev",items=out_values)

    device_default_output_name=device_default_output['name']
    l_info(f'defaults:{device_default_output_name}')

    if out_values:
        if out_dev_name not in out_values:
            if device_default_output_name in out_values:
                set_value("out_dev",device_default_output_name)
            else:
                set_value("out_dev",out_values[0])

    if out_values:
        if out_dev_name not in out_values:
            if device_default_output_name in out_values:
                set_value("out_dev",device_default_output_name)
            else:
                set_value("out_dev",out_values[0])

    out_dev_changed(None,None)

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
FFT_SIZE_MAX=65536
def fft_size_callback(sender=None, app_data=None):
    global cfg,FFT_POINTS,FFT_SIZE,fft_ready
    fft_ready=False

    l_info(f'fft_size_callback:{sender},{app_data}')

    FFT_SIZE=cfg['fft_size']=int(get_value('fft_size'))
    FFT_POINTS=FFT_SIZE//2+1
    set_status(f'fft_size_callback:{FFT_SIZE}')

    fft_window_changed()

def fft_window_changed(sender=None, app_data=None):
    global FFT,fft_window,fft_window_sum,cfg,fft_ready,FFT_SIZE
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

    configure_item("fft_line2", show=FFT)
    configure_item("fft_line", show=FFT)

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
    global scale_factor_logf_to_bucket_fft,logf_sweep_step,log_bucket_fft_width,log_bucket_fft_width_by2,cfg,fft_ready
    fft_ready=False

    scale_factor_logf_to_bucket_fft=cfg['fft_fba_size']/logf_max_audio_m_logf_min_audio

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

tda_tracks=0.0
tda_tracks_1m=1.0
def tda_tracks_callback(sender=None, app_data=None):
    l_info(f'tda_tracks_callback:{sender},{app_data}')
    global tda_tracks,tracks_ready,tda_tracks_1m
    tda_tracks=float(app_data)
    tda_tracks_1m=1.0-tda_tracks
    common_precalc()

FFT_ACTUAL_BUCKETS=0
def common_precalc():
    l_info('common_precalc')

    global in_samplerate_by_fft_size,cfg,fft_duration,log_bucket_fft_width,log_bucket_fft_width_by2,bucket_fft_freqs,fft_values_x_all,fft_line_data_y,bucket_fft_edges,fft_bin_indices,fft_bin_counts,next_fps

    in_samplerate_by_fft_size = in_samplerate / FFT_SIZE
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
                #save_buckets_tracks()
                #save_buckets_edges()
                save_buckets_fft()
                save_FFT_POINTS()
                save_fft_bin_indices()
                save_fft_bin_counts()
        except:
            pass

    global fft_bin_indices_selected,fft_values_x_bins,fft_ready,FFT_ACTUAL_BUCKETS,fft_values_y_prev
    fft_bin_indices_selected=np_array([i for i,i_n in enumerate(isnan(bincount(fft_bin_indices, weights=dummy_data)[1:] / fft_bin_counts[1:])) if not i_n])
    FFT_ACTUAL_BUCKETS=len(fft_bin_indices_selected)
    fft_values_x_bins=np_array([bucket_fft_freqs[i] for i in fft_bin_indices_selected[:-1]])

    fft_values_y_prev=[0]*len(bucket_fft_freqs)

    fft_ready=True
    next_fps = 0

device_out_current=None

def out_dev_changed(sender=None, app_data=None):
    l_info(f'out_dev_changed:{sender},{app_data}')

    global device_out_current

    out_dev_name=get_value("out_dev")

    device_out_current=[device for device in devices if device['name']==out_dev_name][0]

    output_channels=[str(val) for val in range(1,device_out_current['max_output_channels']+1)]
    l_info(f'{output_channels=}')

    configure_item("out_channel",items=output_channels)

    out_channel_value=get_value("out_channel")

    if not out_channel_value or out_channel_value not in output_channels:
        out_channel_value=1
        set_value("out_channel",out_channel_value)

    global out_samplerate,two_pi_by_out_samplerate
    out_samplerate=int(device_out_current['default_samplerate'])
    set_value("out_samplerate",out_samplerate)

    two_pi_by_out_samplerate = two_pi/out_samplerate

    out_channel_changed(None,out_channel_value)
    out_latency_changed(None,out_latency_default)
    out_blocksize_changed(None,out_blocksize_default)

    out_stream_init()

device_in_current=None

def in_dev_changed(sender=None, app_data=None,user_data=False):
    l_info(f'in_dev_changed:{sender},{app_data},{user_data}')

    global device_in_current,fft_ready
    fft_ready=False

    dev_name=get_value("in_dev")

    device_in_current=[device for device in devices if device['name']==dev_name][0]

    input_channels=[str(val) for val in range(1,device_in_current['max_input_channels']+1)]
    l_info(f'{input_channels=}')

    configure_item("in_channel",items=input_channels)

    in_channel_value=get_value("in_channel")

    if not in_channel_value or in_channel_value not in input_channels:
        in_channel_value=1
        set_value("in_channel",in_channel_value)

    global in_samplerate
    in_samplerate=int(device_in_current['default_samplerate'])
    set_value("in_samplerate",str(in_samplerate))

    in_channel_changed(None,in_channel_value)
    in_latency_changed(None,in_latency_default)
    in_blocksize_changed(None,in_blocksize_default)

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
            sweep_abort()

            if lock_frequency:
                lock_frequency=False
                play_stop()
            else:
                lock_frequency=True

                play_start()
                status_set_frequency()

def release_callback(sender, button_nr):
    #print('release_callback',sender, button_nr)
    if button_nr==0:
        if is_item_hovered("plot"):
            #if not sweeping:
            play_stop()
        else:

            #global sweeping,lock_frequency
            global is_dragging,is_resizing
            set_viewport_vsync(cfg['vsync'])
            is_dragging,is_resizing = False,False
            print('release_callback - end dragging')
            #gc_enable()

        #lock_frequency=False

        #if not sweeping:
        #    play_stop()
        #    status_set_frequency()
    #elif button_nr==1:
    #    sweep_abort()
    else:
        l_info(f'another button:{button_nr}')

def wheel_callback(sender, val):
    global lock_frequency

    if lock_frequency:
        scroll_mod(val)
    else:
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

        vh = get_viewport_height()
        vw = get_viewport_width()

        curr_vp_x, curr_vp_y = get_viewport_pos()

        if offset_y<20:
            is_dragging = True
            set_viewport_vsync(False)
            print('on_mouse_down - start dragging')
            #gc_disable()
        elif offset_x>vw-30 and offset_y>vh-30:
            is_resizing = True

set_viewport_pos_scheduled=cfg['viewport_pos']
set_viewport_size_scheduled=cfg['viewport_size']

prev_plot_x=0
def on_mouse_move(sender, app_data):
    global is_dragging, is_resizing, offset_x, offset_y, curr_vp_x, curr_vp_y

    if is_item_hovered("plot"):
        #print('move - plot')
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
        #mouse_x, mouse_y = app_data
        mouse_x, mouse_y = get_mouse_pos(local=False)
        if is_dragging:
            curr_vp_x = curr_vp_x + mouse_x - offset_x
            curr_vp_y = curr_vp_y + mouse_y - offset_y

            global set_viewport_pos_scheduled
            set_viewport_pos_scheduled=[curr_vp_x, curr_vp_y]

        elif is_resizing:
            global set_viewport_size_scheduled
            set_viewport_size_scheduled=[mouse_x,mouse_y]

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
LIGHT_ACCENT = (50, 50, 70, 255)  # check, slider grab, etc.

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

LIGHT_TOOLTIP_BG = (210, 210, 0, 255)
DARK_TOOLTIP_BG = (160, 160, 0, 255)

with theme() as semi_bg_theme:
    with theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_WindowBg, BG_SEMI)

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
        #dpg.add_theme_color(dpg.mvPlotCol_Fill, LIGHT_BG)

    with theme_component(dpg.mvShadeSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Fill,
            (100, 150, 255, 80),
            category=dpg.mvThemeCat_Plots
        )

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
        #dpg.add_theme_color(dpg.mvPlotCol_Fill, DARK_BG_LIGHTER)
        #dpg.add_theme_color(dpg.mvPlotCol_FrameBg, DARK_BG_LIGHTER)
        #dpg.add_theme_color(dpg.mvThemeCol_WindowBg, DARK_BG)

    with theme_component(dpg.mvShadeSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Fill,
            (100, 150, 255, 80),
            category=dpg.mvThemeCat_Plots
        )

    with theme_component(dpg.mvTooltip):
        dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 3, 3, category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_PopupBg,DARK_TOOLTIP_BG,category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_Border,DARK_TOOLTIP_BG, category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_Text, DARK_TEXT)
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
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,4.0,category=dpg.mvThemeCat_Plots)

with theme() as fft_line_theme_light:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line,(0, 0, 0, 130),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,1.0,category=dpg.mvThemeCat_Plots)

with theme() as fft_line2_theme_light:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line,(245, 245, 245, 100),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,4.0,category=dpg.mvThemeCat_Plots)
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

with theme() as fft_line2_theme_dark:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line,(10, 10, 10, 100),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,4.0,category=dpg.mvThemeCat_Plots)
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
        dpg.add_theme_color(dpg.mvPlotCol_Line,(255, 150, 80, 255),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,1.0,category=dpg.mvThemeCat_Plots)

with theme() as track_recorded_bg_theme_light:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line,(200,100, 0, 20),category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight,4.0,category=dpg.mvThemeCat_Plots)
########################

with theme() as std_dev_cloud_theme:
    with theme_component(dpg.mvShadeSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Fill,(128, 128, 128, 25),category=dpg.mvThemeCat_Plots)

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
    with tooltip(widget, delay=0.3):
        add_text(message)

def key_press_callback(sender, app_data):
    set_status('')
    hide_info()

    Shift = is_key_down(dpg.mvKey_LShift)

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
    elif app_data==dpg.mvKey_F3:
        items=get_item_configuration('fft_window')['items']
        configure_item('fft_window',default_value=items[(items.index(get_value('fft_window'))+(1,-1)[Shift]) % len(items)])
        fft_window_changed()
    elif app_data==dpg.mvKey_F4:
        items=get_item_configuration('fft_size')['items']
        configure_item('fft_size',default_value=items[(items.index(get_value('fft_size'))+(1,-1)[Shift]) % len(items)])
        fft_size_callback()
    elif app_data==dpg.mvKey_F5:
        items=get_item_configuration('fft_fba_size')['items']
        configure_item('fft_fba_size',default_value=items[(items.index(get_value('fft_fba_size'))+(1,-1)[Shift]) % len(items)])
        fft_fba_size_callback()
    elif app_data==dpg.mvKey_F6:
        items=get_item_configuration('fft_tda_factor')['items']
        configure_item('fft_tda_factor',default_value=items[(items.index(get_value('fft_tda_factor'))+(1,-1)[Shift]) % len(items)])
        fft_tda_factor_callback(None,get_value('fft_tda_factor'))
    elif app_data==dpg.mvKey_F7:
        items=get_item_configuration('track_buckets')['items']
        configure_item('track_buckets',default_value=items[(items.index(get_value('track_buckets'))+(1,-1)[Shift]) % len(items)])
        tracks_buckets_quant_change()
    elif app_data==dpg.mvKey_F8:
        items=get_item_configuration('tda_tracks')['items']
        configure_item('tda_tracks',default_value=items[(items.index(get_value('tda_tracks'))+(1,-1)[Shift]) % len(items)])
        tda_tracks_callback(None,get_value('tda_tracks'))
    elif app_data==dpg.mvKey_F12:
        settings_wrapper()
    elif app_data==dpg.mvKey_F11:
        set_value('debug',(True,False)[get_value('debug')])
        debug_callback()
    elif app_data==dpg.mvKey_L:
        theme_light_callback()
    elif app_data==dpg.mvKey_D:
        theme_dark_callback()
    elif app_data==dpg.mvKey_S:
        save_image()
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

decorated=False
try:
    if environ['SAS_DECORATED']:
        decorated=True
except:
    pass

title_hight=(0 if decorated else 26)
status_height=80
plot_min_height=200
plot_axis_height=40
viewport_height_min=plot_min_height+status_height+title_hight

def theme_light_callback():
    l_info('theme_light_callback')
    dpg.bind_theme(theme_light)
    bind_item_theme("fft_line_avg",std_dev_cloud_theme)
    bind_item_theme("fft_line2",fft_line2_theme_light)
    bind_item_theme("fft_line",fft_line_theme_light)

    for track in range(tracks):
        bind_item_theme(f"track{track}_bg",track_theme_bg_light)
        bind_item_theme(f"track{track}",track_theme_light)

    configure_item('plotbg',texture_tag=ico['bg'])
    configure_item('exit_button',texture_tag=ico['exit_light'])
    cfg['theme']='light'
    refresh_tracks()

def theme_dark_callback():
    l_info('theme_dark_callback')
    dpg.bind_theme(theme_dark)
    bind_item_theme("fft_line_avg",std_dev_cloud_theme)
    bind_item_theme("fft_line2",fft_line2_theme_dark)
    bind_item_theme("fft_line",fft_line_theme_dark)

    for track in range(tracks):
        bind_item_theme(f"track{track}_bg",track_theme_bg_dark)
        bind_item_theme(f"track{track}",track_theme_dark)

    configure_item('plotbg',texture_tag=ico['bg_dark'])
    configure_item('exit_button',texture_tag=ico['exit_dark'])
    cfg['theme']='dark'
    refresh_tracks()

PEAKS=cfg['peaks']
def peaks_callback():
    global PEAKS
    cfg['peaks']=PEAKS=get_value('peaks')

    configure_item('peaks_dist_factor',enabled=PEAKS)
    configure_item('peaks_threshold',enabled=PEAKS)

    configure_item('fft_line_avg',show=PEAKS)

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

def help_off():
    set_value('help',False)
    help_callback()

def help_callback():
    l_info('help_callback')
    global HELP,next_fps
    cfg['help']=HELP=get_value('help')

    if HELP:
        set_value('help_text',
            "H - show this help\n"
            "F12 - toggle settings\n"
            "F11 - toggle debug info\n"
            "F   - toggle FFT\n"
            "F3 / Shift+F3 - FFT window\n"
            "F4 / Shift+F4 - FFT size\n"
            "F5 / Shift+F5 - FFT FBA\n"
            "F6 / Shift+F6 - FFT TDA\n"
            "F7 / Shift+F7 - Recorded Tracks Frequency 'buckets'\n"
            "F8 / Shift+F8 - Recorded Tracks TDA\n"
            "\n"
            "F1 / F2 - about / license\n"
            "L / D - light / dark theme\n"
            "\n"
            "V - toggle VSync\n"
            "S / C - save screenshot / csv\n"
            "P - peaks detection\n"
            "1,2,3,4,5,6,7,8 - toggle track (recording with Ctrl)]\n")
    else:
        set_value('help_text','')

    next_fps=0

create_viewport(title=title,width=1200,min_height=viewport_height_min,vsync=cfg['vsync'],decorated=decorated)

settings_shown=True

def settings_wrapper():
    global cfg,settings_shown
    l_info(f'settings_wrapper:{settings_shown}')

    settings_shown=(True,False)[settings_shown]

    if settings_shown:
        show_item('settings_group')
        h=max(viewport_height_min,get_viewport_height()+settings_height)
    else:
        hide_item('settings_group')
        h=max(viewport_height_min,get_viewport_height()-settings_height)

    try:
        if settings_shown:
            values=[ api['name'] for api in apis if api['devices'] ]
            configure_item('api_out',items=values)
            configure_item('api_in',items=values)

            api_out_name=get_value('api_out')
            if api_out_name not in values:
                if values:
                    set_value('api_out',values[0]['name'])

            api_in_name=get_value('api_in')

            if api_in_name not in values:
                if values:
                    set_value('api_in',values[0]['name'])

    except Exception as e:
        l_error(f'settings_wrapper:{e}')

    set_viewport_height(h)
    on_viewport_resize()

status_text=''
def set_status(text,alert=False,timeout=2):
    global status_text,status_timeout
    if text!=status_text:
        set_value('status',text)
        #set_value('help_text',text)
        status_text=text

        if timeout:
            status_timeout=perf_counter()+timeout

        #if alert:
        #    bind_item_theme("status_text", text_alert)
        #else:
        #    bind_item_theme("status_text", text_ok)

info_chars=0

def on_viewport_resize(sender=None, app_data=None):
    vw = get_viewport_client_width()
    vh = get_viewport_client_height()

    global info_chars,settings_height,settings_shown

    info_chars=int(vw/7)

    #30 -magic factor ...
    plot_height  = max(plot_min_height, vh - (settings_height if settings_shown else 0) - status_height - title_hight + 30)

    set_item_height('slider', plot_height-plot_axis_height)
    set_item_pos('slider',[5,title_hight+23])

    set_item_height('plot', plot_height)
    set_item_width('plot', vw-64)

    set_item_pos('info_window',[0,title_hight])
    set_item_pos('debug_text',[85,24+title_hight])
    set_item_pos('help_text',[385,24+title_hight])

    set_item_pos('central_info',[(vw-64-100)/2,(plot_height)/2])

    set_item_width('info_window', vw)
    set_item_height('info_window', vh)

def exit_press(sender=None, app_data=None):
    global exiting
    exiting=True

###################################################
with window(tag='main',no_title_bar=True,no_scrollbar=True,no_resize=True,no_move=True) as main:
    set_primary_window(main, True)

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
            with group(tag='plot_combo',horizontal=True):
                add_spacer(width=6)

                dpg.add_slider_float(tag='slider',callback=slide_change,vertical=True,max_value=30,min_value=100,default_value=100,format="",width=10,track_offset=0.5)
                widget_tooltip('Adjust dynamic range')

                with plot(tag='plot',no_mouse_pos=True,no_menus=True,no_frame=True):
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

                        add_line_series([20], [-120], tag="fft_line_avg")
                        add_line_series([20], [-120], tag="fft_line2")
                        add_line_series([20], [-120], tag="fft_line")

                        #add_line_series([20], [-120], tag="fft_line_fast")
                        #add_line_series([20], [-120], tag="fft_line_slow")

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

                    add_spacer(height=-1)
                    add_image_button(ico["reset"],tag='resetrack',callback=reset_track_press)
                    widget_tooltip(' Reset selected track samples.')

        with table_row():
            with table(header_row=False, resizable=False, policy=mvTable_SizingStretchProp,
                borders_innerH=False, borders_innerV=False, borders_outerH=False, borders_outerV=False,
                row_background=False, context_menu_in_body=False, freeze_rows=0, freeze_columns=0,
                no_host_extendX=False, no_host_extendY=False, pad_outerX=False, no_pad_outerX=True):

                add_table_column(width_fixed=True, init_width_or_weight=6, width=6)
                add_table_column(width_fixed=True, init_width_or_weight=18, width=18)
                add_table_column(width_stretch=True, init_width_or_weight=-1)
                add_table_column(width_fixed=True, init_width_or_weight=255, width=255)

                with table_row():
                    add_spacer(height=6)
                    add_spacer(height=6)

                    add_text(tag='status',default_value='')

                    with group(horizontal=True):
                        add_image_button(ico["play"],tag='sweep',callback=sweep_press)
                        widget_tooltip('Run frequency sweep')
                        add_spacer(width=16)
                        add_image_button(ico["save_pic"],tag='save_image',callback=save_image)
                        widget_tooltip("Save Image file")
                        add_image_button(ico["save_csv"],tag='save_csv_button',callback=save_csv)
                        widget_tooltip("Save CSV file")
                        add_spacer(width=16)
                        add_image_button(ico["home"],tag='homepage',callback=go_to_homepage)
                        widget_tooltip(f'Visit project homepage ({HOMEPAGE})')
                        add_image_button(ico["license"],tag='licensex',callback=license_wrapper)
                        widget_tooltip('Show License')
                        add_image_button(ico["about"],tag='aboutx',callback=about_wrapper)
                        widget_tooltip("Show 'About' Dialog")
                        add_image_button(ico["settings"],tag='settingsx',callback=settings_wrapper)
                        widget_tooltip("Show settings")

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
                                        dpg.add_image(ico["out_off"],tag='out_status',width=16)
                                        widget_tooltip('Output Stream status')
                                        add_text(default_value='Output')

                                with table(tag='in_tab1',header_row=False, resizable=False, policy=mvTable_SizingStretchProp):
                                    add_table_column(width_fixed=True, init_width_or_weight=16, width=16)
                                    add_table_column(width_fixed=True, init_width_or_weight=66)
                                    with table_row():
                                        dpg.add_image(ico["in_off"],tag='in_status')
                                        widget_tooltip('Input Stream status')
                                        add_text(default_value='Input')

                            with table_row():
                                with group(width=-1):
                                    add_text(default_value='API')
                                    add_text(default_value=' ')
                                    add_text(default_value='Device:')
                                    add_text(default_value='channels:')
                                    add_text(default_value='Samplerate:')
                                    add_text(default_value='latency:')
                                    add_text(default_value='blckocksize:')

                                with group(width=-1):

                                    add_combo(tag='api_out',default_value='',callback=api_out_callback,width=c1width)
                                    add_text(default_value=' ')

                                    add_combo(tag='out_dev',default_value='',callback=out_dev_changed)
                                    add_combo(tag='out_channel',default_value='',callback=out_channel_changed,user_data=True)
                                    add_text(tag='out_samplerate')

                                    add_combo(tag='out_latency',label='',callback=out_latency_changed,items=latency_values,default_value=out_latency_default,user_data=True)
                                    add_combo(tag='out_blocksize',label='',callback=out_blocksize_changed,items=out_blocksize_values,default_value=out_blocksize_default,user_data=True)

                                with group(width=-1):

                                    add_combo(tag='api_in',default_value='',callback=api_in_callback,width=c1width)
                                    add_text(default_value=' ')

                                    add_combo(tag='in_dev',default_value='',callback=in_dev_changed,user_data=True)
                                    add_combo(tag='in_channel',default_value='',callback=in_channel_changed,user_data=True)
                                    add_text(tag='in_samplerate')

                                    add_combo(tag='in_latency',label='',callback=in_latency_changed,items=latency_values,default_value=in_latency_default,user_data=True)
                                    add_combo(tag='in_blocksize',label='',callback=in_blocksize_changed,items=in_blocksize_values,default_value=in_blocksize_default,user_data=True)

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
                                add_text(default_value='size'); FFT_size_tooltip='FFT size\nF4 / Shift+F4'; widget_tooltip(FFT_size_tooltip)
                                add_combo(tag='fft_size',items=['64','128','256','512','1024','2048','4096','8192','16384','32768','65536'],default_value=cfg['fft_size'],callback=fft_size_callback,width=c2width); widget_tooltip(FFT_size_tooltip)
                            with table_row():
                                add_text(default_value='window'); FFT_window_tooltip='FFT window\nF3 / Shift+F3' ; widget_tooltip(FFT_window_tooltip)
                                add_combo(tag='fft_window',items=['ones','hanning','hamming','blackman','bartlett'],default_value=cfg['fft_window'],callback=fft_window_changed,width=c2width); widget_tooltip(FFT_window_tooltip)

                            FFT_buckets_tooltip='Frequency bin aggregation\n(equal frequency width "buckets" on log scale)\nF5 / Shift+F5'
                            with table_row():
                                add_checkbox(tag='fft_fba',label='FBA',callback=fft_fba_callback,default_value=cfg['fft_fba']); widget_tooltip(FFT_buckets_tooltip)
                                add_combo(tag='fft_fba_size',items=['64','128','256','512','1024','2048','4096'],default_value=cfg['fft_fba_size'],callback=fft_fba_size_callback,user_data=True,width=c2width); widget_tooltip(FFT_buckets_tooltip)
                            with table_row():
                                add_checkbox(tag='fft_smooth',label='Smth',callback=fft_smooth_callback,default_value=cfg['fft_smooth']); widget_tooltip('Smoothing')
                                dpg.add_slider_int(tag='fft_smooth_factor',callback=fft_smooth_factor_change,max_value=12,min_value=1,default_value=cfg['fft_smooth_factor'],format="%d",width=130,track_offset=0.5)
                            with table_row():
                                add_checkbox(tag='fft_tda',label='TDA',callback=fft_tda_callback,default_value=cfg['fft_tda']); FFT_tda_tooltip='Time domain averaging\nF6 / Shift+F6'; widget_tooltip(FFT_tda_tooltip)

                            with table_row():
                                add_text(default_value='factor'); FFT_tda_tooltip='Time domain averaging\nF6 / Shift+F6'; widget_tooltip(FFT_tda_tooltip)
                                add_combo(tag='fft_tda_factor',items=['0.1','0.2','0.3','0.4','0.5','0.6','0.7','0.8','0.9'],default_value=cfg['fft_tda_factor'],callback=fft_tda_factor_callback,width=c2width); widget_tooltip(FFT_tda_tooltip)

                            with table_row():
                                add_checkbox(tag='peaks',label='Peaks',callback=peaks_callback,default_value=cfg['peaks']); widget_tooltip('Peaks detection')

                            with table_row():
                                add_text(default_value='S.L.F.')
                                dpg.add_slider_float(tag='peaks_dist_factor',callback=peaks_dist_factor_change,max_value=5.0,min_value=1.0,default_value=cfg['peaks_dist_factor'],format="%.1f",width=130,track_offset=0.5); widget_tooltip('Short Length Factor\n... that\'s complicated ...')

                            with table_row():
                                add_text(default_value='Threshold')
                                dpg.add_slider_float(tag='peaks_threshold',callback=peaks_threshold_change,max_value=40.0,min_value=1.0,default_value=cfg['peaks_threshold'],format="%.3f",width=130,track_offset=0.5); widget_tooltip('Peak Detection Threshold.')

                with child_window(border=True,autosize_y=False,autosize_x=False,width=220,no_scrollbar=True,height=settings_height-5):
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
                                add_text(default_value='buckets'); FFT_tooltip5='Recorded Tracks Frequency "buckets"\nF7 / Shift+F7'; widget_tooltip(FFT_tooltip5)
                                add_combo(tag='track_buckets',items=['64','128','256'],default_value=cfg['track_buckets'],callback=tracks_buckets_quant_change,width=c2width); widget_tooltip(FFT_tooltip5)
                            with table_row():
                                add_text(default_value='TDA'); FFT_tooltip6='Time domain averaging\nF8 / Shift+F8'; widget_tooltip(FFT_tooltip6)
                                add_combo(tag='tda_tracks',items=['0.0','0.1','0.2','0.3','0.4','0.5','0.6','0.7','0.8','0.9'],default_value=0.7,callback=tda_tracks_callback,width=c2width); widget_tooltip(FFT_tooltip6)

                with child_window(border=True,autosize_y=False,autosize_x=False,width=140,no_scrollbar=True,height=settings_height-5):
                    with group():
                        add_text(default_value='DISPLAY SETTINGS')
                        dpg.add_separator()
                        add_checkbox(tag='vsync',label='VSync',callback=vsync_callback,default_value=cfg['vsync'])
                        add_checkbox(tag='debug',label='Debug',callback=debug_callback,default_value=cfg['debug'])
                        add_checkbox(tag='help',label='Help',callback=help_callback,default_value=cfg['help'])

                        with group(horizontal=True):
                            add_text(default_value='Theme:')

                            add_image_button(ico["light"],callback=theme_light_callback,width=16); widget_tooltip("Light theme\nkey:L")
                            add_image_button(ico["dark"],callback=theme_dark_callback,width=16); widget_tooltip("Dark theme\nkey:D")
                add_spacer(width=5)

    add_text(tag='debug_text',default_value='')
    add_text(tag='help_text',default_value='')
    add_text(tag='central_info',default_value='')

    with dpg.handler_registry():
        add_mouse_click_handler(callback=click_callback)
        add_mouse_release_handler(callback=release_callback)
        add_mouse_wheel_handler(callback=wheel_callback)
        add_key_press_handler(callback=key_press_callback)

        #dpg.add_mouse_drag_handler(button=0, threshold=0.0, callback=drag_viewport)
        dpg.add_mouse_down_handler(button=0, callback=on_mouse_down)
        dpg.add_mouse_move_handler(callback=on_mouse_move)

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

distro_info+= "\nnumpy       " + str(numpy_version) + "\nsounddevice " + str(sounddevice_version) + "\n\nDearPyGui   " + str(dpg.get_dearpygui_version()) + "\n\n"

print(distro_info)
l_info(distro_info)

def track_file(track,tlen):
    return path_join(INTERNAL_DIR, f'track{track}_{tlen}.json')

sweeping=False

stream_in=None
stream_out=None

fft_duration=0

refresh_devices()

settings_wrapper()

show_viewport()
set_viewport_height(460)

fft_ready=False

fft_buckets_quant_change(None,None,False)
tracks_buckets_quant_change(None,None,True)

api_in_callback()
api_out_callback()
fft_callback()

status_timeout=0

next_fps = 0
status_shown=True
status_hide_time=0

next_gc=0

hide_info()
frames = 0
frames_change = 0

output_callbacks_all = 0
output_samples = 0

configure_app(anti_aliased_lines=True,anti_aliased_lines_use_tex=True,anti_aliased_fill=True)
help_callback()


#gc_disable()
gc_collect()
gc_freeze()

def main_loop():
    peaks_annos=set()
    peaks_annos_clear = peaks_annos.clear

    CENTRAL_INFO_SHOWN=False

    global sweeping,output_callbacks_all,output_callbacks_count,output_samples,samples_chunks_requested_new,set_viewport_pos_scheduled,set_viewport_size_scheduled,schedule_screenshot,status_timeout,fft_window_sum
    global redraw_track_line,frames_change,frames,next_fps,track_line_data_y_recorded,sweeping_i,logf_sweep_step,is_dragging,is_resizing,samples_chunks_fifo

    next_sweep_time=0
    input_callbacks_all=0
    rec_samples=0

    data=zeros(FFT_SIZE_MAX)
    new_data=False

    while is_dearpygui_running():
        real_update=False

        if sweeping:
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
        if DEBUG and not (is_dragging or is_resizing):
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
            except:
                break

        if new_data and not (is_dragging or is_resizing):
            new_data=False

            real_update=True

            #from numpy.random import randn
            #data = randn(cfg['fft_size'])

            data_slice=data[-FFT_SIZE:]

            current_sample_db = 10 * log10( np_mean(np_square(data_slice)) + 1e-12)

            if not PEAKS:
                for fint in peaks_annos:
                    delete_item(f'peak{fint}')
                peaks_annos_clear()

            if FFT and fft_ready:
                try:
                    fft_values_y=20*np_log10( np_abs( np_fft_rfft(data_slice*fft_window)) / FFT_SIZE + 1e-12 )
                    #print('i1:',len(fft_values_y))

                    if FFT_FBA:
                        fft_values_means_in_buckets = bincount(fft_bin_indices, weights=fft_values_y)[1:] / fft_bin_counts[1:]
                        fft_values_y=np_array([fft_values_means_in_buckets[i] for i in fft_bin_indices_selected[:-1]])
                        fft_values_x = fft_values_x_bins

                        initlen=len(fft_values_y)
                        if FFT_SMOOTH:
                            for i_smooth in range(FFT_SMOOTH_FACTOR):
                                csum = np_cumsum(np_pad(fft_values_y,2,'reflect'))
                                #print('slooop:',i_smooth,len(csum))
                                fft_values_y = (csum[4:] - csum[:-4])/4

                        initlen2=len(fft_values_y)
                        #print('i2:',initlen,initlen2)
                    else:
                        fft_values_x = fft_values_x_all

                    if FFT_TDA:
                        try:
                            fft_values_y=FFT_TDA_FACTOR_1m*np_array(fft_values_y) + FFT_TDA_FACTOR*np_array(fft_values_y_prev)
                        except:
                            pass

                    if PEAKS:
                        points=len(fft_values_y)

                        dist_half=int(PEAKS_DIST_FACTOR*points/64)
                        dist=dist_half*2
                        #int(PEAKS_DIST_FACTOR*points/32)
                        #dist_half=dist//2

                        padded=np_pad(fft_values_y,dist_half,'reflect')
                        csum = np_cumsum(padded)
                        window_sum = csum[dist:] - csum[:-dist]
                        fft_values_y_avg_fast = window_sum / dist

                        dist_half=points//16
                        dist=dist_half*2
                        #points//8
                        #dist_half=dist//2

                        padded=np_pad(fft_values_y_avg_fast,dist_half,'reflect')
                        csum = np_cumsum(padded)
                        window_sum = csum[dist:] - csum[:-dist]
                        fft_values_y_avg_slow = window_sum / dist

                        #print('ip3:',len(fft_values_x),len(fft_values_y),len(fft_values_y_avg_fast),len(fft_values_y_avg_slow))

                        #set_value("fft_line_fast", [fft_values_x, fft_values_y_avg_fast])
                        #set_value("fft_line_slow", [fft_values_x, fft_values_y_avg_slow])

                        area_len_threshold=PEAKS_DIST_FACTOR*points/64

                        peaks_annos_new=set()
                        peaks_annos_new_add=peaks_annos_new.add
                        area_len=0
                        #area_start=0
                        #area_end=0

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
                                        #area_end=i
                                        #area_start=i-area_len
                                        ratio=max_val-min_val
                                        if ratio>PEAKS_THRESHOLD:
                                            peaks_annos_new_add((ratio,int(max_val_f),max_val))
                                            #print('found;',area_start,'\t',area_end,'\t',area_end-area_start,'\t',int(max_val_f),'\t',max_val,'\t',ratio)

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

                    set_value("fft_line2", [fft_values_x, fft_values_y])
                    set_value("fft_line", [fft_values_x, fft_values_y])

                    if FFT_TDA:
                        fft_values_y_prev=fft_values_y

                except Exception as exception_fft:
                    l_error(f'FFT Exception:{exception_fft}')
                    print('FFT Exception:',exception_fft)

            if playing_state==2 and track_line_data_y_recorded and current_bucket<TRACK_BUCKETS:
                #track_line_data_y_recorded[current_bucket]=track_line_data_y_recorded[current_bucket]*tda_tracks + current_sample_db*tda_tracks_1m

                track_line_data_y_recorded[current_bucket]*=tda_tracks
                track_line_data_y_recorded[current_bucket]+=current_sample_db*tda_tracks_1m
                redraw_track_line=True

            set_value('cursor_db_txt', (25000, current_sample_db))
            configure_item('cursor_db_txt',label=f'{round(current_sample_db)}dB')

            if current_sample_db<-110:
                set_status('No signal / Mic not connected ...',1)
                CENTRAL_INFO_SHOWN=True
                set_value('central_info',""
                            "     No signal !    \n"
                            "(Mic not connected ?)")
                #set_value('help_text','')
                help_off()
            elif status_timeout!=0:
                if perf_counter()>status_timeout:
                    #set_value('help_text','')
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

        if set_viewport_pos_scheduled:
            set_viewport_pos(set_viewport_pos_scheduled)
            cfg['viewport_pos']=set_viewport_pos_scheduled
            set_viewport_pos_scheduled=False
            real_update=True
        elif set_viewport_size_scheduled:
            set_viewport_width(set_viewport_size_scheduled[0])
            set_viewport_height(set_viewport_size_scheduled[1])
            cfg['viewport_size']=set_viewport_size_scheduled
            set_viewport_size_scheduled=None
            real_update=True

        if schedule_screenshot:
            hide_item('cursor_db_txt')
            hide_item('cursor_f_txt')
            hide_item('cursor_f')

            render_dearpygui_frame()

            if os.path.isfile(filename_full_screenshot):
                x, y = dpg.get_item_rect_min("plot")
                w, h = dpg.get_item_rect_size("plot")

                timestamp=strftime('%Y_%m_%d-%H_%M_%S',localtime_catched(time()) )
                filename_cut=path_join(INTERNAL_DIR_IMAGES, f'sas-{timestamp}.png')

                set_status(f'saving {filename_cut} ...')

                try:
                    Image.open(filename_full_screenshot).crop((x, y, x+w, y+h)).save(filename_cut)
                except Exception as exception_img:
                    l_error(f'exception_img:{exception_img}')
                    print(f'exception_img:{exception_img}')
                else:
                    schedule_screenshot=False

                    show_item('cursor_db_txt')
                    show_item('cursor_f_txt')
                    show_item('cursor_f')

        render_dearpygui_frame()

        ##################################
        #if not real_update:
        #    if now>next_gc:
        #        gc_collect(0)
        #        next_gc=now+1

        if DEBUG and not (is_dragging or is_resizing):
            if real_update:
                frames_change+=1
            frames += 1

            now = perf_counter()
            if now >= next_fps :
                set_value('debug_text',
                    f"FPS:{frames}/{frames_change} VSync:{VSYNC_STATE_NAME}\n\n"
                    f"OUT samplerate : {output_samples}/s ({output_callbacks_all}/s)\n"
                    f"IN samplerate: {rec_samples}/s ({input_callbacks_all})/s\n\n"
                    f"FFT Window: {round(fft_duration,3)}s\n"
                    f"FFT  / FBA  / act:\n"
                    f"{FFT_POINTS} / {FFT_FBA_SIZE} / {FFT_ACTUAL_BUCKETS}\n"
                    f"FBA: {FFT_FBA}\n"
                    f"FBA_SIZE: {FFT_FBA_SIZE}\n"
                    f"TDA: {FFT_TDA}\n"
                    f"TDA_FACTOR: {FFT_TDA_FACTOR}")
                frames = 0
                frames_change = 0
                input_callbacks_all = 0
                rec_samples = 0

                output_callbacks_all = 0
                output_samples = 0

                next_fps = now+1.0

        ##################################

        if exiting:
            break

main_loop()

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
    f.write(dumps(cfg))

for track in range(tracks):
    with open(track_file(track,TRACK_BUCKETS), "w", encoding="utf-8") as f:
        f.write(dumps(track_line_data_y[track]))

destroy_context()
l_info('Exiting.')
sys_exit(0)
