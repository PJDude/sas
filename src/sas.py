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

from dearpygui.dearpygui import get_plot_mouse_pos,set_value,get_value,bind_item_theme,item_handler_registry,plot,add_line_series,add_scatter_series,theme,configure_item,render_dearpygui_frame,is_dearpygui_running,destroy_context,theme_component,add_item_clicked_handler,add_item_deactivated_handler,add_item_hover_handler,bind_item_handler_registry,add_mouse_release_handler,handler_registry,add_combo,child_window,table_row,add_checkbox,add_button

import time

from threading import Thread
from time import sleep

import numpy as np
from numpy import mean as np_mean,square as np_square,float32,ones,hanning,hamming,blackman,bartlett, abs as np_abs,fft as np_fft,log10 as np_log10,__version__ as numpy_version, concatenate as np_concatenate
from sounddevice import Stream,InputStream,OutputStream,query_devices,default as sd_default,query_hostapis,__version__ as sounddevice_version
from collections import deque
from queue import Queue

from math import pi, sin, log10, ceil, floor
from PIL import ImageGrab, ImageTk, Image

from pathlib import Path
from time import strftime, localtime

import os
from os import name as os_name, system
from os.path import join as path_join, normpath,dirname

from sys import exit as sys_exit

from images import image
from dialogs import *

VERSION_FILE='version.txt'

HOMEPAGE='https://github.com/PJDude/sas'

windows = bool(os_name=='nt')

ImageGrab_grab=ImageGrab.grab
np_fft_rfft=np_fft.rfft

blocksize_out = 128
blocksize_in = 128

fft_size = blocksize_in*8
fft_points=int(fft_size/2+1)

def canvas_itemconfig(*args,**kwargs):
    print('TODO canvas_itemconfig',*args,**kwargs)

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
    res_list = [str(round(f_current))+ ' Hz (']
    res_list_append = res_list.append
    if current_bucket<spectrum_buckets_quant:
        for track in sorted(visible_tracks):
            db_temp = round(spectrum_buckets[track][current_bucket])
            res_list_append(str(track+1) + ':' + str(db_temp))
    else:
        print(f'{current_bucket=}')

    res_list_append(') [#buffer:dBFS]')
    set_value('status',' '.join(res_list))

def recording_start():
    global recording
    recording=True

record_after=None

#@catch
#def on_mouse_press_1(event):
#    global sweeping,record_after,lock_frequency
#    sweeping=False

#    if lock_frequency:
#        lock_frequency=False
#        play_stop()
#        on_mouse_move_old(event)
#    else:
#        play_start()
#        status_set_frequency()

#        record_after=root_after(200,recording_start)

#@catch
#def on_mouse_press_3(event):
#    global sweeping,record_after,lock_frequency
#    sweeping=False

#    if lock_frequency:
#        lock_frequency=False
#       play_stop()
#        on_mouse_move_old(event)
#    else:
#        on_mouse_move_old(event)
#        lock_frequency=True

#        play_start()
#        status_set_frequency()

#        record_after=root_after(200,recording_start)

#@catch
#def on_mouse_release_1(event):
#    global recording,sweeping,lock_frequency
#    root_after_cancel(record_after)
#    lock_frequency=False

#    recording=False
#    update_tracks_buttons()
#    sweeping=False

#    play_stop()
#    status_set_frequency()

#catch
#def on_mouse_release_3(event):
#    global recording,sweeping
#    root_after_cancel(record_after)

#    recording=False
#    update_tracks_buttons()
#    sweeping=False

@catch
def on_mouse_scroll_win(event):
    fmod = int(-1 * (event.delta/120))
    scroll_mod(fmod)

@catch
def on_mouse_scroll_lin(event):
    if event.num == 4:
        fmod = -1
    elif event.num == 5:
        fmod = 1
    else:
        return

    scroll_mod(fmod)

@catch
def scroll_mod(mod,factor=0.01):
    if lock_frequency:
        global f_current
        if mod>0:
            f_new = ceil(f_current*(1.0+factor))
        else:
            f_new = floor(f_current*(1.0-factor))

        if f_new>0:
            f_new=log10(f_new)
            if f_min_audio<f_new<f_max_audio:
                change_f(f_new)
                status_set_frequency()
                f_current=f_new

@catch
def save_csv():
    time_postfix=strftime('%Y_%m_%d_%H_%M_%S',localtime())
    filename = asksaveasfilename(title = "Save CSV",initialfile = f'sas_{time_postfix}.csv',defaultextension=".csv",filetypes=[("All Files","*.*"),("CSV Files","*.csv")])

    if filename:
        try:
            with open(filename,'w',encoding='utf-8') as f:
                f.write("# Created with " + title + " #\n")
                f.write("frequency[Hz],level[dBFS]\n")
                for i,db in enumerate(spectrum_buckets[current_track]):
                    logf=bucket_to_logf(i)
                    f.write(f"{round(100*(10**logf))/100},{round(1000*db)/1000}\n")
        except Exception as e:
            print("save_csv_error:",e)

