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

from dearpygui.dearpygui import create_context,file_dialog,add_file_extension,get_plot_mouse_pos,set_value,get_value,bind_item_theme,item_handler_registry,plot,add_line_series,add_scatter_series,theme,configure_item,render_dearpygui_frame,is_dearpygui_running,destroy_context,theme_component,add_item_clicked_handler,add_item_deactivated_handler,add_item_hover_handler,bind_item_handler_registry,add_mouse_release_handler,add_mouse_wheel_handler,handler_registry,add_combo,child_window,table_row,add_checkbox,add_button,add_text,add_table_column,window,table,is_item_hovered,tooltip,add_image_button,add_static_texture,texture_registry,output_frame_buffer
from dearpygui.dearpygui import create_viewport,get_viewport_client_width,get_viewport_client_height,set_viewport_vsync,set_viewport_height,hide_item,show_item,set_item_height,set_item_width,get_viewport_height,show_viewport,set_item_pos,set_primary_window

from time import sleep,strftime,time,localtime,perf_counter

from numpy import mean as np_mean,square as np_square,float32,ones,hanning,hamming,blackman,bartlett, abs as np_abs,fft as np_fft,log10 as np_log10,__version__ as numpy_version, concatenate as np_concatenate,sum as np_sum, arange, sin as np_sin,zeros, append as np_append,digitize,bincount,array
from sounddevice import Stream,InputStream,OutputStream,query_devices,default as sd_default,query_hostapis,__version__ as sounddevice_version

from collections import deque
from queue import Queue

from math import pi, log10, ceil, floor
from PIL import Image

from pathlib import Path

import os
from os import name as os_name, system, sep
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
Path(INTERNAL_DIR).mkdir(parents=True,exist_ok=True)

print(f'{INTERNAL_DIR=}')

def localtime_catched(t):
    try:
        #mtime sometimes happens to be negative (Virtual box ?)
        return localtime(t)
    except:
        return localtime(0)

log_file = path_join(INTERNAL_DIR, strftime('%Y_%m_%d-%H_%M_%S',localtime_catched(time()) ) +'.txt')
ini_file = path_join(INTERNAL_DIR, 'gui.ini')

print(f'{log_file=}')
print(f'{ini_file=}')

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

fft_size = 8
fft_points = 4

f_current=0
tracks=8
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
    global show_track
    res_list = []
    res_list_append = res_list.append
    if current_bucket<spectrum_buckets_quant:
        for track,show in enumerate(show_track):
            if show:
                db_temp = round(track_line_data_y[track][current_bucket])
                res_list_append(str(track+1) + ':' + str(db_temp))
    else:
        print(f'{current_bucket=}')

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

def save_fft_points():
    file = path_join(INTERNAL_DIR, f'fft-{fft_size}-{fft_points}.csv')
    #set_status(f'saving {file} ...')
    print(file)

    global bucket_freqs

    try:
        with open(file,'w',encoding='utf-8') as fh:
            fh.write(f"#fft_size:{fft_size},fft_points:{fft_points}\n")
            fh.write("#index,frequency[Hz]\n")
            for i,f in enumerate(fft_line_data_x):
                fh.write(f'{i},{f}\n')
    except Exception as e:
        print(f'buckets-save_csv_error:{e}')
        #l_error()

def save_buckets():
    file = path_join(INTERNAL_DIR, f'buckets-{spectrum_buckets_quant}.csv')
    #set_status(f'saving {file} ...')
    print(file)

    global bucket_freqs

    try:
        with open(file,'w',encoding='utf-8') as fh:
            fh.write(f"#buckets:{spectrum_buckets_quant}\n")
            fh.write("#index,frequency[Hz]\n")
            for b in range(spectrum_buckets_quant):
                f=bucket_freqs[b]
                fh.write(f'{b},{f}\n')
    except Exception as e:
        print(f'buckets-save_csv_error:{e}')
        #l_error()

def save_buckets_edges():
    global bucket_edges
    file = path_join(INTERNAL_DIR, f'buckets-edges-{len(bucket_edges)}.csv')
    #set_status(f'saving {file} ...')
    print(file)


    try:
        with open(file,'w',encoding='utf-8') as fh:
            fh.write(f"#buckets-edges:{len(bucket_edges)}\n")
            fh.write("#index,frequency[Hz]\n")
            for i,f in enumerate(bucket_edges):
                fh.write(f'{i},{f}\n')
    except Exception as e:
        print(f'buckets-edges-save_csv_error:{e}')
        #l_error()

def save_bin_indices():
    global bin_indices
    file = path_join(INTERNAL_DIR, f'bin_indices-{len(bin_indices)}.csv')
    #set_status(f'saving {file} ...')
    print(file)

    try:
        with open(file,'w',encoding='utf-8') as fh:
            fh.write(f"#bin_indices:{len(bin_indices)}\n")
            fh.write("#index,index[Hz]\n")
            for i,j in enumerate(bin_indices):
                fh.write(f'{i},{j}\n')
    except Exception as e:
        print(f'bin_indices-save_csv_error:{e}')
        #l_error()

def save_bin_counts():
    global bin_counts
    file = path_join(INTERNAL_DIR, f'bin_counts-{len(bin_counts)}.csv')
    #set_status(f'saving {file} ...')
    print(file)

    try:
        with open(file,'w',encoding='utf-8') as fh:
            fh.write(f"#bin_counts:{len(bin_counts)}\n")
            fh.write("#index,index[Hz]\n")
            for i,j in enumerate(bin_counts):
                fh.write(f'{i},{j}\n')
    except Exception as e:
        print(f'bin_counts-save_csv_error:{e}')
        #l_error()

def save_csv():
    filename='sas.csv'
    set_status(f'saving {filename} ...')

    try:
        with open(filename,'w',encoding='utf-8') as f:
            f.write("# Created with " + title + " #\n")
            f.write("frequency[Hz],level[dBFS]\n")
            for i in range(spectrum_buckets_quant):
                values=[]
                for track,show in enumerate(show_track):
                    if show:
                        db=track_line_data_y[track][i]
                        logf=bucket_to_logf(i)
                        values.append(f"{round(100*(10**logf))/100},{round(1000*db)/1000}")
                f.write(','.join(values) + '\n')
    except Exception as e:
        l_error(f'save_csv_error:{e}')

def load_csv_file_selected(sender, app_data):
    filename=app_data["file_path_name"]

    if filename:
        try:
            with open(filename,'r',encoding='utf-8') as f:
                for line in f:
                    line=line.strip()
                    if line:
                        if line[0]=='#':
                            print("ignoring line:",line)
                            continue
                        try:
                            freq,db = line.split(',')
                            float_freq,float_db=float(freq),float(db)
                        except Exception as el:
                            print("ignoring line:",line)
                            continue

                        if fmin_audio<=float_freq<=fmax_audio:
                            logf=log10(float_freq)
                            bucket = logf_to_bucket(logf)
                        else:
                            print("wrong frequency:",float_freq)
                            continue

                        if dbmin<=float_db<=dbmax:
                            track_line_data_y[recorded_track][bucket]=float_db
                        else:
                            print("wrong db value:",float_db)
                            continue

        except Exception as e:
            l_error(f'Load_csv_error:{e}')

        global redraw_tracks_lines
        redraw_tracks_lines=True

def load_csv():
    show_item("file_dialog_load")

