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

from numpy import mean as np_mean,square as np_square,float32,ones,hanning,hamming,blackman,bartlett, abs as np_abs,fft as np_fft,log10 as np_log10,__version__ as numpy_version, concatenate as np_concatenate,sum as np_sum, arange, sin as np_sin,zeros, append as np_append,digitize,bincount,array
from sounddevice import Stream,InputStream,OutputStream,query_devices,default as sd_default,query_hostapis,__version__ as sounddevice_version
from collections import deque
from queue import Queue

from math import pi, log10, ceil, floor
from PIL import Image

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

np_fft_rfft=np_fft.rfft

blocksize_out = 256
blocksize_in = 512

phase_i = arange(blocksize_out)
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

def save_image():
    filename='sas.png'
    set_status(f'saving {filename} ...')
    dpg.output_frame_buffer(filename)

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
        set_value('cursor_f_txt', (fpar, -3))
        configure_item('cursor_f_txt',label=f'{round(fpar)}Hz')

        phase_step = two_pi_by_samplerate * fpar

played_bucket=0
played_bucket_callbacks=0

def audio_output_callback(outdata, frames, time, status):
    global phase,playing_state,played_bucket,played_bucket_callbacks,phase_step,two_pi,current_bucket,out_channell_buffer_mod_index,phase_i

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
    #set_value('sweep',False)
    configure_item('sweep',texture_tag=ico["play"])
    #print('sweeping aborted')

sweeping_i=0
def sweep_press(sender=None, app_data=None):
    print('sweep_press',sender,app_data)

    global sweeping,lock_frequency,sweeping_i
    sweeping=(True,False)[sweeping]

    if recorded_track is None:
        print('no recorded_track')
        sweep_abort()
        #set_value('sweep',False)
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
    global playing_state
    if playing_state==2:
        playing_state=-1

    bind_item_theme("cursor_f",green_line_theme)
    redraw_tracks_lines=False

    if recorded_track:
        bind_item_theme(f"track{recorded_track}",reddark_line_theme)

    sweep_abort()

@catch
def play_abort():
    global playing_state

    bind_item_theme("cursor_f",green_line_theme)
    playing_state=0

exiting=False

current_sample_db=-120

samples_chunks_fifo_chunks_new=0
samples_chunks_fifo_new=0
samples_chunks_fifo=deque(maxlen=32)
samples_chunks_fifo_put=samples_chunks_fifo.append

###########################################################
def audio_input_callback(indata, frames, time_info, status):
    new_samples=len(indata[:, 0])
    samples_chunks_fifo_put(indata[:, 0].copy())

    global samples_chunks_fifo_new,samples_chunks_fifo_chunks_new
    samples_chunks_fifo_new+=new_samples
    samples_chunks_fifo_chunks_new+=1

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
        print("dev_out_channell_config",str(e))
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
        stream_in = InputStream( samplerate=samplerate, callback=audio_input_callback,device=device_in_current['index'] , latency="low", blocksize=0,channels=1,dtype='float32')
        #channels=device_in_channels_stream_option
        # dtype="float32"
        #, latency="low"
        #
    except Exception as e:
        print("dev_in_channell_config",e)
    else:
        stream_in.start()

def hide_info():
    #dpg.hide_item('info')
    #set_value('info_text','')
    on_viewport_resize()
    #dpg.show_item("plot")

def show_info(message):
    pass
    #dpg.hide_item("plot")
    #set_value('info_text',message)
    #show_item('info')

    #configure_item('plot',show=False)

    #with window(label=title,modal=True,no_close=True,autosize=True,tag="info_dialog"):
    ##   add_text(message)
    #    add_button(label="OK", width=80,callback=lambda: dpg.delete_item("info_dialog"))

    #vw, vh = dpg.get_viewport_client_width(), dpg.get_viewport_client_height()
    #ww, wh = dpg.get_item_width("info_dialog"), dpg.get_item_height("info_dialog")

    #dpg.set_item_pos("info_dialog", ((vw - ww) // 2, (vh - wh) // 2))

@catch
def about_wrapper():
    text1= f'Simple Audio Sweeper {VER_TIMESTAMP}\nAuthor: Piotr Jochymek\n\n{HOMEPAGE}\n\nPJ.soft.dev.x@gmail.com\n'
    text2='\n' + distro_info + '\n'
    show_info(text1+text2)

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

    show_info(license_txt)