@catch
def load_csv():
    filename = askopenfilename(title = "Load CSV",initialfile = 'sas*.csv',defaultextension=".csv",filetypes=[("CSV Files","*.csv"),("All Files","*.*")])

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
                            spectrum_buckets[current_track][bucket]=float_db
                            track_line_data_y[current_track][bucket]=float_db
                        else:
                            print("wrong db value:",float_db)
                            continue

        except Exception as e:
            print("Load_csv_error:",e)

        global redraw_tracks_lines,redraw_fft_line
        redraw_tracks_lines=True
        redraw_fft_line=True

@catch
def save_image():
    time_postfix=strftime('%Y_%m_%d_%H_%M_%S',localtime())
    filename = asksaveasfilename(title = "Save Image",initialfile = f'sas_{time_postfix}.png',defaultextension=".png",filetypes=[("All Files","*.*"),("PNG Files","*.png")])

    if filename:
        if os.path.exists(filename):
            print("Name already exists!")
        else:
            path, file = os.path.split(filename)
            name, ext = os.path.splitext(file)

            if ext.lower() in ['.gif', '.png']:
                no_update=True

                x1 = root.winfo_rootx() + canvas.winfo_x()
                y1 = root.winfo_rooty() + canvas.winfo_y()
                x2 = x1 + canvas_width
                y2 = y1 + canvas_height

                canvas_itemconfig('cursor', state='hidden')
                canvas_itemconfig('cursor_freq', state='hidden')

                canvas_itemconfig('cursor_db', state='hidden')
                canvas_itemconfig('cursor_db_text', state='hidden')

                root.lift()
                root.attributes('-topmost', True)

                x_offset=72
                y_offset=4
                text="Created with " + title

                for x,y in ((x_offset-1, y_offset-1),
                            (x_offset-1, y_offset),
                            (x_offset-1, y_offset+1),
                            (x_offset+1, y_offset-1),
                            (x_offset+1, y_offset),
                            (x_offset+1, y_offset+1),
                            (x_offset, y_offset-1),
                            (x_offset, y_offset+1)):
                    canvas_create_text(x, y, text=text, anchor="nw", font=("Arial", 8), fill=bg_color,tags='mark')

                canvas_create_text(x_offset, y_offset, text=text, anchor="nw", font=("Arial", 8), fill="black",tags='mark')

                ###################################
                #root_update()
                #root_update_idletasks()
                #root_after(200)

                ImageGrab_grab().crop((x1, y1, x2, y2)).save(filename)
                canvas_delete('mark')

                canvas_itemconfig('cursor', state='normal')
                canvas_itemconfig('cursor_db', state='normal')
                canvas_itemconfig('cursor_db_text', state='normal')

                #update_tracks_buttons()

                global redraw_tracks_lines,redraw_fft_line
                redraw_tracks_lines=True
                redraw_fft_line=True

                change_f(current_f)

                root.attributes('-topmost', False)
                ###################################
            else:
                print("Unknown file type")
    else:
        print("Cancel")

def logf_to_bucket(logf):
    return int(floor(scale_factor_logf_to_bucket * (logf - logf_min_audio)))

def bucket_to_logf(i):
    return (i+0.5)/scale_factor_logf_to_bucket + logf_min_audio

phase_step=1.0

def change_f(fpar):
    global current_logf,current_bucket,phase_step,current_bucket,two_pi_by_samplerate

    current_logf=log10(fpar)
    current_f=fpar
    current_bucket=logf_to_bucket(current_logf)
    if current_bucket>=spectrum_buckets_quant:
       current_bucket= spectrum_buckets_quant-1

    set_value("cursor_f", ((fpar,fpar), (0,dbmin)))

    phase_step = two_pi_by_samplerate * fpar

    #TODO
    #canvas_delete('cursor_freq')
    #canvas_create_text(x+2, 2, text=str(round(fpar))+"Hz", anchor="nw", font=("Arial", 8), fill="black",tags='cursor_freq')

    #set_value('api',apis[default_api_nr]['name'])

played_bucket=0
played_bucket_callbacks=0

