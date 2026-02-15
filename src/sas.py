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

from dearpygui.dearpygui import create_context,file_dialog,add_file_extension,get_plot_mouse_pos,set_value,get_value,bind_item_theme,item_handler_registry,plot,add_line_series,add_scatter_series,theme,configure_item,render_dearpygui_frame,is_dearpygui_running,destroy_context,theme_component,add_item_clicked_handler,add_item_deactivated_handler,add_item_hover_handler,bind_item_handler_registry,add_mouse_release_handler,add_mouse_wheel_handler,handler_registry,add_combo,child_window,table_row,add_checkbox,add_button,add_text,add_table_column,window,table,is_item_hovered,show_item,tooltip,add_image_button,add_static_texture,texture_registry,output_frame_buffer

from time import sleep,strftime,localtime,perf_counter

#import numpy as np
from numpy import mean as np_mean,square as np_square,float32,ones,hanning,hamming,blackman,bartlett, abs as np_abs,fft as np_fft,log10 as np_log10,__version__ as numpy_version, concatenate as np_concatenate,sum as np_sum, arange, sin as np_sin,zeros, append as np_append
from numpy.random import randn
from sounddevice import Stream,InputStream,OutputStream,query_devices,default as sd_default,query_hostapis,__version__ as sounddevice_version
from collections import deque
from queue import Queue

from math import pi, log10, ceil, floor
from PIL import ImageGrab, Image

from pathlib import Path

import os
from os import name as os_name, system
from os.path import join as path_join, normpath,dirname

from sys import exit as sys_exit

from images import image
from dialogs import *

from io import BytesIO
VERSION_FILE='version.txt'

HOMEPAGE='https://github.com/PJDude/sas'

windows = bool(os_name=='nt')

#ImageGrab_grab=ImageGrab.grab
np_fft_rfft=np_fft.rfft

blocksize_out = 512
blocksize_in = 512

phase_i = arange(blocksize_out)
#fft_size = blocksize_in*8*2
fft_size = 2048
fft_points=int(fft_size/2+1)

f_current=0
tracks=8
playing_state=0
'''
2 - on
1 - ramp on
0 - off
-1 - ramp off
'''

lock_frequency=False

if windows:
    from os import startfile

def catch(func):
    def wrapper(*args,**kwargs):
        try:
            return func(*args,**kwargs)
        except Exception as e:
            print("catch:",func,e,*args,**kwargs)
            return None
    return wrapper

@catch
def status_set_frequency():
    global show_track
    res_list = [str(round(f_current))+ ' Hz (']
    res_list_append = res_list.append
    if current_bucket<spectrum_buckets_quant:
        for track,show in enumerate(show_track):
            db_temp = round(track_line_data_y[track][current_bucket])
            res_list_append(str(track+1) + ':' + str(db_temp))
    else:
        print(f'{current_bucket=}')

    res_list_append(') [#buffer:dBFS]')
    set_value('status',' '.join(res_list))

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

def save_csv():
    show_item("file_dialog_save")

def save_csv_file_selected(sender, app_data):
    filename=app_data["file_path_name"]

    if filename:
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
            print("save_csv_error:",e)

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
            print("Load_csv_error:",e)

        global redraw_tracks_lines
        redraw_tracks_lines=True

def load_csv():
    show_item("file_dialog_load")

def save_png_file_selected(sender, app_data):
    filename=app_data["file_path_name"]

    time_postfix=strftime('%Y_%m_%d_%H_%M_%S',localtime())

    if filename:
        if os.path.exists(filename):
            print("Name already exists!")
        else:
            path, file = os.path.split(filename)
            name, ext = os.path.splitext(file)

            if ext.lower() in ['.gif', '.png']:
                win_pos = dpg.get_item_pos('main')

                # 2. Pozycja plotu w oknie
                plot_pos = dpg.get_item_pos('plot')

                # 3. Rozmiar plotu
                plot_w = dpg.get_item_width('plot')
                plot_h = dpg.get_item_height('plot')

                # 4. Współrzędne plotu względem viewport / ekranu
                screen_x = win_pos[0] + plot_pos[0]
                screen_y = win_pos[1] + plot_pos[1]

                bbox = (screen_x, screen_y, screen_x + plot_w, screen_y + plot_h)

                print('filename:',filename)
                sleep(0.1)
                output_frame_buffer(filename)

                #print('bbox:',bbox)

                #ImageGrab_grab(bbox).save(filename)
                ###################################
            else:
                print("Unknown file type")
    else:
        print("Cancel")