def save_image():
    filename_full = path_join(INTERNAL_DIR, 'sas.png')

    set_status(f'saving {filename_full} ...')
    dpg.output_frame_buffer(filename_full)

    x, y = dpg.get_item_rect_min("plot")
    w, h = dpg.get_item_rect_size("plot")

    img = Image.open(filename_full)

    cropped_img = img.crop((x, y, x+w, y+h))

    timestamp=strftime('%Y_%m_%d-%H_%M_%S',localtime_catched(time()) )
    filename_cut=path_join(INTERNAL_DIR, f'sas-{timestamp}.png')

    set_status(f'saving {filename_cut} ...')
    cropped_img.save(filename_cut)

scale_factor_logf_to_bucket=1

def logf_to_bucket(logf):
    return int(floor(scale_factor_logf_to_bucket * (logf - logf_min_audio)))

def bucket_to_logf(i):
    return (i+0.5)/scale_factor_logf_to_bucket + logf_min_audio

phase_step=1.0

def change_f(fpar):
    global current_logf,current_bucket,phase_step,current_bucket,two_pi_by_in_samplerate

    if fmin_audio<fpar<fmax_audio:
        current_logf=log10(fpar)
        current_f=fpar
        current_bucket=logf_to_bucket(current_logf)

        set_value("cursor_f", ((fpar,fpar), (0,dbmin)))
        set_value('cursor_f_txt', (fpar, -3))
        configure_item('cursor_f_txt',label=f'{round(fpar)}Hz')

        phase_step = two_pi_by_in_samplerate * fpar

played_bucket=0
played_bucket_callbacks=0

audio_output_callback_outside=0
audio_output_callback_inside=0
audio_output_callback_prev=perf_counter()

def audio_output_callback(outdata, frames, time, status):
    global phase,playing_state,played_bucket,played_bucket_callbacks,phase_step,two_pi,current_bucket,out_channel_buffer_mod_index,phase_i,audio_output_callback_prev,audio_output_callback_inside,audio_output_callback_outside
    audio_output_callback_start=perf_counter()
    audio_output_callback_outside += audio_output_callback_start-audio_output_callback_prev

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

    audio_output_callback_end=perf_counter()
    audio_output_callback_inside += audio_output_callback_end-audio_output_callback_start
    audio_output_callback_prev=audio_output_callback_end

def wasapi_exclusive_callback(sender=None, app_data=None):
    l_info(f'wasapi_exclusive_callback:{sender},{app_data}')

    out_stream_init()

def vsync_callback(sender=None, app_data=None):
    l_info(f'vsync_callback:{sender},{app_data}')
    set_viewport_vsync(app_data)

def sweep_abort():
    global sweeping
    sweeping=False
    configure_item('sweep',texture_tag=ico["play"])

def rec_press(sender=None, app_data=None):
    l_info(f'rec_press:{sender},{app_data}')

sweeping_i=0
def sweep_press(sender=None, app_data=None):
    l_info(f'sweep_press:{sender},{app_data}')

    global sweeping,lock_frequency,sweeping_i
    sweeping=(True,False)[sweeping]

    if recorded_track is None:
        l_info('no recorded_track')
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
    global playing_state
    bind_item_theme("cursor_f",red_line_theme)
    playing_state=1
    redraw_tracks_lines=True

    if recorded_track:
        bind_item_theme(f"track{recorded_track}",red_line_theme)

@catch
def play_stop():
    global playing_state,lock_frequency
    if playing_state==2:
        playing_state=-1
    lock_frequency=False

    bind_item_theme("cursor_f",green_line_theme)
    #playing_state=0

    if recorded_track:
        bind_item_theme(f"track{recorded_track}",reddark_line_theme)

    sweep_abort()

    redraw_tracks_lines=False

exiting=False

current_sample_db=-120

samples_chunks_fifo_chunks_new=0
samples_chunks_fifo_new=0
samples_chunks_fifo=deque(maxlen=32)
samples_chunks_fifo_put=samples_chunks_fifo.append

###########################################################

audio_input_callback_outside=0
audio_input_callback_inside=0
audio_input_callback_prev=perf_counter()

def audio_input_callback(indata, frames, time_info, status):
    global samples_chunks_fifo_new,samples_chunks_fifo_chunks_new,audio_input_callback_prev,audio_input_callback_inside,audio_input_callback_outside
    audio_input_callback_start=perf_counter()
    audio_input_callback_outside += audio_input_callback_start-audio_input_callback_prev

    new_samples=len(indata[:, 0])
    samples_chunks_fifo_put(indata[:, 0].copy())

    samples_chunks_fifo_new+=new_samples
    samples_chunks_fifo_chunks_new+=1

    audio_input_callback_end=perf_counter()
    audio_input_callback_inside += audio_input_callback_end-audio_input_callback_start
    audio_input_callback_prev=audio_input_callback_end

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
        set_value('api',apis[default_api_nr]['name'])
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
in_blocksize_default=512
in_latency_default='low'

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

    global record_blocks_len,record_blocks_len_part1,record_blocks_len_part2,time_to_collect_sample

    in_blocksize=int(get_value('in_blocksize'))

    if in_blocksize:
        record_blocks_len=int((in_samplerate*time_to_collect_sample)/in_blocksize)
        record_blocks_len_part1=int(record_blocks_len/2)
        record_blocks_len_part2=record_blocks_len-record_blocks_len_part1
    else:
        #TODO
        record_blocks_len=128
        record_blocks_len_part1=64
        record_blocks_len_part2=64

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

    if get_value('exclusive'):
        extra_settings=WasapiSettings(exclusive=True)
    else:
        extra_settings=None

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
            channels=channels
        )
        #dtype="float32",
        stream_out.start()
    except Exception as e:
        l_error(f'OutputStream init error:{e}')
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
    global stream_in,device_in_current,device_in_channels_stream_option,in_channel_buffer_mod_index

    device=int(device_in_current['index'])
    samplerate=float(get_value('in_samplerate'))
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
            channels=channels
        )
        #channels=device_in_channels_stream_option
        # dtype="float32"
        stream_in.start()

    except Exception as e:
        l_error(f'InputStream init error:{e}')
    else:
        l_info('InputStream init DONE.')

def hide_info():
    hide_item('info_window')
    set_value('info_text','')
    on_viewport_resize()

def show_info(message):
    on_viewport_resize()
    set_value('info_text',normalize_text(message,info_chars))
    show_item('info_window')

@catch
def about_wrapper():
    text1= f'Simple Audio Sweeper {VER_TIMESTAMP}\nAuthor: Piotr Jochymek\n\n{HOMEPAGE}\n\nPJ.soft.dev.x@gmail.com\n'
    text2='\n' + distro_info + '\n'
    show_info('\n' + text1+text2)

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
        print(exception_lic)
        try:
            license_txt=Path(path_join(dirname(EXECUTABLE_DIR),'LICENSE')).read_text(encoding='ASCII')
        except Exception as exception_2:
            print(exception_2)
            sys_exit(1)

    show_info('\n'+ license_txt)

fft_on=True

def resetrack_press(sender=None, app_data=None):
    print('resetrack:',sender,app_data)

    global recorded_track,redraw_tracks_lines
    if recorded_track!='none':
        sweep_abort()
        track_line_data_y[recorded_track]=[dbinit]*spectrum_buckets_quant
        redraw_tracks_lines=True
    else:
        print('recording not enabled for track',track)

recorded_track=None

def configure_track_button(track):
    if show_track[track]:
        configure_item(f'showcheck{track}',texture_tag=ico[f"{track+1}_on"])
    else:
        configure_item(f'showcheck{track}',texture_tag=ico[f"{track+1}_off"])