def audio_output_callback(outdata, frames, time, status):
    global phase,stream_out_state,played_bucket,played_bucket_callbacks,phase_step,two_pi,current_bucket,out_channell_buffer_mod_index

    if stream_out_state:
        for i in range(blocksize_out):
            outdata[i,out_channell_buffer_mod_index]=sin(phase)
            phase = (phase+phase_step) % two_pi

        if stream_out_state==1:
            stream_out_state=2
            for i in range(blocksize_out):
                outdata[i,out_channell_buffer_mod_index]*=volume_ramp[i]
        elif stream_out_state==-1:
            stream_out_state=0
            for i in range(blocksize_out):
                outdata[i,out_channell_buffer_mod_index]*=volume_ramp[blocksize_out_m1-i]

        if current_bucket!=played_bucket:
            played_bucket_callbacks=1
            played_bucket=current_bucket
        else:
            played_bucket_callbacks+=1
    else:
        outdata.fill(0)

@catch
def sweep(sender=None, app_data=None):
    global recording,sweeping,fft_on,rec_on,redraw_fft_line,lock_frequency,redraw_tracks_lines
    lock_frequency=False

    prev_fft=fft_on
    fft_on=False
    redraw_fft_line=True
    fft_set()

    rec_on=True
    recording=True

    track_auto_enable()
    #update_tracks_buttons()

    redraw_tracks_lines=True

    play_stop()

    change_f(f_min_audio)
    logf_sweep_step=logf_max_audio_m_logf_min_audio/sweep_steps

    sweeping=True

    play_start()
    for i in range(sweep_steps):
        logf=logf_min_audio+i*logf_sweep_step
        f=10**logf
        change_f(f)
        set_value('status','Sweeping (' + str(round(f))+ ' Hz), Click on the graph to abort ...')

        #root_update()
        #root_after(sweeping_delay)
        sleep(sweeping_delay)

        if not sweeping:
            break

    sweeping=False
    set_value('status','Sweeping done.')

    play_stop()

    recording=False

    fft_on=prev_fft
    redraw_fft_line=True
    fft_set()

@catch
def play_start():
    global stream_out_state
    bind_item_theme("cursor_f",red_line_theme)
    stream_out_state=1

@catch
def play_stop():
    global stream_out_state
    if stream_out_state==2:
        stream_out_state=-1

    bind_item_theme("cursor_f",white_line_theme)

@catch
def play_abort():
    global stream_out_state

    bind_item_theme("cursor_f",white_line_theme)
    stream_out_state=0

exiting=False

current_sample_db=-120

samples_chunks_fifo=Queue(maxsize=fft_size*20)
samples_chunks_fifo_put=samples_chunks_fifo.put
samples_chunks_fifo_get=samples_chunks_fifo.get

###########################################################
def audio_input_processing_thread():
    global redraw_fft_line,current_sample_db,rec_on,current_track,current_bucket,redraw_tracks_lines,current_sample_modified,fft_window,fft_size,fft_on,lock_frequency,fft_line_data_y,exiting,recording,track_line_data_y

    try:
        chunks=128
        data_fifo_chunks = deque(maxlen=chunks)
        data_fifo_chunks_append=data_fifo_chunks.append

        while True:
            chunk=samples_chunks_fifo_get()

            data_fifo_chunks_append(chunk)
            data=np_concatenate(data_fifo_chunks)

            if exiting:
                sys_exit(0)

            #record_blocks_len/record_blocks_len_short

            if len(data) > fft_size:
                current_sample_db = 10 * log10( np_mean(np_square(data[-fft_size:])) + 1e-12)
            else:
                current_sample_db=-119
            current_sample_modified=True

            if recording or lock_frequency:
                if rec_on:
                    if current_track is not None:
                        spectrum_buckets[current_track][current_bucket]=current_sample_db

                        if played_bucket_callbacks>record_blocks_len:
                            track_line_data_y[current_track][current_bucket]=current_sample_db
                        else:
                            track_line_data_y[current_track][current_bucket]=( track_line_data_y[current_track][current_bucket]*record_blocks_len_part1 + current_sample_db*record_blocks_len_part2 ) / record_blocks_len
                            #track_line_data_y[current_track][current_bucket]=current_sample_db

                        redraw_tracks_lines=True

            if fft_on:
                if len(data) > fft_size:
                    if not redraw_fft_line:
                        fft_line_data_y = 20*np_log10( np_abs( (np_fft_rfft( data[-fft_size:]*fft_window))[0:fft_points] ) / fft_size + 1e-12)

                        #for val in fft_line_data_y:
                        #    print(val)
                        #print(fft_line_data_y)
                        #print('\n')
                        redraw_fft_line=True

    except Exception as e:
        print("audio_input_processing_thread ERROR:",e)
        exiting=True

    sys_exit(0)

###########################################################
def audio_input_callback(indata, frames, time_info, status):
    if status:
        print(status)
        return

    samples_chunks_fifo_put(indata[:, 0])

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
        #out_channell_buffer_mod_index=int(dev_out_channell_var.get())-1
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
        stream_out = OutputStream( samplerate=samplerate, channels=device_out_channels_stream_option, dtype="float32", blocksize=blocksize_out, callback=audio_output_callback, latency="low",device=device_out_current['index'] )
    except Exception as e:
        messagebox.showerror("dev_out_channell_config",str(e))
    else:
        stream_out.start()