def settings_wrapper():
    try:
        values=[ api['name'] for api in apis if api['devices'] ]
        configure_item('api',items=values)

        apiname=get_value('api')
        if apiname not in values:
            if values:
                set_value('api',values[0]['name'])

    except Exception as e:
        print(e)

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

show_track=[False]*tracks
def show_press(sender=None, app_data=None,track_combo=None):
    print('show_press:',sender,app_data,track_combo)
    track,press=track_combo

    track_pressed(track)

    global show_track,redraw_tracks_lines,ico,recorded_track
    if press:
        show_track[track]=(True,False)[show_track[track]]

    if show_track[track]:
        configure_item(f'showcheck{track}',texture_tag=ico[f"{track+1}_on"])
    else:
        configure_item(f'showcheck{track}',texture_tag=ico[f"{track+1}_off"])

    if not show_track[track]:
        if recorded_track==track:
            recorded_track=None
            set_value('rec_track','none')

@catch
def track_pressed(track):
    global redraw_tracks_lines,lock_frequency

    lock_frequency=False
    sweep_abort()
    play_stop()
    status_set_frequency()
    redraw_tracks_lines=True

try:
    VER_TIMESTAMP=Path(os.path.join(os.path.dirname(__file__),VERSION_FILE)).read_text(encoding='ASCII').strip()
except Exception as e_ver:
    print(e_ver)
    VER_TIMESTAMP=''

samplerate = 44100
#samplerate = 48000

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

fft_line_data_x=[0]*fft_points
fft_line_data_y=[0]*fft_points

for i_fft in range(fft_points):
    fft_line_data_x[i_fft]=i_fft * samplerate_by_fft_size

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
            print('unknown track:',track_to_record)

        show_track[recorded_track]=True

        show_press(sender,True,(recorded_track,False))

        #for track_temp in range(tracks):
        #    if track_temp==track:
        #        recording_enabled[track]=True
        #        configure_item(f'recordcheck{track}',texture_tag=ico["rec_on"])
        #    else:
        #        recording_enabled[track_temp]=False
        #        configure_item(f'recordcheck{track_temp}',texture_tag=ico["rec_off"])

        #recorded_track=track

        bind_item_theme(f"track{recorded_track}",reddark_line_theme)

@catch
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
            print('unknown window:',fft_window_name)

    window_correction = np_sum(fft_window)
    configure_item("fft_line", show=fft_on)

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

    set_value("dev_out_samplerate",str(int(device_out_current['default_samplerate'])))

    dev_out_channell_changed()

device_in_current=None

@catch
def dev_in_changed(sender=None, app_data=None):
    print('dev_in_changed',sender, app_data)

    global device_in_current

    dev_name=get_value("dev_in")

    device_in_current=[device for device in devices if device['name']==dev_name][0]

    dev_in_channell_values=['all'] + [str(val) for val in range(1,device_in_current['max_input_channels']+1)]
    configure_item("dev_in_channell",items=dev_in_channell_values)

    dev_in_channell_value=get_value("dev_in_channell")

    if not dev_in_channell_value or dev_in_channell_value not in dev_in_channell_values:
        dev_in_channell_value='all'
        set_value("dev_in_channell",dev_in_channell_value)

    set_value("dev_in_samplerate",str(int(device_in_current['default_samplerate'])))

    dev_in_channell_changed()

def on_click_plot(sender, app_data):
    print('on_click',sender, app_data)

    hide_info()

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
                f_current=x
                status_set_frequency()
                change_f(f_current)