show_track=[False]*tracks
def show_press(sender=None,app_data=None,track_combo=None):
    l_info(f'show_press:{sender},{app_data},{track_combo}')
    track,press=track_combo

    track_pressed(track)

    global show_track,redraw_tracks_lines,ico,recorded_track
    if press:
        show_track[track]=(True,False)[show_track[track]]

    configure_track_button(track)

    if not show_track[track]:
        if recorded_track==track:
            recorded_track=None
            set_value('rec_track','none')

def track_pressed(track):
    global redraw_tracks_lines,lock_frequency

    lock_frequency=False
    sweep_abort()
    play_stop()
    status_set_frequency()
    redraw_tracks_lines=True

try:
    VER_TIMESTAMP=Path(path_join(dirname(__file__),VERSION_FILE)).read_text(encoding='ASCII').strip()
except Exception as e_ver:
    print(e_ver)
    VER_TIMESTAMP=''

#TODO
in_samplerate = 44100
two_pi = pi+pi

phase = 0.0

fmin,fini,fmax=10,442,30000
fmin_audio,fmax_audio=20,20000

logf_min,logf_ini,logf_max=log10(fmin),log10(fini),log10(fmax)
logf_min_audio,logf_max_audio=log10(fmin_audio),log10(fmax_audio)

current_f=fini
current_logf=logf_ini

spectrum_buckets_quant=16

current_bucket=logf_to_bucket(current_logf)

dbmin=-122.0
dbmin_display=-123.0
dbinit=dbmin
dbmax_display=dbmax=0.0

dbrange=dbmax-dbmin

dbrange_display=dbmax_display-dbmin_display

redraw_tracks_lines=True

title=f"Simple Audio Sweeper {VER_TIMESTAMP}"

create_context()

ico = {}
for name, data in image.items():
    img = Image.open(BytesIO(data)).convert("RGBA")
    w, h = img.size
    with texture_registry():
        add_static_texture(w, h, [v/255 for px in list(img.get_flattened_data()) for v in px], tag=name)
    ico[name] = name

with file_dialog(directory_selector=False,show=False,callback=load_csv_file_selected,id="file_dialog_load",file_count=1,default_filename="sas"):
    add_file_extension(".csv", color=(255, 255, 0))
    add_file_extension(".*")

current_api=None

@catch
def api_changed(sender=None, app_data=None):
    global current_api,apis,devices,in_dev_cb

    apiname=get_value('api')
    l_info(f'api_changed:{sender},{app_data},{apiname}')

    current_api=[api for api in apis if api['name']==apiname][0]

    out_values=[ dev['name'] for dev in devices if dev['max_output_channels'] > 0 and dev['index'] in current_api['devices'] ]
    in_values=[ dev['name'] for dev in devices if dev['max_input_channels'] > 0 and dev['index'] in current_api['devices'] ]

    out_dev_name=get_value("out_dev")
    in_dev_name=get_value("in_dev")

    configure_item("out_dev",items=out_values)
    configure_item("in_dev",items=in_values)

    device_default_input_name=device_default_input['name']
    device_default_output_name=device_default_output['name']

    l_info(f'defaults:{device_default_input_name},{device_default_output_name}')

    if out_values:
        if out_dev_name not in out_values:
            if device_default_output_name in out_values:
                set_value("out_dev",device_default_output_name)
            else:
                set_value("out_dev",out_values[0])

    out_dev_changed(None,None,True)

    if in_values:
        if in_dev_name not in in_values:
            if device_default_input_name in in_values:
                set_value("in_dev",device_default_input_name)
            else:
                set_value("in_dev",in_values[0])

    in_dev_changed(None,None,True)

@catch
def record_track_changed(sender=None, app_data=None):
    track_to_record=get_value('rec_track')

    sweep_abort()

    global recorded_track

    if track_to_record=='none':
        recorded_track=None
        bind_item_theme(f"track{recorded_track}",gray_line_theme)
    else:
        if track_to_record=='1':
            recorded_track=0
        elif track_to_record=='2':
            recorded_track=1
        elif track_to_record=='3':
            recorded_track=2
        elif track_to_record=='4':
            recorded_track=3
        elif track_to_record=='5':
            recorded_track=4
        elif track_to_record=='6':
            recorded_track=5
        elif track_to_record=='7':
            recorded_track=6
        elif track_to_record=='8':
            recorded_track=7
        else:
            l_error(f'unknown track:{track_to_record}')

        show_track[recorded_track]=True

        show_press(sender,True,(recorded_track,False))

        bind_item_theme(f"track{recorded_track}",reddark_line_theme)

prev_fft='blackman'
def fft_toggle():
    global prev_fft
    fft_window_name=get_value('fft_window')

    if fft_window_name=='none':
        set_value('fft_window', prev_fft)
        configure_item("fft_line", show=True)
    else:
        set_value('fft_window', 'none')
        configure_item("fft_line", show=False)
        prev_fft=fft_window_name

def fft_change(sender=None, app_data=None):
    print(f'fft_change:{sender},{app_data}')
    global fft_size,fft_points,in_samplerate,fft_line_data_x,fft_line_data_y,fft_line_data_x_border_index

    fft_size=int(get_value('fft_size'))
    fft_points=int(fft_size/2+1)

    fft_window_changed()

def fft_window_changed(sender=None, app_data=None):
    fft_window_name=get_value('fft_window')

    global fft_on,fft_window,window_correction
    if fft_window_name=='off':
        fft_on=False
    else:
        fft_on=True
        if fft_window_name=='ones':
            fft_window=ones(fft_size)
        elif fft_window_name=='hanning':
            fft_window=hanning(fft_size)
        elif fft_window_name=='hamming':
            fft_window=hamming(fft_size)
        elif fft_window_name=='blackman':
            fft_window=blackman(fft_size)
        elif fft_window_name=='bartlett':
            fft_window=bartlett(fft_size)
        else:
            l_error(f'unknown window:{fft_window_name}')

    window_correction = np_sum(fft_window)
    configure_item("fft_line", show=fft_on)

    l_info(f'fft_window_changed:{sender},{app_data},{fft_window_name},{len(fft_window)}')

    common_precalc()
    #fft_window = eval(f'{fft_window_name}({fft_size})')()

bucket_freqs=[0]
bucket_edges=[0]

fft_line_data_x_border_index=0
bucket_freqs_border_index=0
track_line_data_y={}

time_to_collect_sample=0.125 #[s]
#1/4s
spectrum_sub_bucket_samples=4
sweeping_delay=time_to_collect_sample*1.5/spectrum_sub_bucket_samples
l_info(f'{sweeping_delay=}')

logf_max_audio_m_logf_min_audio = logf_max_audio-logf_min_audio

postprocessing=False
def postprocessing_callback(sender=None, app_data=None):
    global postprocessing
    print(f'postprocessing_callback:{sender},{app_data}')
    postprocessing=get_value('postprocessing')
    common_precalc()

def buckets_quant_change(sender=None, app_data=None):
    print(f'buckets_quant_change:{sender},{app_data}')

    global spectrum_buckets_quant,sweep_steps,scale_factor_logf_to_bucket,logf_sweep_step,log_bucket_width,log_bucket_width_by2,redraw_tracks_lines

    spectrum_buckets_quant=int(get_value('buckets'))
    sweep_steps=spectrum_buckets_quant*spectrum_sub_bucket_samples
    logf_sweep_step=logf_max_audio_m_logf_min_audio/sweep_steps

    scale_factor_logf_to_bucket=spectrum_buckets_quant/logf_max_audio_m_logf_min_audio
    log_bucket_width=logf_max_audio_m_logf_min_audio/spectrum_buckets_quant
    log_bucket_width_by2=log_bucket_width*0.5

    common_precalc()

    redraw_tracks_lines=True