def save_image():
    show_item("file_dialog_save_image")

def logf_to_bucket(logf):
    return int(floor(scale_factor_logf_to_bucket * (logf - logf_min_audio)))

def bucket_to_logf(i):
    return (i+0.5)/scale_factor_logf_to_bucket + logf_min_audio

phase_step=1.0

def change_f(fpar):
    global current_logf,current_bucket,phase_step,current_bucket,two_pi_by_samplerate

    if fmin_audio<fpar<fmax_audio:
        current_logf=log10(fpar)
        current_f=fpar
        current_bucket=logf_to_bucket(current_logf)

        set_value("cursor_f", ((fpar,fpar), (0,dbmin)))

        phase_step = two_pi_by_samplerate * fpar
    else:
        #print("freq out of range:",fpar)
        pass

    #TODO
    #canvas_delete('cursor_freq')
    #canvas_create_text(x+2, 2, text=str(round(fpar))+"Hz", anchor="nw", font=("Arial", 8), fill="black",tags='cursor_freq')

    #set_value('api',apis[default_api_nr]['name'])

played_bucket=0
played_bucket_callbacks=0

def audio_output_callback(outdata, frames, time, status):
    global phase,playing_state,played_bucket,played_bucket_callbacks,phase_step,two_pi,current_bucket,out_channell_buffer_mod_index,blocksize_out_m1,phase_i

    if playing_state:
        phase_arr=(phase + phase_step * phase_i) % two_pi
        outdata[phase_i, out_channell_buffer_mod_index] = np_sin(phase_arr)
        phase = phase_arr[-1]+phase_step

        if playing_state==1:
            playing_state=2
            outdata[:, out_channell_buffer_mod_index] *= volume_ramp
        elif playing_state==-1:
            playing_state=0
            outdata[:, out_channell_buffer_mod_index] *= volume_ramp[::-1]

        if current_bucket!=played_bucket:
            played_bucket_callbacks=1
            played_bucket=current_bucket
        else:
            played_bucket_callbacks+=1
    else:
        outdata.fill(0)

def sweep_abort():
    global sweeping
    sweeping=False
    set_value('sweep',False)
    print('sweeping aborted')

sweeping_i=0
def sweep_press(sender=None, app_data=None):
    print('sweep_press',sender,app_data)

    global sweeping,lock_frequency,sweeping_i

    if recorded_track is None:
        print('no recorded_track')
        set_value('sweep',False)
        return

    lock_frequency=False

    if get_value('sweep'):
        change_f(fmin_audio)
        sweeping=True
        play_start()
    else:
        sweeping=False
        play_stop()
        play_stop()

    sweeping_i=0

@catch
def play_start():
    global playing_state
    bind_item_theme("cursor_f",red_line_theme)
    playing_state=1
    redraw_tracks_lines=True

@catch
def play_stop():
    global playing_state
    if playing_state==2:
        playing_state=-1

    bind_item_theme("cursor_f",white_line_theme)
    redraw_tracks_lines=False

@catch
def play_abort():
    global playing_state

    bind_item_theme("cursor_f",white_line_theme)
    playing_state=0

exiting=False

current_sample_db=-120

samples_chunks_fifo_new=False
samples_chunks_fifo=deque(maxlen=32)
samples_chunks_fifo_put=samples_chunks_fifo.append

###########################################################
def audio_input_callback(indata, frames, time_info, status):
    samples_chunks_fifo_put(indata[:, 0].copy())

    global samples_chunks_fifo_new
    samples_chunks_fifo_new=True

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
        print('go_to_homepage error:',e)

dialog_shown=False

def pre_show():
    global dialog_shown
    dialog_shown=True

def post_close():
    global dialog_shown
    dialog_shown=False

default_api_nr=0

device_default_input=None
device_default_output=None