def create_theme(
    tag: str,
    *,
    window_bg,
    text,
    frame_bg,
    button,
    button_hovered,
    button_active,
    menubar_bg,
    popup_bg=None,
    child_bg=None,
    border=(0, 0, 0, 50),
    slider_grab=(128, 128, 128),
    check_mark=(50, 150, 255),
    title_bg=None,
    title_bg_active=None,
    drag_drop_target=(200, 200, 80, 60),
    dock_bg=None,
    rounding=(4, 8, 4),  # (frame, window, child)
    frame_padding=(6, 6),
    item_spacing=(8, 6),
):
    """
    Tworzy kompletny theme obejmujący: mvAll + mvMenuBar + mvMenu + mvFileDialog + mvPopup + mvTooltip + wybrane widgety.
    """
    popup_bg = popup_bg or frame_bg
    child_bg = child_bg or window_bg
    title_bg = title_bg or window_bg
    title_bg_active = title_bg_active or window_bg
    dock_bg = dock_bg or window_bg

    with dpg.theme(tag=tag):
        # ---------- Global (mvAll) ----------
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, _rgba(window_bg))
            dpg.add_theme_color(dpg.mvThemeCol_Text, _rgba(text))
            dpg.add_theme_color(dpg.mvThemeCol_Border, _rgba(border))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, _rgba(frame_bg))
            #dpg.add_theme_color(dpg.mvThemeCol_Button, _rgba(button))
            dpg.add_theme_color(dpg.mvThemeCol_Button, _rgba(window_bg))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, _rgba(button_hovered))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, _rgba(button_active))
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, _rgba(title_bg))
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, _rgba(title_bg_active))
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, _rgba(popup_bg))
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, _rgba(child_bg))
            dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, _rgba(menubar_bg))
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, _rgba(slider_grab))
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, _rgba(button_active))
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, _rgba(check_mark))
            dpg.add_theme_color(dpg.mvThemeCol_DockingEmptyBg, _rgba(dock_bg))
            dpg.add_theme_color(dpg.mvThemeCol_DragDropTarget, _rgba(drag_drop_target))

            #dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, rounding[0], category=dpg.mvThemeCat_Core)
            #dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, rounding[1], category=dpg.mvThemeCat_Core)
            #dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, rounding[2], category=dpg.mvThemeCat_Core)
            #dpg.add_theme_style(dpg.mvStyleVar_FramePadding, frame_padding[0], frame_padding[1])
            #dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, item_spacing[0], item_spacing[1])

            # Scrollbars (jedyny poprawny sposób w DPG 1.11+)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, _rgba(window_bg))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, _rgba(button))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, _rgba(button_hovered))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive, _rgba(button_active))

            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 0, 0, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 1, 1, category=dpg.mvThemeCat_Core)
            #dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 2, 2, category=dpg.mvThemeCat_Core)
            #dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 0, 0, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 0, category=dpg.mvThemeCat_Core)

        # ---------- MenuBar ----------
        with dpg.theme_component(dpg.mvMenuBar):
            dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, _rgba(menubar_bg))
            dpg.add_theme_color(dpg.mvThemeCol_Text, _rgba(text))
            dpg.add_theme_color(dpg.mvThemeCol_Border, _rgba(border))

        # ---------- Menu ----------
        with dpg.theme_component(dpg.mvMenu):
            dpg.add_theme_color(dpg.mvThemeCol_Header, _rgba(button))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, _rgba(button_hovered))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, _rgba(button_active))
            dpg.add_theme_color(dpg.mvThemeCol_Text, _rgba(text))

        # ---------- MenuItem ----------
        with dpg.theme_component(dpg.mvMenuItem):
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, _rgba(button_hovered))
            dpg.add_theme_color(dpg.mvThemeCol_Text, _rgba(text))

        # ---------- FileDialog ----------
        with dpg.theme_component(dpg.mvFileDialog):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, _rgba(window_bg))
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, _rgba(child_bg))
            dpg.add_theme_color(dpg.mvThemeCol_Text, _rgba(text))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, _rgba(frame_bg))
            dpg.add_theme_color(dpg.mvThemeCol_Button, _rgba(button))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, _rgba(button_hovered))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, _rgba(button_active))
            dpg.add_theme_color(dpg.mvThemeCol_Border, _rgba(border))
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, _rgba(popup_bg))
            dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, _rgba(menubar_bg))

        # ---------- Popup ----------
        #with dpg.theme_component(dpg.mvPopup):
        #    dpg.add_theme_color(dpg.mvThemeCol_PopupBg, _rgba(popup_bg))
        #    dpg.add_theme_color(dpg.mvThemeCol_Text, _rgba(text))
        #    dpg.add_theme_color(dpg.mvThemeCol_Border, _rgba(border))

        # ---------- Tooltip ----------
        with dpg.theme_component(dpg.mvTooltip):
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, _rgba(popup_bg))
            dpg.add_theme_color(dpg.mvThemeCol_Text, _rgba(text))
            dpg.add_theme_color(dpg.mvThemeCol_Border, _rgba(border))

        # ---------- Widgety często używane ----------
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, _rgba(button))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, _rgba(button_hovered))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, _rgba(button_active))

        with dpg.theme_component(dpg.mvInputText):
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, _rgba(frame_bg))
            dpg.add_theme_color(dpg.mvThemeCol_Text, _rgba(text))

        with dpg.theme_component(dpg.mvCheckbox):
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, _rgba(frame_bg))
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, _rgba(check_mark))
            dpg.add_theme_color(dpg.mvThemeCol_Text, _rgba(text))

        with dpg.theme_component(dpg.mvCombo):
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, _rgba(frame_bg))
            dpg.add_theme_color(dpg.mvThemeCol_Text, _rgba(text))
            dpg.add_theme_color(dpg.mvThemeCol_Button, _rgba(button))

        with dpg.theme_component(dpg.mvSliderFloat):
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, _rgba(frame_bg))
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, _rgba(slider_grab))
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, _rgba(button_active))


        # ---------- Table headers ----------
        #with dpg.theme_component(dpg.mvTableHeaderRow):
        #    dpg.add_theme_color(dpg.mvThemeCol_Header, _rgba(button))
        #    dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, _rgba(button_hovered))
        #    dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, _rgba(button_active))
        #    dpg.add_theme_color(dpg.mvThemeCol_Text, _rgba(text))

        with dpg.theme_component(dpg.mvTable):
            dpg.add_theme_color(dpg.mvThemeCol_Border, _rgba(border))
            dpg.add_theme_color(dpg.mvThemeCol_BorderShadow, _rgba((0, 0, 0, 0)))
            dpg.add_theme_color(dpg.mvThemeCol_TableHeaderBg, _rgba(button))
            #dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 6, 4)


        with dpg.theme_component(dpg.mvTable):
            dpg.add_theme_color(dpg.mvThemeCol_TableHeaderBg, _rgba(button))
            dpg.add_theme_color(dpg.mvThemeCol_Border, _rgba(border))
            dpg.add_theme_color(dpg.mvThemeCol_BorderShadow, (0, 0, 0, 0))
            #dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 6, 4)


    #THEME_TAGS[tag] = tag
    return tag