def common_precalc():
    global two_pi_by_in_samplerate,in_samplerate_by_fft_size,fft_size
    global sweep_steps,fft_line_data_x_border_index,spectrum_buckets_quant,track_line_data_y,time_to_collect_sample,log_bucket_width,log_bucket_width_by2,bucket_freqs_border_index

    in_samplerate_by_fft_size = in_samplerate / fft_size

    global bucket_freqs,fft_line_data_x,fft_line_data_y,bucket_edges,bin_indices,bin_counts

    fft_line_data_x=[0]*fft_points
    fft_line_data_y=[-110]*fft_points

    for i_fft in range(fft_points):
        fft_line_data_x[i_fft]=i_fft * in_samplerate_by_fft_size

    bin_indices = digitize(fft_line_data_x, bucket_edges)
    l_info(f'bin_indices={len(bin_indices)}')
    bin_counts = bincount(bin_indices)
    l_info(f'bin_counts={len(bin_counts)}')

    bucket_freqs=[0]*spectrum_buckets_quant
    bucket_edges=[0]*(spectrum_buckets_quant+1)

    for b in range(spectrum_buckets_quant):
        bucket_freqs[b]= 10**(logf_min_audio + log_bucket_width_by2 + log_bucket_width * b)
        bucket_edges[b+1]= 10**(logf_min_audio + log_bucket_width * (b+1))

    save_buckets()
    save_buckets_edges()
    save_fft_points()
    save_bin_indices()
    save_bin_counts()

    border=0
    border_f=1

    prev_ind=-1
    for f,ind in zip(fft_line_data_x,bin_indices):
        if prev_ind!=ind:
            prev_ind=ind
        else:
            border=int(ind)
            border_f=f
            break

    l_info('')
    l_info(f'{border=}')
    l_info(f'{border_f=}')

    for i,f in enumerate(fft_line_data_x):
        if f<border_f:
            continue
        else:
            fft_line_data_x_border_index=i
            break

    for i,f in enumerate(bucket_freqs):
        if f>=border_f:
            bucket_freqs_border_index=i
            break

    l_info(f'{fft_line_data_x_border_index=} / {len(fft_line_data_x)}')
    l_info(f'{bucket_freqs_border_index=} / {len(bucket_freqs)}')

    for track in range(tracks):
        track_line_data_y[track]=[dbmin]*spectrum_buckets_quant

    global fft_line_new_x
    if postprocessing:
        #fft_line_new_x=tuple(fft_line_data_x[1:fft_line_data_x_border_index] + bucket_freqs[bucket_freqs_border_index:])
        fft_line_new_x=fft_line_data_x[:fft_line_data_x_border_index] + bucket_freqs[bucket_freqs_border_index:]
        fft_line_new_x[0]=5
        fft_line_new_x=fft_line_new_x
    else:
        fft_line_new_x=fft_line_data_x

device_out_current=None

def out_dev_changed(sender=None, app_data=None,user_data=False):
    l_info(f'out_dev_changed:{sender},{app_data},{user_data}')

    global device_out_current

    out_dev_name=get_value("out_dev")

    device_out_current=[device for device in devices if device['name']==out_dev_name][0]

    output_channels=[str(val) for val in range(1,device_out_current['max_output_channels']+1)]
    l_info(f'{output_channels=}')

    configure_item("out_channel",items=output_channels)

    out_channel_value=get_value("out_channel")

    if not out_channel_value or out_channel_value not in output_channels:
        out_channel_value=2
        set_value("out_channel",out_channel_value)

    set_value("out_samplerate",device_out_current['default_samplerate'])

    out_channel_changed(None,out_channel_value)
    out_latency_changed(None,out_latency_default)
    out_blocksize_changed(None,out_blocksize_default)

    if user_data:
        out_stream_init()

device_in_current=None

def in_dev_changed(sender=None, app_data=None,user_data=False):
    l_info(f'in_dev_changed:{sender},{app_data},{user_data}')

    global device_in_current

    dev_name=get_value("in_dev")

    device_in_current=[device for device in devices if device['name']==dev_name][0]

    input_channels=[str(val) for val in range(1,device_in_current['max_input_channels']+1)]
    l_info(f'{input_channels=}')

    configure_item("in_channel",items=input_channels)

    in_channel_value=get_value("in_channel")

    if not in_channel_value or in_channel_value not in input_channels:
        in_channel_value=1
        set_value("in_channel",in_channel_value)

    global in_samplerate,two_pi_by_in_samplerate
    in_samplerate=int(device_in_current['default_samplerate'])
    set_value("in_samplerate",str(in_samplerate))

    two_pi_by_in_samplerate = two_pi/in_samplerate

    in_channel_changed(None,in_channel_value)
    in_latency_changed(None,in_latency_default)
    in_blocksize_changed(None,in_blocksize_default)

    common_precalc()

    if user_data:
        in_stream_init()

def on_click(sender, app_data):
    hide_info()

def on_click_plot(sender, app_data):
    #print('on_click',sender, app_data)

    button_nr=app_data[0]

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

def on_release(sender, app_data):
    #print('on_release',sender, app_data)
    button_nr=app_data

    global sweeping,lock_frequency

    if button_nr==0:
        lock_frequency=False

        if not sweeping:
            play_stop()
            status_set_frequency()

    elif button_nr==1:

        sweep_abort()
    else:
        l_info(f'another button:{button_nr}')

prev_mouse_x=0
def on_mouse_move(sender, app_data):

    if not is_item_hovered("plot"):
        return

    plot_x, _ = get_plot_mouse_pos()

    if plot_x is not None:
        x = int(plot_x)
        global prev_mouse_x,f_current

        if x != prev_mouse_x:
            prev_mouse_x = x

            if not sweeping and not lock_frequency:
                f_current=x
                status_set_frequency()
                change_f(f_current)

import dearpygui.dearpygui as dpg

dpg.create_context()

is_dragging = False
is_resizing = False

def mouse_down(sender, app_data):
    global is_dragging, is_resizing, offset_x, offset_y, curr_vp_x, curr_vp_y
    if not is_dragging:
        offset_x, offset_y = dpg.get_mouse_pos()

        vh = dpg.get_viewport_height()
        vw = dpg.get_viewport_width()

        curr_vp_x, curr_vp_y = dpg.get_viewport_pos()

        if offset_y<20:
            is_dragging = True
        elif offset_x>vw-30 and offset_y>vh-30:
            is_resizing = True

def mouse_release(sender, app_data):
    global is_dragging,is_resizing
    is_dragging = False
    is_resizing = False

def mouse_move(sender, app_data):
    global is_dragging, is_resizing, offset_x, offset_y, curr_vp_x, curr_vp_y

    #mouse_x, mouse_y = app_data
    mouse_x, mouse_y = dpg.get_mouse_pos()
    if is_dragging:
        curr_vp_x = curr_vp_x + mouse_x - offset_x
        curr_vp_y = curr_vp_y + mouse_y - offset_y

        dpg.set_viewport_pos([curr_vp_x, curr_vp_y])
    elif is_resizing:
        dpg.set_viewport_height(mouse_y)
        dpg.set_viewport_width(mouse_x)

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
LIGHT_ACCENT = (50, 50, 200, 255)  # check, slider grab, etc.