@catch
def dev_in_channell_changed(sender=None, app_data=None):
    print('dev_in_channell_changed',sender,app_data)

    global device_in_channels_stream_option,in_channell_buffer_mod_index,lock_frequency,stream_in,device_in_current

    if stream_in:
        stream_in.stop()

    try:
        in_channell_buffer_mod_index=int(get_value("dev_in_channell"))-1
        device_in_channels_stream_option=device_in_current['max_input_channels']
    except:
        device_in_channels_stream_option=1
        in_channell_buffer_mod_index=0

    dev_in_channell_config()

@catch
def dev_in_channell_config():
    global stream_in,device_in_current,device_in_channels_stream_option

    try:
        stream_in = InputStream( samplerate=samplerate, channels=device_in_channels_stream_option, dtype="float32", blocksize=blocksize_in, callback=audio_input_callback, latency="low",device=device_in_current['index'] )
    except Exception as e:
        messagebox.showerror("dev_in_channell_config",str(e))
    else:
        stream_in.start()

about_dialog_created = False
def get_about_dialog():
    global about_dialog_created,about_dialog

    if not about_dialog_created:

        about_dialog = GenericDialog(root,main_icon_tuple,bg_color,'',pre_show=pre_show,post_close=post_close)

        frame1 = LabelFrame(about_dialog.area_main,text='',bd=2,bg=bg_color,takefocus=False)
        frame1.grid(row=0,column=0,sticky='news',padx=4,pady=(4,2))

        about_dialog.area_main.grid_rowconfigure(1, weight=1)

        text= f'\n\nSimple Audio Sweeper {VER_TIMESTAMP}\nAuthor: Piotr Jochymek\n\n{HOMEPAGE}\n\nPJ.soft.dev.x@gmail.com\n\n'

        Label(frame1,text=text,bg=bg_color,justify='center').pack(expand=1,fill='both')

        frame2 = LabelFrame(about_dialog.area_main,text='',bd=2,bg=bg_color,takefocus=False)
        frame2.grid(row=1,column=0,sticky='news',padx=4,pady=(2,4))

        lab_courier = Label(frame2,text='\n' + distro_info + '\n',bg=bg_color,justify='left')
        lab_courier.pack(expand=1,fill='both')

        try:
            lab_courier.configure(font=('Courier', 10))
        except:
            try:
                lab_courier.configure(font=('TkFixedFont', 10))
            except:
                pass

        about_dialog_created = True

    return about_dialog

@catch
def about_wrapper():
    get_about_dialog().show()

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

license_dialog_created=False
def get_license_dialog():
    global license_dialog, license_dialog_created

    if not license_dialog_created:
        try:
            license_txt=Path(path_join(APP_DIR,'LICENSE')).read_text(encoding='ASCII')
        except Exception as exception_lic:
            print(exception_lic)
            try:
                license_txt=Path(path_join(dirname(APP_DIR),'LICENSE')).read_text(encoding='ASCII')
            except Exception as exception_2:
                print(exception_2)
                sys_exit()

        license_dialog = GenericDialog(root,(ico['license'],ico['license']),bg_color,'',pre_show=pre_show,post_close=post_close,min_width=700,min_height=400)

        frame1 = LabelFrame(license_dialog.area_main,text='',bd=2,bg=bg_color,takefocus=False)
        frame1.grid(row=0,column=0,sticky='news',padx=4,pady=4)
        license_dialog.area_main.grid_rowconfigure(0, weight=1)

        lab_courier=Label(frame1,text=license_txt,bg=bg_color,justify='center')
        lab_courier.pack(expand=1,fill='both')

        try:
            lab_courier.configure(font=('Courier', 10))
        except:
            try:
                lab_courier.configure(font=('TkFixedFont', 10))
            except:
                pass

        license_dialog_created = True

    return license_dialog

def license_wrapper():
    get_license_dialog().show()

@catch
def rec_toggle(sender=None, app_data=None):
    global rec_on,redraw_tracks_lines

    rec_on=(True,False)[rec_on]

    redraw_tracks_lines=True
    track_auto_enable()
    #update_tracks_buttons()

@catch
def fft_toggle():
    global fft_on,redraw_fft_line,sweeping
    #fft_on=(True,False)[fft_on]
    fft_on=get_value('fft')
    print('fft_toggle:',fft_on)

    sweeping=False

    fft_set()
    fft_window_changed()

    redraw_fft_line=True

fft_on=True

@catch
def fft_set():
    set_value("fft",fft_on)
    configure_item("fft_line", show=fft_on)