def _rgba(c):
    """Umożliwia podawanie kolorów jako (r,g,b) lub (r,g,b,a); domyślnie a=255."""
    if len(c) == 3:
        return (*c, 255)
    return c

temp=create_theme(
    "theme_windows_light",
    window_bg=(242, 242, 242),
    text=(10, 10, 10),
    frame_bg=(255, 255, 255),
    button=(230, 230, 230),
    button_hovered=(215, 215, 215),
    button_active=(200, 200, 200),
    menubar_bg=(235, 235, 235),
    popup_bg=(250, 250, 250),
    border=(0, 0, 0, 60),
    slider_grab=(130, 130, 130),
    check_mark=(0, 120, 215),
    title_bg=(242, 242, 242),
    title_bg_active=(230, 230, 230),
    rounding=(3, 6, 3),
)

with theme() as theme_light:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_Text, (20, 20, 20))
        dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (250, 250, 250))
        dpg.add_theme_color(dpg.mvThemeCol_Border, (210, 210, 210))
        dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (245, 245, 245))
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (230, 230, 230))
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (220, 220, 220))
        dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (240, 240, 240))
        dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (240, 240, 240))
        dpg.add_theme_color(dpg.mvThemeCol_Button, (240, 240, 240))
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (225, 225, 225))
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (210, 210, 210))
        dpg.add_theme_color(dpg.mvThemeCol_CheckMark, (0, 120, 215))   # Windows accent
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (0, 120, 215))
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (0, 100, 180))

        dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, (240, 240, 240))
        dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (240, 240, 240))
        dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (240, 240, 240))
        dpg.add_theme_color(dpg.mvThemeCol_DockingEmptyBg, (240, 240, 240))
        dpg.add_theme_color(dpg.mvThemeCol_DragDropTarget, (240, 240, 240))

        dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 0, 0, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 0, 0, category=dpg.mvThemeCat_Core)
        #dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 2, 2, category=dpg.mvThemeCat_Core)
        #dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 0, 0, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 0, category=dpg.mvThemeCat_Core)

    with dpg.theme_component(dpg.mvSliderFloat):
        dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (240, 240, 240))
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (240, 240, 240))
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (240, 240, 240))

    with dpg.theme_component(dpg.mvCombo):
        dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (240, 240, 240))
        dpg.add_theme_color(dpg.mvThemeCol_Text, (240, 240, 240))
        dpg.add_theme_color(dpg.mvThemeCol_Button, (240, 240, 240))