DARK_BG = (45, 45, 48, 128)
DARK_BG_LIGHTER = (80, 80, 80, 128)
DARK_CHILD_BG = (60, 60, 65, 255)
DARK_BORDER = (90, 90, 90, 255)
DARK_FRAME = (70, 70, 75, 255)
DARK_FRAME_HOVER = (100, 100, 150, 255)
DARK_FRAME_ACTIVE = (120, 120, 200, 255)
DARK_TEXT = (255, 255, 255, 255)
DARK_BUTTON = DARK_BG #(90, 90, 100, 255)
DARK_BUTTON_HOVER = (120, 120, 180, 255)
DARK_BUTTON_ACTIVE = (150, 150, 200, 255)
DARK_ACCENT = (100, 150, 255, 255)  # check, slider grab, etc.

with dpg.theme() as theme_light:
    with dpg.theme_component(dpg.mvAll):
        # tło i ramki
        dpg.add_theme_color(dpg.mvThemeCol_WindowBg, LIGHT_BG)
        dpg.add_theme_color(dpg.mvThemeCol_ChildBg, LIGHT_CHILD_BG)
        dpg.add_theme_color(dpg.mvThemeCol_PopupBg, LIGHT_CHILD_BG)
        dpg.add_theme_color(dpg.mvThemeCol_Border, LIGHT_BORDER)
        dpg.add_theme_color(dpg.mvThemeCol_FrameBg, LIGHT_FRAME)
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, LIGHT_FRAME_HOVER)
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, LIGHT_FRAME_ACTIVE)

        # tekst i przyciski
        dpg.add_theme_color(dpg.mvThemeCol_Text, LIGHT_TEXT)
        dpg.add_theme_color(dpg.mvThemeCol_Button, LIGHT_BUTTON)
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, LIGHT_BUTTON_HOVER)
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, LIGHT_BUTTON_ACTIVE)

        # checkboxes, radiobuttons, sliders
        dpg.add_theme_color(dpg.mvThemeCol_CheckMark, LIGHT_ACCENT)
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, LIGHT_ACCENT)
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (30, 30, 180, 255))
        dpg.add_theme_color(dpg.mvThemeCol_Header, LIGHT_FRAME)
        dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, LIGHT_FRAME_HOVER)
        dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, LIGHT_FRAME_ACTIVE)

        # taby
        dpg.add_theme_color(dpg.mvThemeCol_Tab, LIGHT_FRAME)
        dpg.add_theme_color(dpg.mvThemeCol_TabHovered, LIGHT_FRAME_HOVER)
        dpg.add_theme_color(dpg.mvThemeCol_TabActive, LIGHT_FRAME_ACTIVE)
        dpg.add_theme_color(dpg.mvThemeCol_TabUnfocused, LIGHT_FRAME)
        dpg.add_theme_color(dpg.mvThemeCol_TabUnfocusedActive, LIGHT_FRAME_HOVER)

        dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 0, 0, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 0, 0, category=dpg.mvThemeCat_Core)
        #dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 2, 2, category=dpg.mvThemeCat_Core)
        #dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 0, 0, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 0, category=dpg.mvThemeCat_Core)

with dpg.theme() as theme_dark:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvPlotCol_PlotBg, DARK_BG_LIGHTER)
        dpg.add_theme_color(dpg.mvPlotCol_FrameBg, DARK_BG_LIGHTER)
        dpg.add_theme_color(dpg.mvThemeCol_WindowBg, DARK_BG)
        dpg.add_theme_color(dpg.mvThemeCol_ChildBg, DARK_CHILD_BG)
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
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (80, 120, 220, 255))
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
        #dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 2, 2, category=dpg.mvThemeCat_Core)
        #dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 0, 0, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 0, category=dpg.mvThemeCat_Core)

#with theme() as text_ok:
 #   with theme_component(dpg.mvText):
 #       dpg.add_theme_color(dpg.mvThemeCol_Text, (220, 220, 220))

#with theme() as text_alert:
#    with theme_component(dpg.mvText):
#        dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 90, 90))

with theme() as red_line_theme:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(
            dpg.mvPlotCol_Line,
            (255, 0, 0, 255),
            category=dpg.mvThemeCat_Plots
        )
        dpg.add_theme_style(
            dpg.mvPlotStyleVar_LineWeight,
            1.0,
            category=dpg.mvThemeCat_Plots
        )
with theme() as reddark_line_theme:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(
            dpg.mvPlotCol_Line,
            (128, 0, 0, 255),
            category=dpg.mvThemeCat_Plots
        )
        dpg.add_theme_style(
            dpg.mvPlotStyleVar_LineWeight,
            1.0,
            category=dpg.mvThemeCat_Plots
        )

with theme() as gray_line_theme:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(
            dpg.mvPlotCol_Line,
            (100, 100, 100, 100),
            category=dpg.mvThemeCat_Plots
        )
        dpg.add_theme_style(
            dpg.mvPlotStyleVar_LineWeight,
            1.0,
            category=dpg.mvThemeCat_Plots
        )

with theme() as white_line_theme:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(
            dpg.mvPlotCol_Line,
            (255, 255, 255, 128),
            category=dpg.mvThemeCat_Plots
        )
        dpg.add_theme_style(
            dpg.mvPlotStyleVar_LineWeight,
            1.0,
            category=dpg.mvThemeCat_Plots
        )

with theme() as green_line_theme:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(
            dpg.mvPlotCol_Line,
            (30, 200, 0, 200),
            category=dpg.mvThemeCat_Plots
        )
        dpg.add_theme_style(
            dpg.mvPlotStyleVar_LineWeight,
            1.0,
            category=dpg.mvThemeCat_Plots
        )

with theme() as grid_line_theme:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(
            dpg.mvPlotCol_Line,
            (128, 128, 128, 128),
            category=dpg.mvThemeCat_Plots
        )
        dpg.add_theme_style(
            dpg.mvPlotStyleVar_LineWeight,
            1.0,
            category=dpg.mvThemeCat_Plots
        )

def widget_tooltip(message,widget=None):
    if not widget:
        widget=dpg.last_item()
    with tooltip(widget, delay=0.3):
        add_text(message)

def key_callback(sender, app_data):
    hide_info()
    if app_data==dpg.mvKey_1:
        show_press(None,None,(0,True))
    elif app_data==dpg.mvKey_2:
        show_press(None,None,(1,True))
    elif app_data==dpg.mvKey_3:
        show_press(None,None,(2,True))
    elif app_data==dpg.mvKey_4:
        show_press(None,None,(3,True))
    elif app_data==dpg.mvKey_5:
        show_press(None,None,(4,True))
    elif app_data==dpg.mvKey_6:
        show_press(None,None,(5,True))
    elif app_data==dpg.mvKey_7:
        show_press(None,None,(6,True))
    elif app_data==dpg.mvKey_8:
        show_press(None,None,(7,True))
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
    elif app_data==dpg.mvKey_F12:
        settings_wrapper()
    elif app_data==dpg.mvKey_L:
        theme_light_callback()
    elif app_data==dpg.mvKey_D:
        theme_dark_callback()
    elif app_data==dpg.mvKey_S:
        save_image()
    elif app_data==dpg.mvKey_F:
        fft_toggle()
    elif app_data==dpg.mvKey_V:
        vsync=get_value('vsync')
        vsync=(True,False)[vsync]
        set_value('vsync',vsync)
        vsync_callback(None,vsync)
    elif app_data==dpg.mvKey_H:
        set_value('debug_text2','H - help\nF12 - settings\n\nF1 - about\nL - light theme\nD - dark theme\n\nV - VSync toggle\n\n1,2,3,4,5,6,7,8 - show/hide track\n\nS - take screenshot\nC - save csv\nF - toggle FFT')
    elif app_data==dpg.mvKey_Escape:
        global lock_frequency,sweeping
        lock_frequency=False
        sweeping=False
        set_value('debug_text2','')
    else:
        #print('key_callback',sender, app_data)
        pass