@catch
def flatline(sender=None, app_data=None):
    global redraw_tracks_lines,current_track

    if current_track is not None:
        spectrum_buckets[current_track]=[dbinit]*spectrum_buckets_quant

        for i in range(spectrum_buckets_quant):
            track_line_data_y[current_track][i]=dbinit

        redraw_tracks_lines=True

def trackbutton_press(sender=None, app_data=None,track=None):
    print('trackbutton_press:',sender,app_data,track)

    track_pressed(track)

    global visible_tracks
    if app_data:
        visible_tracks.add(track)
    else:
        visible_tracks.discard(track)

@catch
def KeyPress(event):
    control_pressed=bool('Control' in str(event))

    try:
        track=int(event.keysym)-1
        if control_pressed:
            global rec_on
            rec_on=True

    except Exception as e_kp2:
        if event.keysym=="Left":
            scroll_mod(-1,0.001)
        elif event.keysym=="Down":
            scroll_mod(-1,0.0001)
        elif event.keysym=="Right":
            scroll_mod(1,0.001)
        elif event.keysym=="Up":
            scroll_mod(1,0.0001)
        else:
            pass
    else:
        if track in range(tracks):
            track_pressed(track)

@catch
def track_auto_enable():
    global current_track,visible_tracks,redraw_tracks_lines

    if not visible_tracks:
        set_value('track0',True)
        visible_tracks.add(0)

    if current_track is None:
        current_track=next(iter(visible_tracks))

    redraw_tracks_lines=True

@catch
def track_pressed(track):
    global current_track,visible_tracks,redraw_tracks_lines,sweeping,lock_frequency,rec_on

    lock_frequency=False
    sweeping=False

    try:
        prev_current_track=current_track

        #if control_pressed:
        #    rec_on=True

        #    visible_tracks.add(track)
        #    current_track=track

        if track in visible_tracks:
            visible_tracks.remove(track)
        else:
            visible_tracks.add(track)
            current_track=prev_current_track

        if current_track in visible_tracks:
            pass
        elif visible_tracks:
            current_track=next(iter(visible_tracks))
        else:
            current_track=None
            rec_on=False

        #recording=False
        play_stop()

        redraw_tracks_lines=True
        status_set_frequency()

    except Exception as e_kp:
        print("track_pressed:",track, e_kp)

f_current=0
tracks=8
stream_out_state=0
'''
2 - on
1 - ramp on
0 - off
-1 - ramp off
'''
lock_frequency=False

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

current_track=None
visible_tracks=set()

two_pi = pi+pi
two_pi_by_samplerate = two_pi/samplerate

spectrum_buckets_quant=256
spectrum_sub_bucket_samples=4
sweep_steps=spectrum_buckets_quant*spectrum_sub_bucket_samples

logf_max_m_logf_min = logf_max-logf_min
logf_max_audio_m_logf_min_audio = logf_max_audio-logf_min_audio

scale_factor_logf_to_bucket=spectrum_buckets_quant/logf_max_audio_m_logf_min_audio

current_bucket=logf_to_bucket(current_logf)
#current_bucket_x2=current_bucket+current_bucket

dbmin=-122.0
dbmin_display=-123.0
dbinit=dbmin
dbmax_display=dbmax=0.0

dbrange=dbmax-dbmin

spectrum_buckets=[ [dbinit]*spectrum_buckets_quant for i in range(tracks) ]

dbrange_display=dbmax_display-dbmin_display

canvas_height=1
canvas_width=1

samplerate_by_fft_size = samplerate / fft_size

blocksize_out_m1=blocksize_out-1

volume_ramp = tuple([(i+1.0)/blocksize_out for i in range(blocksize_out)])

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

#record_blocks=[0]*record_blocks_len

#record_blocks_short=[0]*record_blocks_len_short

redraw_tracks_lines=True
redraw_fft_line=True
current_sample_modified=True

title=f"Simple Audio Sweeper {VER_TIMESTAMP}"

dpg.create_context()
dpg.create_viewport(title=title, width=1100, height=520)

#print('dearpygui_version:',dpg.get_dearpygui_version())



#POINTS=64

#x_data = np.arange(POINTS, dtype=np.float32)
#y_data = np.zeros(POINTS, dtype=np.float32)

spectrum_line_color={}
spectrum_line={}

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
                #dev_out_name_var.set(device_default_output_name)
                set_value("dev_out",device_default_output_name)
            else:
                #dev_out_name_var.set(out_values[0])
                set_value("dev_out",out_values[0])

    dev_out_changed()

    if in_values:
        if dev_in_name not in in_values:
            if device_default_input_name in in_values:
                #dev_in_name_var.set(device_default_input_name)
                set_value("dev_in",device_default_input_name)
            else:
                #dev_in_name_var.set(in_values[0])
                set_value("dev_in",in_values[0])

    dev_in_changed()