with theme() as theme_win_shapes:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 8)
        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
        dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 6)
        dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 6)
        dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 6)
        dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 6)
        dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 6)

        dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 1)
        dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 1)
        dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 6)
        dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 12, 10)


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

with theme() as padding_mod_theme:
    with theme_component(dpg.mvAll):
        dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 0, 0, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 0, 0, category=dpg.mvThemeCat_Core)
        #dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 2, 2, category=dpg.mvThemeCat_Core)
        #dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 0, 0, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 0, category=dpg.mvThemeCat_Core)

log_bucket_width=logf_max_audio_m_logf_min_audio/spectrum_buckets_quant
log_bucket_width_by2=log_bucket_width*0.5

bucket_freqs=[0]*spectrum_buckets_quant
bucket_edges=[0]*(spectrum_buckets_quant+1)

for b in range(spectrum_buckets_quant):
    bucket_freqs[b]= 10**(logf_min_audio + log_bucket_width_by2 + log_bucket_width * b)
    bucket_edges[b+1]= 10**(logf_min_audio + log_bucket_width * (b+1))

#bucket_freqs=tuple(bucket_freqs)
#print('bucket_freqs:',bucket_freqs)
#print('bucket_edges:',bucket_edges)

bin_indices = digitize(fft_line_data_x, bucket_edges)
#print('bin_indices:',bin_indices)
bin_counts = bincount(bin_indices)

prev_ind=-1
for f,ind in zip(fft_line_data_x,bin_indices):
    if prev_ind!=ind:
        prev_ind=ind
    else:
        border=ind
        border_f=f
        break

print(f'\n{border=}\n{border_f=}\n')

fft_line_data_x_border_index=0
for i,f in enumerate(fft_line_data_x):
    if f<border_f:
        continue
    else:
        fft_line_data_x_border_index=i
        break

bucket_freqs_border_index=0
for i,f in enumerate(bucket_freqs):
    if f>=border_f:
        bucket_freqs_border_index=i
        break

print(f'\n{fft_line_data_x_border_index=} / {len(fft_line_data_x)}\n{bucket_freqs_border_index=} / {len(bucket_freqs)}\n')

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

def slide_change(sender):
    val=dpg.get_value(sender)
    dpg.set_axis_limits("y_axis", dbmin_display*val/100, dbmax_display)

dpg.bind_theme(padding_mod_theme)
#dpg.bind_theme(theme_light)
dpg.bind_theme(temp)
dpg.create_viewport(title=title,width=1000,height=380,vsync=True)

def on_viewport_resize(sender=None, app_data=None):

    vh = dpg.get_viewport_client_height()
    vw = dpg.get_viewport_client_width()

    FIXED_BOTTOM_HEIGHT = 44
    GAP=100
    top_h  = max(220, vh - FIXED_BOTTOM_HEIGHT - GAP)

    dpg.set_item_height('slider', top_h-40)
    dpg.set_item_height('slider_window', top_h-40+8)
    #dpg.set_item_width('slider', 60)

    dpg.set_item_height('plot', top_h)
    dpg.set_item_width('plot', vw-80)

    #dpg.set_item_pos('info', (100,12))

    #dpg.set_item_height('info', top_h-40)
    #dpg.set_item_width('info', vw-30)
    #dpg.set_item_width('info_text', vw-30)

with dpg.theme() as window_theme_1:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (247,247,247,180), category=dpg.mvThemeCat_Core)