def slide_change(sender):
    val=get_value(sender)
    dpg.set_axis_limits("y_axis", dbmin_display*val/100, dbmax_display)

vsync_default=False
settings_height=120

status_height=50
plot_min_height=200
plot_axis_height=40
viewport_height_min=plot_min_height+status_height

def theme_light_callback():
    dpg.bind_theme(theme_light)
    bind_item_theme("fft_line",gray_line_theme)

def theme_dark_callback():
    dpg.bind_theme(theme_dark)
    bind_item_theme("fft_line",white_line_theme)

def debug_callback():
    set_value('debug_text','')

decoration=True
create_viewport(title=title,width=1200,min_height=viewport_height_min,vsync=vsync_default,decorated=decoration)

bottom_shown=True

def settings_wrapper():
    global bottom_shown
    bottom_shown=(True,False)[bottom_shown]
    l_info(f'settings_wrapper:{bottom_shown}')

    if bottom_shown:
        show_item('settings_table')
        #show_item('settings_window')
        h=max(viewport_height_min,get_viewport_height()+settings_height)
    else:
        hide_item('settings_table')
        #hide_item('settings_window')
        h=max(viewport_height_min,get_viewport_height()-settings_height)

    set_viewport_height(h)
    on_viewport_resize()

    try:
        values=[ api['name'] for api in apis if api['devices'] ]
        configure_item('api',items=values)

        apiname=get_value('api')
        if apiname not in values:
            if values:
                set_value('api',values[0]['name'])

    except Exception as e:
        l_error(f'settings_wrapper:{e}')

info_chars=0

def on_viewport_resize(sender=None, app_data=None):
    vw = get_viewport_client_width()
    vh = get_viewport_client_height()

    global info_chars,settings_height

    info_chars=int(vw/7)

    plot_height  = max(plot_min_height, vh - (settings_height if bottom_shown else 0) - status_height)

    set_item_height('slider', plot_height-plot_axis_height)
    set_item_height('slider_window', plot_height-plot_axis_height+8)

    set_item_height('plot', plot_height)
    set_item_width('plot', vw-80)

    set_item_pos('info_window',[0,0])
    set_item_pos('debug_text',[85,20])
    set_item_pos('debug_text2',[385,20])
    set_item_width('info_window', vw)
    set_item_height('info_window', vh)