@catch
def fft_window_changed(sender=None, app_data=None):
    fft_window_name=get_value('fft_window')
    print('fft_window_changed',sender, app_data,fft_window_name)

    global fft_window
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

    print('fft_window:',len(fft_window))

    #fft_window = eval(f'{fft_window_name}({fft_size})')()

device_out_current=None

@catch
def dev_out_changed(sender=None, app_data=None):
    print('dev_out_changed',sender, app_data)

    global device_out_current,device_out_channels_stream_option

    #dev_name=dev_out_name_var.get()
    dev_out_name=get_value("dev_out")

    device_out_current=[device for device in devices if device['name']==dev_out_name][0]

    dev_out_channell_values=['all'] + [str(val) for val in range(1,device_out_current['max_output_channels']+1)]
    #dev_out_channell_cb.configure( values=dev_out_channell_cb_values )

    configure_item("dev_out_channell",items=dev_out_channell_values)

    #dev_out_channell_value=dev_out_channell_var.get()
    dev_out_channell_value=get_value("dev_out_channell")

    if not dev_out_channell_value or dev_out_channell_value not in dev_out_channell_values:
        dev_out_channell_value='all'
        #dev_out_channell_var.set(dev_out_channell_value)
        set_value("dev_out_channell",dev_out_channell_value)

    #dev_out_samplerate_var.set(int(device_out_current['default_samplerate']))
    set_value("dev_out_samplerate",int(device_out_current['default_samplerate']))

    dev_out_channell_changed()

device_in_current=None

@catch
def dev_in_changed(sender=None, app_data=None):
    print('dev_in_changed',sender, app_data)

    global device_in_current,device_in_channels_stream_option

    #dev_name=dev_in_name_var.get()
    dev_name=get_value("dev_in")

    device_in_current=[device for device in devices if device['name']==dev_name][0]

    dev_in_channell_values=['all'] + [str(val) for val in range(1,device_in_current['max_input_channels']+1)]
    configure_item("dev_in_channell",items=dev_in_channell_values)

    dev_in_channell_value=get_value("dev_in_channell")

    if not dev_in_channell_value or dev_in_channell_value not in dev_in_channell_values:
        dev_in_channell_value='all'
        set_value("dev_in_channell",dev_in_channell_value)

    #dev_in_samplerate_var.set(int(device_in_current['default_samplerate']))
    set_value("dev_in_samplerate",int(device_in_current['default_samplerate']))

    dev_in_channell_changed()

def on_click(sender, app_data):
    print('on_click',sender, app_data)

    button_nr=app_data[0]

    global sweeping,record_after,lock_frequency
    if button_nr==0:
        sweeping=False

        if lock_frequency:
            lock_frequency=False
            play_stop()
            #on_mouse_move_old(event)
        else:
            play_start()
            status_set_frequency()

            #record_after=root_after(200,recording_start)
            recording_start()
    elif button_nr==1:
        sweeping=False

        if lock_frequency:
            lock_frequency=False
            play_stop()
            #on_mouse_move_old(event)
        else:
            #on_mouse_move_old(event)
            lock_frequency=True

            play_start()
            status_set_frequency()
    else:
        print('another button:',button_nr)

def on_release(sender, app_data):
    print('on_release',sender, app_data)
    button_nr=app_data

    global recording,sweeping,lock_frequency

    if button_nr==0:
        #root_after_cancel(record_after)
        lock_frequency=False

        recording=False
        #update_tracks_buttons()
        sweeping=False

        play_stop()
        status_set_frequency()

    elif button_nr==1:
        #root_after_cancel(record_after)

        recording=False
        #update_tracks_buttons()
        sweeping=False
    else:
        print('another button:',button_nr)

prev_mouse_x=0
def on_mouse_move(sender, app_data):
    if not dpg.is_item_hovered("plot"):
        return

    # app_data = (x, y) w pikselach viewportu
    #mouse_x, mouse_y = app_data

    # konwersja pixel -> wartość osi X
    plot_x, _ = get_plot_mouse_pos()
    #print(app_data,plot_x)

    # ustawienie pozycji pionowej linii
    #set_value("cursor_f", [plot_x])
    if plot_x is not None:
        x = int(plot_x)
        global prev_mouse_x,f_current

        if x != prev_mouse_x:
            prev_mouse_x = x

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
            2.0,
            category=dpg.mvThemeCat_Plots
        )