@catch
def refresh_devices():
    global apis,default_api_nr,devices,device_default_input,device_default_output

    apis = query_hostapis()
    default_api_nr=-1
    print(f'\nApis:')
    for i,api in enumerate(apis):
        print('')
        for key,val in api.items():
            print('  ',key,':',val)
            if api['devices']:
                default_api_nr=i

    device_default_input_index,device_default_output_index = sd_default.device

    print('\nQuery Devices ...')
    devices=query_devices()

    print('\nLoop Devices ...')
    for dev in devices:
        if not windows:
            try:
                stream_test=Stream(device=dev['index'], samplerate=samplerate, channels=2)
                stream_test.close()
            except Exception as e_try:
                print('e_try:',dev['index'],dev['name'],e_try)
                continue

        if dev['index']==device_default_input_index:
            device_default_input=dev
            default_api_nr=dev['hostapi']
        if dev['index']==device_default_output_index:
            device_default_output=dev
            default_api_nr=dev['hostapi']

    print(f'{default_api_nr=}')
    print(f'{device_default_input=}')
    print(f'{device_default_output=}')

    if default_api_nr!=-1:
        print('\nDefaults:',apis[default_api_nr]['name'],device_default_input['name'],device_default_output['name'])
        set_value('api',apis[default_api_nr]['name'])

    print('\nDevices:')
    for dev in devices:
        print('')
        for key,val in dev.items():
            print('  ',key,':',val)

def dev_out_samplerate_changed(sender=None, app_data=None):
    print('dev_out_samplerate_changed',sender,app_data)

def dev_in_samplerate_changed(sender=None, app_data=None):
    print('dev_in_samplerate_changed',sender,app_data)

@catch
def dev_out_channell_changed(sender=None, app_data=None):
    print('dev_out_channell_changed',sender,app_data)

    global device_out_channels_stream_option,out_channell_buffer_mod_index,lock_frequency,stream_out,device_out_current
    lock_frequency=False
    play_abort()

    if stream_out:
        stream_out.stop()

    try:
        out_channell_buffer_mod_index=int(get_value("dev_out_channell"))-1
        device_out_channels_stream_option=device_out_current['max_output_channels']
    except:
        device_out_channels_stream_option=1
        out_channell_buffer_mod_index=0
    dev_out_channell_config()

@catch
def dev_out_channell_config():
    global stream_out,device_out_current,device_out_channels_stream_option

    try:
        stream_out = OutputStream( samplerate=samplerate, channels=device_out_channels_stream_option, blocksize=blocksize_out, callback=audio_output_callback, device=device_out_current['index'] )
        #dtype="float32",
        #latency="low",
    except Exception as e:
        messagebox.showerror("dev_out_channell_config",str(e))
    else:
        stream_out.start()

@catch
def dev_in_channell_changed(sender=None, app_data=None):
    print('dev_in_channell_changed',sender,app_data)

    global device_in_channels_stream_option,in_channell_buffer_mod_index,stream_in,device_in_current

    if stream_in:
        stream_in.stop()

    try:
        in_channell_buffer_mod_index=int(get_value("dev_in_channell"))-1
        device_in_channels_stream_option=device_in_current['max_input_channels']
    except:
        device_in_channels_stream_option=1
        in_channell_buffer_mod_index=0

    dev_in_channell_config()

def dev_in_channell_config():
    global stream_in,device_in_current,device_in_channels_stream_option

    try:
        stream_in = InputStream( samplerate=samplerate, channels=device_in_channels_stream_option, callback=audio_input_callback,device=device_in_current['index'] , latency="high", blocksize=blocksize_in)
        # dtype="float32"
        #, latency="low"
        #
    except Exception as e:
        print("dev_in_channell_config",e)
    else:
        stream_in.start()