###################################################
with window(tag='main',no_title_bar=True,no_scrollbar=True,no_resize=True,no_move=True) as main:
    set_primary_window(main, True)

    if not decoration:
        with dpg.table(header_row=False,resizable=False, policy=dpg.mvTable_SizingStretchProp,borders_outerH=False, borders_innerV=False, borders_outerV=False):
            dpg.add_table_column( width_fixed=True, init_width_or_weight=60)
            dpg.add_table_column( width_stretch=True, init_width_or_weight=10)
            dpg.add_table_column( width_fixed=True, init_width_or_weight=16)

            with dpg.table_row():
                dpg.add_text(title)
                dpg.add_spacer()
                dpg.add_button(label="X", callback=lambda: sys.exit())

        with dpg.handler_registry():
            dpg.add_mouse_down_handler(button=0, callback=mouse_down)
            dpg.add_mouse_release_handler(button=0, callback=mouse_release)
            dpg.add_mouse_move_handler(callback=mouse_move)

    with window(tag='info_window',no_close=True,menubar=False,no_title_bar=True,autosize=False,no_scrollbar=True):
        add_text(tag='info_text',default_value='')
        hide_item('info_window')

    with dpg.table(header_row=False, resizable=False, policy=dpg.mvTable_SizingStretchProp,
        borders_innerH=False, borders_innerV=False, borders_outerH=False, borders_outerV=False,
        row_background=False, context_menu_in_body=False, freeze_rows=0, freeze_columns=0,
        no_host_extendX=False, no_host_extendY=False, pad_outerX=False, no_pad_outerX=True):

        add_table_column(width_stretch=True, init_width_or_weight=-1)

        with dpg.table_row():
            with dpg.group(tag='plot_combo',horizontal=True):
                dpg.add_spacer(width=6)

                with child_window(tag='slider_window',no_scrollbar=True, border=False,width=12):
                    dpg.add_spacer(height=6)
                    dpg.add_slider_float(tag='slider',callback=slide_change,vertical=True,max_value=30,min_value=100,default_value=100,format="",width=10)

                with plot(tag='plot',no_mouse_pos=True,no_menus=True,no_frame=True):
                    yticks = (('dBFS',00),('-10',-10),("-20",-20),('-30',-30),('-40',-40),('-50',-50),('-60',-60),('-70',-70),('-80',-80),('-90',-90), ("-100",-100), ("-110",-110), ("-120",-120))
                    xticks = (('',10),("20Hz",20),('',30),('',40),('',50),('',60),('',70),('',80),('',90), ("100Hz",100),
                        ('',200),('',300),('',400),('',500),('',600),('',700),('',800),('',900),("1kHz",1000),
                        ("",2000),("",3000),("",4000),("",5000),("",6000),("",7000),("",8000),("",9000),("10kHz",10000),("20kHz",20000))
                    dpg.add_plot_annotation(tag='cursor_f_txt',label='',parent='y_axis',default_value=(10, -5), color=(0, 0, 0, 0), offset=(5,0))
                    dpg.add_plot_annotation(tag='cursor_db_txt',label='',parent='y_axis',default_value=(100, -30), color=(0, 0, 0, 0), offset=(0,0))

                    with dpg.plot_axis(dpg.mvXAxis, tag='x_axis',no_highlight=True) as xaxis:
                        configure_item(dpg.last_item(),scale=dpg.mvPlotScale_Log10)
                        dpg.set_axis_limits("x_axis", fmin,fmax)
                        dpg.set_axis_ticks("x_axis", xticks)

                    with dpg.plot_axis(dpg.mvYAxis, tag = 'y_axis',no_highlight=True):
                        dpg.set_axis_limits("y_axis", dbmin_display, dbmax_display)
                        dpg.set_axis_ticks("y_axis", yticks)

                        #add_line_series(fft_line_data_x, fft_line_data_y, tag="fft_line",label='FFT', user_data='FFT')
                        add_line_series([20], [-120], tag="fft_line",label='FFT', user_data='FFT')

                        add_line_series((0,0),(dbmin,0),tag="cursor_f")
                        bind_item_theme("cursor_f",red_line_theme)

                        for lab,val in xticks:
                            if lab:
                                add_line_series([val,val], [-130,0],tag=f'stick{val}')
                                bind_item_theme(f'stick{val}',grid_line_theme)

                        for track in range(tracks):
                            #add_line_series(bucket_freqs, track_line_data_y[track], tag=f"track{track}",label=f"track{track+1}",user_data=track,show=False)
                            add_line_series([20], [-120], tag=f"track{track}",label=f"track{track+1}",user_data=track,show=False)

                    dpg.add_image_series(
                        texture_tag=ico['bg'],
                        bounds_min=(0, -280),
                        bounds_max=(40000, 0),
                        parent='y_axis'
                    )

                    with item_handler_registry(tag="plot_handlers"):
                        add_item_hover_handler(callback=on_mouse_move)
                        add_item_clicked_handler(callback=on_click_plot)

                    bind_item_handler_registry("plot", "plot_handlers")

                with dpg.group(tag='buttons'):
                    dpg.add_spacer(height=6)
                    for track_temp in range(tracks):
                        add_image_button(ico[f"{track_temp+1}_off"],tag=f'showcheck{track_temp}',callback=show_press,user_data=(track_temp,True))
                        widget_tooltip(f'Show/Hide track:{track_temp+1}')

        with dpg.table_row():
            with dpg.table(header_row=False, resizable=False, policy=dpg.mvTable_SizingStretchProp,
                borders_innerH=False, borders_innerV=False, borders_outerH=False, borders_outerV=False,
                row_background=False, context_menu_in_body=False, freeze_rows=0, freeze_columns=0,
                no_host_extendX=False, no_host_extendY=False, pad_outerX=False, no_pad_outerX=True):

                add_table_column(width_fixed=True, init_width_or_weight=6, width=6)
                add_table_column(width_fixed=True, init_width_or_weight=18, width=18)
                add_table_column(width_fixed=True, init_width_or_weight=60, width=60)
                add_table_column(width_fixed=True, init_width_or_weight=18, width=18)
                add_table_column(width_stretch=True, init_width_or_weight=-1)
                add_table_column(width_fixed=True, init_width_or_weight=255, width=255)

                with dpg.table_row():
                    dpg.add_spacer(height=6)
                    add_image_button(ico["rec"],tag='recx',callback=rec_press)
                    add_combo(tag='rec_track',items=['none','1','2','3','4','5','6','7','8'],default_value='1',callback=record_track_changed,width=-1)
                    add_image_button(ico["reset"],tag=f'resetrack',callback=resetrack_press,label="X")
                    widget_tooltip(' Reset selected track samples.')

                    add_text(tag='status',default_value='')

                    with dpg.group(horizontal=True):
                        add_image_button(ico["play"],tag='sweep',callback=sweep_press)
                        widget_tooltip('Run frequency sweep')
                        dpg.add_spacer(width=16)
                        add_image_button(ico["save_pic"],tag='save_image',callback=save_image)
                        widget_tooltip("Save Image file")
                        add_image_button(ico["save_csv"],tag='save_csv_button',callback=save_csv)
                        widget_tooltip("Save CSV file")
                        add_image_button(ico["load_csv"],tag='load_csv_button',callback=load_csv)
                        widget_tooltip("Load CSV file")
                        dpg.add_spacer(width=16)
                        add_image_button(ico["home"],tag='homepage',callback=go_to_homepage)
                        widget_tooltip(f'Visit project homepage ({HOMEPAGE})')
                        add_image_button(ico["license"],tag='licensex',callback=license_wrapper)
                        widget_tooltip('Show License')
                        add_image_button(ico["about"],tag='aboutx',callback=about_wrapper)
                        widget_tooltip("Show 'About' Dialog")
                        add_image_button(ico["settings"],tag='settingsx',callback=settings_wrapper)
                        widget_tooltip("Show settings")
        with dpg.table_row():
                with dpg.table(tag='settings_table',header_row=False, resizable=False, policy=dpg.mvTable_SizingStretchProp):

                    add_table_column(width_fixed=True, init_width_or_weight=6, width=6)
                    add_table_column(width_fixed=True, init_width_or_weight=46, width=46)
                    add_table_column(width_fixed=True, init_width_or_weight=140, width=140)
                    add_table_column(width_fixed=True, init_width_or_weight=100, width=100)
                    add_table_column(width_stretch=True, init_width_or_weight=300)
                    add_table_column(width_stretch=True, init_width_or_weight=300)
                    add_table_column(width_fixed=True, init_width_or_weight=20, width=20)
                    add_table_column(width_fixed=True, init_width_or_weight=100, width=100)
                    add_table_column(width_fixed=True, init_width_or_weight=6, width=6)

                    with dpg.table_row():
                        add_text(default_value='')
                        with dpg.group():
                            add_text(default_value='API')
                            add_text(default_value='')
                            add_text(default_value='FFT')
                            add_text(default_value=' window')
                            add_text(default_value=' size')
                            add_text(default_value='buckets')

                        with dpg.group(width=-1):
                            add_combo(tag='api',default_value='',callback=api_changed)
                            add_checkbox(tag='exclusive',label='WASAPI Exclusive',callback=wasapi_exclusive_callback,default_value=False,enabled=windows)
                            add_text(default_value='')

                            add_combo(tag='fft_window',items=['off','ones','hanning','hamming','blackman','bartlett'],default_value='blackman',callback=fft_window_changed)
                            widget_tooltip(' Show live Fast Fourier Transform graph \n with window function specified')
                            add_combo(tag='fft_size',items=['64','128','256','512','1024','2048','4096','8192','16384','32768','65536'],default_value='2048',callback=fft_change)
                            add_combo(tag='buckets',items=['64','128','256','512','1024','2048','4096'],default_value='512',callback=buckets_quant_change)
                            add_checkbox(tag='postprocessing',label='FFT Postprocessing',callback=postprocessing_callback,default_value=postprocessing)

                        with dpg.group():
                            add_text(default_value=' ')
                            add_text(default_value='Device:')
                            add_text(default_value='channels:')
                            add_text(default_value='Samplerate:')
                            add_text(default_value='latency:')
                            add_text(default_value='blckocksize:')
                        with dpg.group(width=-1):
                            add_text(default_value='Output')
                            add_combo(tag='out_dev',default_value='',callback=out_dev_changed,user_data=True)
                            add_combo(tag='out_channel',default_value='',callback=out_channel_changed,user_data=True)
                            add_text(tag='out_samplerate')

                            add_combo(tag='out_latency',label='',callback=out_latency_changed,items=latency_values,default_value=out_latency_default,user_data=True)
                            add_combo(tag='out_blocksize',label='',callback=out_blocksize_changed,items=out_blocksize_values,default_value=out_blocksize_default,user_data=True)

                        with dpg.group(width=-1):
                            add_text(default_value='Input')
                            add_combo(tag='in_dev',default_value='',callback=in_dev_changed,user_data=True)
                            add_combo(tag='in_channel',default_value='',callback=in_channel_changed,user_data=True)
                            add_text(tag='in_samplerate')

                            add_combo(tag='in_latency',label='',callback=in_latency_changed,items=latency_values,default_value=in_latency_default,user_data=True)
                            add_combo(tag='in_blocksize',label='',callback=in_blocksize_changed,items=in_blocksize_values,default_value=in_blocksize_default,user_data=True)

                        dpg.add_spacer(width=20)

                        with dpg.group():
                            add_checkbox(tag='vsync',label='VSync',callback=vsync_callback,default_value=vsync_default)
                            add_checkbox(tag='debug',label='Debug',callback=debug_callback,default_value=False)
                            add_text(default_value='')

                            with dpg.group(horizontal=True):
                                add_image_button(ico["light"],callback=theme_light_callback,width=16)
                                widget_tooltip("light theme ")

                                add_image_button(ico["dark"],callback=theme_dark_callback,width=16)
                                widget_tooltip("dark theme ")

                        with dpg.group():
                            dpg.add_spacer(width=6)

    add_text(tag='debug_text',default_value='')
    add_text(tag='debug_text2',default_value='')

    with dpg.handler_registry():
        dpg.add_mouse_click_handler(callback=on_click)
        dpg.add_mouse_release_handler(callback=on_release)
        dpg.add_mouse_wheel_handler(callback=wheel_callback)
        dpg.add_key_press_handler(callback=key_callback)