with theme() as white_line_theme:
    with theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(
            dpg.mvPlotCol_Line,
            (255, 255, 255, 255),
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

bucket_freqs

bucket_freqs=tuple(bucket_freqs)

track_line_data_y={}

for track in range(tracks):
    track_line_data_y[track]=[dbmin]*spectrum_buckets_quant


###################################################
with dpg.window(label="main") as main:
    with child_window(height=30):
        dpg.add_text(color=(150,200,255),tag='status')

    with dpg.table(resizable=True,policy=dpg.mvTable_SizingStretchProp,header_row=False):
        #
        dpg.add_table_column()
        dpg.add_table_column(width_fixed=True,init_width_or_weight=300)

        with table_row():
            with plot(tag='plot',no_mouse_pos=True,width=-1,height=-1,no_menus=True,no_frame=True) as plot:
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

                    for lab,val in xticks:
                        if lab:
                            add_line_series([val,val], [-130,0],tag=f'stick{val}')
                            bind_item_theme(f'stick{val}',grid_line_theme)

                    for track in range(tracks):
                        spectrum_line_color[track]='Black'
                        spectrum_line[track]=add_line_series(bucket_freqs, track_line_data_y[track], tag=f"track{track}")
                        bind_item_theme(f"track{track}",red_line_theme)

                with item_handler_registry(tag="plot_handlers"):
                    add_item_hover_handler(callback=on_mouse_move)
                    add_item_clicked_handler(callback=on_click)

            with child_window():
                add_combo(tag='api',default_value='',callback=api_changed,width=-1)
                add_combo(tag='fft_window',items=['ones','hanning','hamming','blackman','bartlett'],default_value='blackman',callback=fft_window_changed,width=-1)
                add_combo(tag='dev_out',default_value='',callback=dev_out_changed,width=-1)
                add_combo(tag='dev_in',default_value='',callback=dev_in_changed,width=-1)
                add_combo(tag='dev_out_channell',default_value='',callback=dev_out_channell_changed,width=-1)
                add_combo(tag='dev_in_channell',default_value='',callback=dev_in_channell_changed,width=-1)
                add_combo(tag='dev_out_samplerate',default_value='',callback=dev_out_samplerate_changed,width=-1)
                add_combo(tag='dev_in_samplerate',default_value='',callback=dev_in_samplerate_changed,width=-1)
                add_checkbox(label='FFT',tag='fft',default_value=fft_on,callback=fft_toggle)

                for track_temp in range(tracks):
                    add_checkbox(label=f'Track {track_temp}',tag=f'trackbutton{track_temp}',default_value=False,callback=trackbutton_press,user_data=track_temp)

                add_checkbox(label='Record',tag='record',default_value=False,callback=rec_toggle)
                add_button(label='Flatline',tag='flatline',callback=flatline)
                add_button(label='Sweep',tag='sweep',callback=sweep)


    bind_item_handler_registry("plot", "plot_handlers")
    with dpg.handler_registry():
        dpg.add_mouse_release_handler(callback=on_release)

APP_FILE = normpath(__file__)
APP_DIR = dirname(APP_FILE)

ico_path=Path(path_join(APP_DIR,"./icons/sas.png"))
ico_small_path=Path(path_join(APP_DIR,"./icons/sas_small.png"))

dpg.set_viewport_small_icon(ico_small_path)
dpg.set_viewport_large_icon(ico_path)

dpg.set_primary_window(main, True)
dpg.setup_dearpygui()
dpg.show_viewport()

########################################################################

#def widget_tooltip(widget,message):
#    widget.bind("<Motion>", lambda event : status_var_set(message))
#    widget.bind("<Leave>", lambda event : status_var_set(default_status))

try:
    distro_info=Path(path_join(APP_DIR,'distro.info.txt')).read_text(encoding='utf-8')

except Exception as exception_1:
    print(exception_1)
    distro_info = 'Error. No distro.info.txt file.'

distro_info+= "\nnumpy       " + str(numpy_version) + "\nsounddevice " + str(sounddevice_version) + "\n\ndear py gui version:  " + str(dpg.get_dearpygui_version())

print(f'distro info:\n{distro_info}')

default_status='Click and hold the mouse button on the spectrum graph...'

recording=False
sweeping=False

#buttons_right = Frame(root,bg=bg_color)
#buttons_right.grid( row=0, column=1, sticky="news", padx=(0,6),pady=4 )
#trackbuttons={}

#canvas.bind("<Motion>", on_mouse_move)
#canvas.bind("<ButtonPress-1>", on_mouse_press_1)
#canvas.bind("<ButtonPress-3>", on_mouse_press_3)
#canvas.bind("<ButtonRelease-1>", on_mouse_release_1)
#canvas.bind("<ButtonRelease-3>", on_mouse_release_3)

#canvas.bind("<MouseWheel>", on_mouse_scroll_win)
#canvas.bind("<Button-4>", on_mouse_scroll_lin)
#canvas.bind("<Button-5>", on_mouse_scroll_lin)

if False:
    #widget_tooltip(rec_button,'Recording')
    #widget_tooltip(reset_button,'Reset all samples in current buffer')
    #widget_tooltip(fft_button,'FFT')

    Label(buttons_right).grid(row=tracks+2,column=0,sticky='news')
    buttons_right.grid_rowconfigure(tracks+2,weight=1)

    buttons_bottom = Frame(root,bg=bg_color)
    buttons_bottom.grid(row=1, column=0, pady=4,padx=6,sticky="news",columnspan=2)

    #widget_tooltip(sweep_button,'Run frequency sweep.')

    Label(buttons_bottom,image=ico['empty'],relief='flat').grid(row=0, column=3, padx=5,sticky='news')

    image_button=Button(buttons_bottom,image=ico['save_pic'], command=save_image,takefocus=0)
    image_button.grid(row=0, column=3, padx=5)
    widget_tooltip(image_button,'Save Image file')

    csv_button=Button(buttons_bottom,image=ico['save_csv'], command=save_csv,takefocus=0)
    csv_button.grid(row=0, column=4, padx=5)
    widget_tooltip(csv_button,'Save CSV file')

    image_button=Button(buttons_bottom,image=ico['load_csv'], command=load_csv,takefocus=0)
    image_button.grid(row=0, column=5, padx=5)
    widget_tooltip(image_button,'Load CSV file')

    Label(buttons_bottom,image=ico['empty'],relief='flat').grid(row=0, column=6, padx=4,sticky='news')

    home_button=Button(buttons_bottom,image=ico['home'], command=go_to_homepage,takefocus=0)
    home_button.grid(row=0, column=7, padx=5)
    widget_tooltip(home_button,f'Visit project homepage ({HOMEPAGE})')

    license_button=Button(buttons_bottom,image=ico['license'], command=license_wrapper,takefocus=0)
    license_button.grid(row=0, column=8, padx=5)
    widget_tooltip(license_button,'Show License')

    about_button=Button(buttons_bottom,image=ico['about'],  command=about_wrapper,takefocus=0)
    about_button.grid(row=0, column=9, padx=(5,0))
    widget_tooltip(about_button,'About')

    settings_button=Button(buttons_bottom,image=ico['settings'],  command=settings_wrapper,takefocus=0)
    settings_button.grid(row=0, column=10   , padx=(5,0))
    widget_tooltip(settings_button,'Settings')

    buttons_bottom.columnconfigure(0,weight=1)

fft_on=True
rec_on=True

stream_in=None
stream_out=None

if False:
    frame_options = Frame(root)
    frame_options.grid(row=2,column=0)

    Label(frame_options,text='Channells',anchor='n',justify='center',width=10).grid(row=0, column=2, sticky='news',padx=2,pady=2)
    Label(frame_options,text='Samplerate',anchor='n',justify='center',width=10).grid(row=0, column=3, sticky='news',padx=2,pady=2)

    frame_options.grid_columnconfigure((1,3,6,9), weight=1)
    frame_options.grid_forget()

refresh_devices()

fft_window_changed()

api_changed()

if False:
    root.bind('<F1>', lambda event : about_wrapper() )
    root.bind('<KeyPress>', KeyPress )

redraw_tracks_lines=True
redraw_fft_line=True
current_sample_modified=True

for i_fft in range(fft_points):
    fft_line_data_x[i_fft]=i_fft * samplerate_by_fft_size

fft_set()

processing_thread=Thread(target=audio_input_processing_thread,daemon=True)
processing_thread.start()

track_auto_enable()

try:
    while is_dearpygui_running():
        if redraw_fft_line:
            if fft_on:
                set_value("fft_line", [fft_line_data_x, fft_line_data_y])
                redraw_fft_line=False

        if redraw_tracks_lines:
            for track in range(tracks):
                if track in visible_tracks:
                    set_value(f"track{track}", [bucket_freqs, track_line_data_y[track]])
                    configure_item(f"track{track}",show=True)
                else:
                    configure_item(f"track{track}",show=False)

            redraw_tracks_lines=False

        if False and current_sample_modified:
            continue
            y=db2y(current_sample_db)

            canvas_itemconfigure( cursor_db_text, text=str(round(current_sample_db))+"dB" )
            canvas_coords(cursor_db_text,canvas_width_m20, y)

            canvas_coords(cursor_db,canvas_width-40, y, canvas_width, y)
            current_sample_modified=False

        render_dearpygui_frame()

        if exiting:
            break

except Exception as main_loop_error:
    print("ERROR:",main_loop_error)

finally:
    recording=False
    sweeping=False
    exiting=True

    samples_chunks_fifo_put('dummy_finish')

    if stream_in:
        stream_in.stop()
        stream_in.close()

    play_abort()

    if stream_out:
        stream_out.close()

    destroy_context()
    processing_thread.join()
    sys_exit(1)