def show_info(title, message):
    with window(label=title,modal=True,no_close=True,autosize=True,tag="info_dialog"):
        add_text(message)
        add_button(label="OK", width=80,callback=lambda: dpg.delete_item("info_dialog"))

    vw, vh = dpg.get_viewport_client_width(), dpg.get_viewport_client_height()
    ww, wh = dpg.get_item_width("info_dialog"), dpg.get_item_height("info_dialog")

    dpg.set_item_pos("info_dialog", ((vw - ww) // 2, (vh - wh) // 2))

@catch
def about_wrapper():
    text1= f'Simple Audio Sweeper {VER_TIMESTAMP}\nAuthor: Piotr Jochymek\n\n{HOMEPAGE}\n\nPJ.soft.dev.x@gmail.com\n'
    text2='\n' + distro_info + '\n'
    show_info('About',text1+text2)

def license_wrapper():
    try:
        license_txt=Path(path_join(APP_DIR,'LICENSE')).read_text(encoding='ASCII')
    except Exception as exception_lic:
        print(exception_lic)
        try:
            license_txt=Path(path_join(dirname(APP_DIR),'LICENSE')).read_text(encoding='ASCII')
        except Exception as exception_2:
            print(exception_2)
            sys_exit(1)

    show_info('License information',license_txt)

settings_shown=False
@catch
def settings_wrapper():
    global settings_shown

    try:
        values=[ api['name'] for api in apis if api['devices'] ]
        configure_item('api',items=values)

        apiname=get_value('api')
        if apiname not in values:
            if values:
                set_value('api',values[0]['name'])

    except Exception as e:
        print(e)

    settings_shown=(True,False)[settings_shown]

    if settings_shown:
        frame_options.grid(sticky='news',columnspan=2,padx=4,pady=(0,2) )
    else:
        frame_options.grid_forget()

@catch
def fft_press():
    global fft_on
    fft_on=get_value('fft')
    print('fft_press:',fft_on)

    fft_set()
    fft_window_changed()

fft_on=True

@catch
def fft_set():
    set_value("fft",fft_on)
    configure_item("fft_line", show=fft_on)

def resetrack_press(sender=None, app_data=None, track=None):
    print('resetrack:',sender,app_data,track)

    if recording_enabled[track]:
        sweep_abort()

        track_line_data_y[track]=[dbinit]*spectrum_buckets_quant

        global redraw_tracks_lines
        redraw_tracks_lines=True
    else:
        print('recording not enabled for track',track)

recording_enabled=[False]*tracks
recorded_track=None
def recording_press(sender=None, app_data=None,track=None):
    print('recording_press:',sender,app_data,track)

    global recording_enabled,recorded_track,redraw_tracks_lines

    sweep_abort()

    if app_data:
        set_value(f'showcheck{track}',True)
        show_press(sender,True,track)

        for track_temp in range(tracks):
            recording_enabled[track_temp]=False
            set_value(f'recordcheck{track_temp}',False)

        set_value(f'recordcheck{track}',True)
        recorded_track=track
    else:
        recorded_track=None

    configure_item("sweep", enabled=app_data)
    configure_item(f"resetrack{track}", enabled=app_data)
    recording_enabled[track]=app_data
    redraw_tracks_lines=True

show_track=[False]*tracks
def show_press(sender=None, app_data=None,track=None):
    print('show_press:',sender,app_data,track)

    sweep_abort()

    global show_track,redraw_tracks_lines
    if not app_data:
        set_value(f'recordcheck{track}',False)
        recording_press(sender,False,track)

    show_track[track]=app_data
    track_pressed(track)
    redraw_tracks_lines=True

@catch
def track_pressed(track):
    global redraw_tracks_lines,sweeping,lock_frequency

    lock_frequency=False
    sweep_abort()

    try:
        play_stop()

        redraw_tracks_lines=True
        status_set_frequency()

    except Exception as e_kp:
        print("track_pressed:",track, e_kp)

try:
    VER_TIMESTAMP=Path(os.path.join(os.path.dirname(__file__),VERSION_FILE)).read_text(encoding='ASCII').strip()
except Exception as e_ver:
    print(e_ver)
    VER_TIMESTAMP=''

samplerate = 44100

phase = 0.0

fmin,fini,fmax=10,442,30000
fmin_audio,fmax_audio=20,20000

logf_min,logf_ini,logf_max=log10(fmin),log10(fini),log10(fmax)
logf_min_audio,logf_max_audio=log10(fmin_audio),log10(fmax_audio)

current_f=fini
current_logf=logf_ini

two_pi = pi+pi
two_pi_by_samplerate = two_pi/samplerate

spectrum_buckets_quant=256
spectrum_sub_bucket_samples=4
sweep_steps=spectrum_buckets_quant*spectrum_sub_bucket_samples
logf_max_audio_m_logf_min_audio = logf_max_audio-logf_min_audio
logf_sweep_step=logf_max_audio_m_logf_min_audio/sweep_steps


scale_factor_logf_to_bucket=spectrum_buckets_quant/logf_max_audio_m_logf_min_audio

current_bucket=logf_to_bucket(current_logf)

dbmin=-122.0
dbmin_display=-123.0
dbinit=dbmin
dbmax_display=dbmax=0.0

dbrange=dbmax-dbmin

dbrange_display=dbmax_display-dbmin_display

samplerate_by_fft_size = samplerate / fft_size

blocksize_out_m1=blocksize_out-1

#volume_ramp = tuple([(i+1.0)/blocksize_out for i in range(blocksize_out)])
volume_ramp = arange(1, blocksize_out + 1, dtype=float32) / blocksize_out

time_to_collect_sample=0.125 #[s]
#1/4s - 86 paczek
#record_blocks_len=int((samplerate/4)/blocksize_in)

sweeping_delay=time_to_collect_sample*1.5/spectrum_sub_bucket_samples
#print(f'{sweeping_delay=}')

# 43
record_blocks_len=int((samplerate*time_to_collect_sample)/blocksize_in)
record_blocks_len_part1=int(record_blocks_len/2)
record_blocks_len_part2=record_blocks_len-record_blocks_len_part1
record_blocks_len_short=ceil(record_blocks_len/5)

redraw_tracks_lines=True

title=f"Simple Audio Sweeper {VER_TIMESTAMP}"

create_context()

ico = {}
for name, data in image.items():
    img = Image.open(BytesIO(data)).convert("RGBA")
    w, h = img.size
    with texture_registry():
        #add_static_texture(w, h, [v/255 for px in list(img.getdata()) for v in px], tag=name)
        add_static_texture(w, h, [v/255 for px in list(img.get_flattened_data()) for v in px], tag=name)
    ico[name] = name

with file_dialog(directory_selector=False,show=False,callback=save_csv_file_selected,id="file_dialog_save",file_count=1,default_filename="sas"):
    add_file_extension(".csv", color=(255, 255, 0))
    add_file_extension(".*")

with file_dialog(directory_selector=False,show=False,callback=save_png_file_selected,id="file_dialog_save_image",file_count=1,default_filename="sas"):
    add_file_extension(".png", color=(255, 255, 0))
    add_file_extension(".*")

with file_dialog(directory_selector=False,show=False,callback=load_csv_file_selected,id="file_dialog_load",file_count=1,default_filename="sas"):
    add_file_extension(".csv", color=(255, 255, 0))
    add_file_extension(".*")

current_api=None

@catch
def api_changed(sender=None, app_data=None):

    global current_api,apis,devices,dev_in_cb

    apiname=get_value('api')
    print('api_changed',sender, app_data,apiname)

    current_api=[api for api in apis if api['name']==apiname][0]

    out_values=[ dev['name'] for dev in devices if dev['max_output_channels'] > 0 and dev['index'] in current_api['devices'] ]
    in_values=[ dev['name'] for dev in devices if dev['max_input_channels'] > 0 and dev['index'] in current_api['devices'] ]

    dev_out_name=get_value("dev_out")
    dev_in_name=get_value("dev_in")

    configure_item("dev_out",items=out_values)
    configure_item("dev_in",items=in_values)

    device_default_input_name=device_default_input['name']
    device_default_output_name=device_default_output['name']

    print('defaults:',device_default_input_name,device_default_output_name)

    if out_values:
        if dev_out_name not in out_values:
            if device_default_output_name in out_values:
                set_value("dev_out",device_default_output_name)
            else:
                set_value("dev_out",out_values[0])

    dev_out_changed()

    if in_values:
        if dev_in_name not in in_values:
            if device_default_input_name in in_values:
                set_value("dev_in",device_default_input_name)
            else:
                set_value("dev_in",in_values[0])

    dev_in_changed()

@catch
def fft_window_changed(sender=None, app_data=None):
    fft_window_name=get_value('fft_window')

    global fft_window,window_correction
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
        print('unknown window:',fft_window_name)

    window_correction = np_sum(fft_window)

    print('fft_window_changed',sender, app_data,fft_window_name,len(fft_window))

    #fft_window = eval(f'{fft_window_name}({fft_size})')()

device_out_current=None

@catch
def dev_out_changed(sender=None, app_data=None):
    print('dev_out_changed',sender, app_data)

    global device_out_current,device_out_channels_stream_option

    dev_out_name=get_value("dev_out")

    device_out_current=[device for device in devices if device['name']==dev_out_name][0]

    dev_out_channell_values=['all'] + [str(val) for val in range(1,device_out_current['max_output_channels']+1)]
    #dev_out_channell_cb.configure( values=dev_out_channell_cb_values )

    configure_item("dev_out_channell",items=dev_out_channell_values)

    dev_out_channell_value=get_value("dev_out_channell")

    if not dev_out_channell_value or dev_out_channell_value not in dev_out_channell_values:
        dev_out_channell_value='all'
        set_value("dev_out_channell",dev_out_channell_value)

    set_value("dev_out_samplerate",int(device_out_current['default_samplerate']))

    dev_out_channell_changed()

device_in_current=None

@catch
def dev_in_changed(sender=None, app_data=None):
    print('dev_in_changed',sender, app_data)

    global device_in_current,device_in_channels_stream_option

    dev_name=get_value("dev_in")

    device_in_current=[device for device in devices if device['name']==dev_name][0]

    dev_in_channell_values=['all'] + [str(val) for val in range(1,device_in_current['max_input_channels']+1)]
    configure_item("dev_in_channell",items=dev_in_channell_values)

    dev_in_channell_value=get_value("dev_in_channell")

    if not dev_in_channell_value or dev_in_channell_value not in dev_in_channell_values:
        dev_in_channell_value='all'
        set_value("dev_in_channell",dev_in_channell_value)

    set_value("dev_in_samplerate",int(device_in_current['default_samplerate']))

    dev_in_channell_changed()

def on_click(sender, app_data):
    print('on_click',sender, app_data)

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
        print('another button:',button_nr)

def wheel_callback(sender, val):
    scroll_mod(val)

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
        print('another button:',button_nr)

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
                set_value("cursor_f", ((x,x), (dbmin,0)))
                f_current=x
                status_set_frequency()
                change_f(f_current)

fft_line_data_x=[-2]*fft_points
fft_line_data_y=[-2]*fft_points

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
            (128, 128, 128, 128),
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

log_bucket_width=logf_max_audio_m_logf_min_audio/spectrum_buckets_quant
log_bucket_width_by2=log_bucket_width*0.5

bucket_freqs=[0]*spectrum_buckets_quant
for b in range(spectrum_buckets_quant):
    bucket_freqs[b]= 10**(logf_min_audio + log_bucket_width_by2 + log_bucket_width * b)

bucket_freqs=tuple(bucket_freqs)

track_line_data_y={}

for track in range(tracks):
    track_line_data_y[track]=[dbmin]*spectrum_buckets_quant

def widget_tooltip(message,widget=None):
    if not widget:
        widget=dpg.last_item()
    with tooltip(widget, delay=0.3):
        add_text(message)

def key_callback(sender, app_data):
    if app_data==537: #1
        track_pressed(0)
    elif app_data==538: #2
        track_pressed(1)
    elif app_data==539: #3
        track_pressed(2)
    elif app_data==540: #4
        track_pressed(3)
    elif app_data==541: #5
        track_pressed(4)
    elif app_data==542: #6
        track_pressed(5)
    elif app_data==543: #7
        track_pressed(6)
    elif app_data==544: #8
        track_pressed(7)
    elif app_data==513: #left
        scroll_mod(-1,0.001)
    elif app_data==514: #right
        scroll_mod(1,0.001)
    elif app_data==515: #up
        scroll_mod(1,0.0001)
    elif app_data==516: #down
        scroll_mod(-1,0.0001)
    elif app_data==572: #F1
        about_wrapper()
    else:
        #print('key_callback',sender, app_data)
        pass

dpg.create_viewport(title=title)
#,width=1000,height=330
###################################################
with window(tag='main',width=-1,height=-1) as main:
    with dpg.group(horizontal=True):
        with dpg.child_window(width=800,height=500):
            with plot(tag='plot',no_mouse_pos=True,no_menus=True,no_frame=True,width=-1,height=-1) as plot:
                yticks = (('dBFS',00),('-10',-10),("-20",-20),('-30',-30),('-40',-40),('-50',-50),('-60',-60),('-70',-70),('-80',-80),('-90',-90), ("-100",-100), ("-110",-110), ("-120",-120))
                xticks = (('',10),("20Hz",20),('',30),('',40),('',50),('',60),('',70),('',80),('',90), ("100Hz",100),
                    ('',200),('',300),('',400),('',500),('',600),('',700),('',800),('',900),("1kHz",1000),
                    ("",2000),("",3000),("",4000),("",5000),("",6000),("",7000),("",8000),("",9000),("10kHz",10000),("20kHz",20000))

                with dpg.plot_axis(dpg.mvXAxis, tag='x_axis'):
                    configure_item(dpg.last_item(),scale=dpg.mvPlotScale_Log10)
                    dpg.set_axis_limits("x_axis", fmin,fmax)
                    dpg.set_axis_ticks("x_axis", xticks)

                with dpg.plot_axis(dpg.mvYAxis, tag = 'y_axis'):
                    dpg.set_axis_limits("y_axis", dbmin_display, dbmax_display)
                    dpg.set_axis_ticks("y_axis", yticks)

                    add_line_series(fft_line_data_x, fft_line_data_y, tag="fft_line")

                    add_line_series((0,0),(dbmin,0),tag="cursor_f")
                    bind_item_theme("cursor_f",red_line_theme)

                    add_line_series((20000,22000),(-5,-50),tag='cursor_db')
                    bind_item_theme("cursor_db",red_line_theme)

                    #set_value('cursor_db_txt', 'init2')
                    #dpg.set_item_pos('cursor_db_txt')

                    for lab,val in xticks:
                        if lab:
                            add_line_series([val,val], [-130,0],tag=f'stick{val}')
                            bind_item_theme(f'stick{val}',grid_line_theme)

                    for track in range(tracks):
                        add_line_series(bucket_freqs, track_line_data_y[track], tag=f"track{track}")

                with item_handler_registry(tag="plot_handlers"):
                    add_item_hover_handler(callback=on_mouse_move)
                    add_item_clicked_handler(callback=on_click)

        with dpg.child_window(height=500,width=600):
            with dpg.group():
                with dpg.group(horizontal=True):
                    with dpg.group():
                        add_text(default_value='API:')
                        add_text(default_value='Dev out:')
                        add_text(default_value='Out channells:')
                        add_text(default_value='Out samplerate:')
                        add_text(default_value='Dev in:')
                        add_text(default_value='In channells:')
                        add_text(default_value='In samplerate:')
                        add_checkbox(label='FFT',tag='fft',default_value=fft_on,callback=fft_press)
                        widget_tooltip('Show live Fast Fourier Transform graph')
                    with dpg.group():
                        add_combo(tag='api',default_value='',callback=api_changed,width=160)
                        add_combo(tag='dev_out',default_value='',callback=dev_out_changed,width=160)
                        add_combo(tag='dev_out_channell',default_value='',callback=dev_out_channell_changed,width=160)
                        add_combo(tag='dev_out_samplerate',default_value='',callback=dev_out_samplerate_changed,width=160)
                        add_combo(tag='dev_in',default_value='',callback=dev_in_changed,width=160)
                        add_combo(tag='dev_in_channell',default_value='',callback=dev_in_channell_changed,width=160)
                        add_combo(tag='dev_in_samplerate',default_value='',callback=dev_in_samplerate_changed,width=160)
                        add_combo(tag='fft_window',items=['ones','hanning','hamming','blackman','bartlett'],default_value='blackman',callback=fft_window_changed,width=160)
                with dpg.group():
                    with dpg.group(horizontal=True):
                        with dpg.group() as g1:
                            add_text(default_value=f'Track #')
                        with dpg.group() as g2:
                            add_text(default_value=f'Show')
                        with dpg.group() as g3:
                            add_text(default_value=f'Record')
                        with dpg.group() as g4:
                            add_text(default_value=f'Reset')

                        for track_temp in range(tracks):
                            add_text(default_value=f'{track_temp+1}',parent=g1)
                            add_checkbox(tag=f'showcheck{track_temp}',default_value=False,callback=show_press,user_data=track_temp,parent=g2)
                            add_checkbox(tag=f'recordcheck{track_temp}',default_value=False,callback=recording_press,user_data=track_temp,parent=g3)
                            widget_tooltip(f'Enable/Disable Recording of track:{track_temp}')
                            add_button(tag=f'resetrack{track_temp}',callback=resetrack_press,user_data=track_temp,label="X",parent=g4)
                            widget_tooltip(f'Reset all samples of track:{track_temp}')

                    add_checkbox(label='Enable Frequency Sweep',tag='sweep',callback=sweep_press)
                    widget_tooltip('Run frequency sweep')

                    with dpg.group(horizontal=True):
                        add_image_button(ico["save_csv"],tag='save_csv_button',callback=save_csv)
                        widget_tooltip("Save CSV file")
                        add_image_button(ico["load_csv"],tag='load_csv_button',callback=load_csv)
                        widget_tooltip("Load CSV file")
                        add_image_button(ico["save_pic"],tag='save_image',callback=save_image)
                        widget_tooltip("Save Image file")

                        add_image_button(ico["home"],tag='homepage',callback=go_to_homepage)
                        widget_tooltip(f'Visit project homepage ({HOMEPAGE})')
                        add_image_button(ico["license"],tag='licensex',callback=license_wrapper)
                        widget_tooltip('Show License')
                        add_image_button(ico["about"],tag='aboutx',callback=about_wrapper)
                        widget_tooltip("Show 'About' Dialog")

    with dpg.group(horizontal=True):
        add_text(tag='status',default_value=' -----------------------')


    bind_item_handler_registry("plot", "plot_handlers")
    with dpg.handler_registry():
        dpg.add_mouse_release_handler(callback=on_release)
        dpg.add_mouse_wheel_handler(callback=wheel_callback)
        dpg.add_key_press_handler(callback=key_callback)

APP_FILE = normpath(__file__)
APP_DIR = dirname(APP_FILE)

dpg.set_viewport_small_icon(Path(path_join(APP_DIR,"./icons/sas_small.png")))
dpg.set_viewport_large_icon(Path(path_join(APP_DIR,"./icons/sas.png")))

dpg.set_primary_window(main, True)
dpg.setup_dearpygui()
dpg.show_viewport()

########################################################################

try:
    distro_info=Path(path_join(APP_DIR,'distro.info.txt')).read_text(encoding='utf-8')

except Exception as exception_1:
    print(exception_1)
    distro_info = 'Error. No distro.info.txt file.'

distro_info+= "\nnumpy       " + str(numpy_version) + "\nsounddevice " + str(sounddevice_version) + "\n\nDearPyGui   " + str(dpg.get_dearpygui_version()) + "\n\n"

print(f'distro info:\n{distro_info}')

sweeping=False

fft_on=True

stream_in=None
stream_out=None

refresh_devices()

fft_window_changed()

api_changed()

for i_fft in range(fft_points):
    fft_line_data_x[i_fft]=i_fft * samplerate_by_fft_size

fft_set()

data=zeros(fft_size)
next_sweep_time=0


try:
    while is_dearpygui_running():
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

        if samples_chunks_fifo_new:
            data=np_append(data,np_concatenate(samples_chunks_fifo))[-fft_size:]
            #data = randn(fft_size)
            samples_chunks_fifo_new=False

            current_sample_db = 10 * log10( np_mean(np_square(data)) + 1e-12)
            if fft_on:
                set_value("fft_line", [fft_line_data_x, 20*np_log10( np_abs( (np_fft_rfft( data*fft_window))[0:fft_points] ) / fft_size + 1e-12)])

            if playing_state and recorded_track is not None:
                track_line_data_y[recorded_track][current_bucket]=current_sample_db if played_bucket_callbacks>record_blocks_len else ( track_line_data_y[recorded_track][current_bucket]*record_blocks_len_part1 + current_sample_db*record_blocks_len_part2 ) / record_blocks_len
                redraw_tracks_lines=True

            #set_value('cursor_db', str(current_sample_db))
            #dpg.set_item_pos('cursor_db_txt', (20000, current_sample_db))
            dpg.set_value('cursor_db', ((20000,22000), (current_sample_db,current_sample_db)))


        if redraw_tracks_lines:
            for track,show in enumerate(show_track):
                configure_item(f"track{track}",show=show)
                if show:
                    set_value(f"track{track}", [bucket_freqs, track_line_data_y[track]])

                    if recording_enabled[track]:
                        if playing_state:
                            bind_item_theme(f"track{track}",red_line_theme)
                        else:
                            bind_item_theme(f"track{track}",reddark_line_theme)
                    else:
                        bind_item_theme(f"track{track}",gray_line_theme)

            redraw_tracks_lines=False

        render_dearpygui_frame()

        if exiting:
            break

except Exception as main_loop_error:
    print("ERROR:",main_loop_error)

finally:
    sweeping=False
    lock_frequency=False
    play_abort()

    exiting=True

    if stream_in:
        stream_in.stop()
        stream_in.close()

    if stream_out:
        stream_out.close()

    destroy_context()
    sys_exit(1)