###################################################
with window(tag='main') as main:
    with dpg.table(header_row=False, resizable=False, policy=dpg.mvTable_SizingStretchProp,
        borders_innerH=False, borders_innerV=False, borders_outerH=False, borders_outerV=False,
        row_background=False, context_menu_in_body=False, freeze_rows=0, freeze_columns=0,
        no_host_extendX=False, no_host_extendY=False, pad_outerX=False, no_pad_outerX=True):

        add_table_column(width_stretch=True, init_width_or_weight=-1)

        with dpg.table_row():
            with dpg.group(horizontal=True):
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

                    with dpg.plot_axis(dpg.mvXAxis, tag='x_axis') as xaxis:
                        configure_item(dpg.last_item(),scale=dpg.mvPlotScale_Log10)
                        dpg.set_axis_limits("x_axis", fmin,fmax)
                        dpg.set_axis_ticks("x_axis", xticks)

                    with dpg.plot_axis(dpg.mvYAxis, tag = 'y_axis'):
                        dpg.set_axis_limits("y_axis", dbmin_display, dbmax_display)
                        dpg.set_axis_ticks("y_axis", yticks)

                        add_line_series(fft_line_data_x, fft_line_data_y, tag="fft_line",label='FFT', user_data='FFT')

                        add_line_series((0,0),(dbmin,0),tag="cursor_f")
                        bind_item_theme("cursor_f",red_line_theme)

                        for lab,val in xticks:
                            if lab:
                                add_line_series([val,val], [-130,0],tag=f'stick{val}')
                                bind_item_theme(f'stick{val}',grid_line_theme)

                        for track in range(tracks):
                            add_line_series(bucket_freqs, track_line_data_y[track], tag=f"track{track}",label=f"track{track+1}",user_data=track,show=False)

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

                    #with window(tag='info',height =-1,no_close=True,menubar=False,no_title_bar=True,autosize=True) as moving_frame:
                    #    add_text(tag='info_text',default_value='text1')
                    #    dpg.bind_item_theme(moving_frame,window_theme_1)

                    #dpg.set_item_pos('info', (300,13))
                    #dpg.hide_item('info')

        with dpg.table_row():
            with dpg.table(header_row=False, resizable=False, policy=dpg.mvTable_SizingStretchProp,
                borders_innerH=False, borders_innerV=False, borders_outerH=False, borders_outerV=False,
                row_background=False, context_menu_in_body=False, freeze_rows=0, freeze_columns=0,
                no_host_extendX=False, no_host_extendY=False, pad_outerX=False, no_pad_outerX=True):

                add_table_column(width_fixed=True, init_width_or_weight=10, width=10)
                add_table_column(width_stretch=True, init_width_or_weight=-1)
                add_table_column(width_fixed=True, init_width_or_weight=230, width=230)

                with dpg.table_row():
                    dpg.add_spacer(height=6)

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
        with dpg.table_row():
            with dpg.table(header_row=False, resizable=False, policy=dpg.mvTable_SizingStretchProp,
                borders_innerH=False, borders_innerV=False, borders_outerH=False, borders_outerV=False,
                row_background=False, context_menu_in_body=False, freeze_rows=0, freeze_columns=0,
                no_host_extendX=False, no_host_extendY=False, pad_outerX=False, no_pad_outerX=True):

                add_table_column(width_fixed=True, init_width_or_weight=6, width=6)
                add_table_column(width_fixed=True, init_width_or_weight=30, width=30)
                add_table_column(width_fixed=True, init_width_or_weight=140, width=140)
                add_table_column(width_fixed=True, init_width_or_weight=100, width=100)
                add_table_column(width_stretch=True, init_width_or_weight=-1)
                add_table_column(width_stretch=True, init_width_or_weight=-1)
                #add_table_column(width_fixed=True, init_wi4th_or_weight=200, width=200)
                add_table_column(width_fixed=True, init_width_or_weight=6, width=6)

                with dpg.table_row():
                    add_text(default_value='')
                    with dpg.group(width=-1):
                        add_text(default_value='API')
                        add_text(default_value='')
                        add_text(default_value='FFT')
                        add_text(default_value='REC')
                    with dpg.group(width=-1):
                        add_combo(tag='api',default_value='',callback=api_changed)
                        add_text(default_value='')
                        add_combo(tag='fft_window',items=['off','ones','hanning','hamming','blackman','bartlett'],default_value='blackman',callback=fft_window_changed)
                        widget_tooltip(' Show live Fast Fourier Transform graph \n with window function specified')

                        with dpg.table(header_row=False, resizable=False, policy=dpg.mvTable_SizingStretchProp,
                            borders_innerH=False, borders_innerV=False, borders_outerH=False, borders_outerV=False,
                            row_background=False, context_menu_in_body=False, freeze_rows=0, freeze_columns=0,
                            no_host_extendX=False, no_host_extendY=False, pad_outerX=False, no_pad_outerX=True):

                            add_table_column(width_fixed=True, init_width_or_weight=16, width=16)
                            add_table_column(width_stretch=True, init_width_or_weight=-1)

                            with dpg.table_row():
                                add_image_button(ico["reset"],tag=f'resetrack',callback=resetrack_press,label="X")
                                widget_tooltip(' Reset selected track samples.')
                                add_combo(tag='rec_track',items=['none','1','2','3','4','5','6','7','8'],default_value='none',callback=record_track_changed,width=-1)

                    with dpg.group():
                        add_text(default_value=' ')
                        add_text(default_value='Device:')
                        add_text(default_value='Channells:')
                        add_text(default_value='Samplerate:')
                    with dpg.group(width=-1):
                        add_text(default_value='Output')
                        add_combo(tag='dev_out',default_value='',callback=dev_out_changed)
                        add_combo(tag='dev_out_channell',default_value='',callback=dev_out_channell_changed)
                        add_text(tag='dev_out_samplerate',label='')
                    with dpg.group(width=-1):
                        add_text(default_value='Input')
                        add_combo(tag='dev_in',default_value='',callback=dev_in_changed)
                        add_combo(tag='dev_in_channell',default_value='',callback=dev_in_channell_changed)
                        add_text(tag='dev_in_samplerate',label='')
                    with dpg.group():
                        dpg.add_spacer(width=6)


    with dpg.handler_registry():
        dpg.add_mouse_release_handler(callback=on_release)
        dpg.add_mouse_wheel_handler(callback=wheel_callback)
        dpg.add_key_press_handler(callback=key_callback)