dpg.set_viewport_small_icon(Path(path_join(EXECUTABLE_DIR,"./icons/sas_small.png")))
dpg.set_viewport_large_icon(Path(path_join(EXECUTABLE_DIR,"./icons/sas.png")))

dpg.set_viewport_resize_callback(callback=on_viewport_resize)

dpg.setup_dearpygui()

########################################################################

theme_dark_callback()

try:
    distro_info=Path(path_join(EXECUTABLE_DIR,'distro.info.txt')).read_text(encoding='utf-8')
except Exception as exception_1:
    print(exception_1)
    distro_info = 'Error. No distro.info.txt file.'

distro_info+= "\nnumpy       " + str(numpy_version) + "\nsounddevice " + str(sounddevice_version) + "\n\nDearPyGui   " + str(dpg.get_dearpygui_version()) + "\n\n"

print(distro_info)
l_info(distro_info)

sweeping=False

stream_in=None
stream_out=None

refresh_devices()


show_viewport()
set_viewport_height(460)
settings_wrapper()

fft_on=True

buckets_quant_change()
fft_change()
#->fft_window_changed()

api_changed()

data=zeros(fft_size)
next_sweep_time=0

status_text=''
def set_status(text,alert=False):
    global status_text
    if text!=status_text:
        set_value('status',text)
        status_text=text

        #if alert:
        #    bind_item_theme("status_text", text_alert)
        #else:
        #    bind_item_theme("status_text", text_ok)


def mouse_down():
    pass

def mouse_up():
    pass

def on_drag(sender, app_data):
    pass

next_fps = perf_counter()+1
frames = 0
rec_callbacks = 0
rec_samples = 0

with dpg.handler_registry():
    dpg.add_mouse_drag_handler(button=dpg.mvMouseButton_Left,callback=on_drag)
    dpg.add_mouse_down_handler(button=dpg.mvMouseButton_Left, callback=mouse_down)
    dpg.add_mouse_release_handler(button=dpg.mvMouseButton_Left, callback=mouse_up)

record_track_changed()
dpg.configure_app(init_file=ini_file,load_init_file=True)

while is_dearpygui_running():
    #get_delta_time
    if sweeping:
        now=perf_counter()
        if now>next_sweep_time:
            sweeping_i+=1
            if sweeping_i<sweep_steps:
                logf=logf_min_audio+sweeping_i*logf_sweep_step
                f=10**logf

                change_f(f)
                set_value('status','Sweeping (' + str(round(f))+ ' Hz), Click on the graph to abort ...')

                next_sweep_time=now+sweeping_delay
            else:
                sweeping=False
                play_stop()

    try:
        #print(f'{samples_chunks_fifo_new=}')
        if samples_chunks_fifo_new:
            data=np_append(data,np_concatenate(samples_chunks_fifo))[-fft_size:]
            rec_callbacks+=samples_chunks_fifo_chunks_new
            rec_samples+=samples_chunks_fifo_new

            #from numpy.random import randn
            #data = randn(fft_size)

            samples_chunks_fifo_new=0
            samples_chunks_fifo_chunks_new=0

            current_sample_db = 10 * log10( np_mean(np_square(data)) + 1e-12)
            if fft_on:
                fft_values=20*np_log10( np_abs( (np_fft_rfft( data*fft_window))[0:fft_points] ) / fft_size + 1e-12)
                fft_values_means_in_buckets = bincount(bin_indices, weights=fft_values)[1:] / bin_counts[1:]

                #set_value("fft_line", [fft_line_new_x, np_concatenate([fft_values[1:fft_line_data_x_border_index],fft_values_means_in_buckets[bucket_freqs_border_index:]])])

                if postprocessing:
                    #1,0
                    #print(fft_line_data_x_border_index,bucket_freqs_border_index)
                    if bucket_freqs_border_index==0:
                        set_value("fft_line", [fft_line_new_x, fft_values_means_in_buckets] )
                    else:
                        set_value("fft_line", [fft_line_new_x, np_concatenate([array([-120.0]),fft_values[1:fft_line_data_x_border_index],fft_values_means_in_buckets[bucket_freqs_border_index:]]) ])
                else:
                    set_value("fft_line", [fft_line_new_x, fft_values ])


                #print(f'fft_line_new_x:{len(fft_line_new_x)}')
                #print(f'fft_size:{fft_size},fft_values:{len(fft_values)}')
                #print(f'fft_values_means_in_buckets:{len(fft_values_means_in_buckets)}')

                #vals=np_concatenate([fft_values[:fft_line_data_x_border_index],fft_values_means_in_buckets[bucket_freqs_border_index:]])
                #vals[0]=-120
                #set_value("fft_line", [fft_line_new_x, vals])

            if playing_state and recorded_track is not None:
                track_line_data_y[recorded_track][current_bucket]=current_sample_db if played_bucket_callbacks>record_blocks_len else ( track_line_data_y[recorded_track][current_bucket]*record_blocks_len_part1 + current_sample_db*record_blocks_len_part2 ) / record_blocks_len
                redraw_tracks_lines=True

            set_value('cursor_db_txt', (25000, current_sample_db))
            configure_item('cursor_db_txt',label=f'{round(current_sample_db)}dB')

            if current_sample_db<-110:
                set_status('No signal / Mic not connected ...',1)

        if redraw_tracks_lines:
            for track,show in enumerate(show_track):
                configure_item(f"track{track}",show=show)
                if show:
                    set_value(f"track{track}", [bucket_freqs, track_line_data_y[track]])

                    if track!=recorded_track:
                        bind_item_theme(f"track{track}",gray_line_theme)

            redraw_tracks_lines=False

        render_dearpygui_frame()

        ##################################
        frames += 1
        now = perf_counter()
        if now >= next_fps and get_value('debug'):
            out_sum=audio_output_callback_outside+audio_output_callback_inside
            out_ratio = 0 if out_sum==0 else audio_output_callback_inside/out_sum

            in_sum=audio_input_callback_outside+audio_input_callback_inside
            in_ratio = 0 if in_sum==0 else audio_input_callback_inside/in_sum

            set_value('debug_text',f'FPS:{frames}\n\n{rec_callbacks=}\n{rec_samples=}\n\nOUT  {out_ratio}\nIN   {in_ratio}')

            frames = 0
            rec_callbacks = 0
            rec_samples = 0
            next_fps = now+1.0

            audio_output_callback_outside=0
            audio_output_callback_inside=0

            audio_input_callback_outside=0
            audio_input_callback_inside=0
        ##################################
    except Exception as loop_e:
        print('main loop exception:',loop_e)

    if exiting:
        break

print('exiting')
sweeping=False
lock_frequency=False

play_stop()
out_stream_stop()

exiting=True

if stream_in:
    stream_in.stop()
    stream_in.close()

dpg.save_init_file(ini_file)

destroy_context()
l_info('Exiting.')
sys_exit(0)