APP_FILE = normpath(__file__)
APP_DIR = dirname(APP_FILE)

dpg.set_viewport_small_icon(Path(path_join(APP_DIR,"./icons/sas_small.png")))
dpg.set_viewport_large_icon(Path(path_join(APP_DIR,"./icons/sas.png")))

dpg.set_primary_window(main, True)
dpg.set_viewport_resize_callback(callback=on_viewport_resize)
dpg.setup_dearpygui()
dpg.show_viewport()

on_viewport_resize()

########################################################################

try:
    distro_info=Path(path_join(APP_DIR,'distro.info.txt')).read_text(encoding='utf-8')

except Exception as exception_1:
    print(exception_1)
    distro_info = 'Error. No distro.info.txt file.'

distro_info+= "\nnumpy       " + str(numpy_version) + "\nsounddevice " + str(sounddevice_version) + "\n\nDearPyGui   " + str(dpg.get_dearpygui_version()) + "\n\n"

print(f'distro info:\n{distro_info}')

sweeping=False

stream_in=None
stream_out=None

refresh_devices()


api_changed()

settings_wrapper()

fft_on=True

fft_window_changed()

data=zeros(fft_size)
next_sweep_time=0

#fft_line_new_x=tuple(fft_line_data_x[1:fft_line_data_x_border_index] + bucket_freqs[bucket_freqs_border_index:])
fft_line_new_x=fft_line_data_x[:fft_line_data_x_border_index] + bucket_freqs[bucket_freqs_border_index:]
fft_line_new_x[0]=5
fft_line_new_x=tuple(fft_line_new_x)

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
                play_stop()

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
            set_value("fft_line", [fft_line_new_x, np_concatenate([array([-120.0]),fft_values[1:fft_line_data_x_border_index],fft_values_means_in_buckets[bucket_freqs_border_index:]]) ])
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
    if now >= next_fps:
        set_status(f'FPS:{frames}, {rec_callbacks=}, {rec_samples=}')
        frames = 0
        rec_callbacks = 0
        rec_samples = 0
        next_fps = now+1.0
    ##################################

    if exiting:
        break

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
sys_exit(0)

