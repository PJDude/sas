#!/usr/bin/python3

####################################################################################
#
#  Copyright (c) 2025 Piotr Jochymek
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

from tkinter import Tk,Frame, StringVar, Canvas, PhotoImage, LabelFrame
from tkinter.ttk import Button,Style,Combobox
from tkinter.filedialog import asksaveasfilename, askopenfilename
from threading import Thread
from time import sleep

from numpy import mean as np_mean,square as np_square,float64,ones,hanning,hamming,blackman,bartlett, abs as np_abs,fft as np_fft,log10 as np_log10
from sounddevice import Stream,InputStream,OutputStream,query_devices,default as sd_default,query_hostapis
from collections import deque

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

fft_size = blocksize_in*8*2
fft_points=int(fft_size/2+1)

if windows:
    from os import startfile

def status_set_frequency():
    res_list = [str(round(f_current))+ ' Hz (']
    for track in visible_tracks:
        db_temp = round(spectrum_buckets[track][current_bucket])
        res_list.append(str(track+1) + ':' + str(db_temp))

    res_list.append(') [#buffer:dBFS]')
    status_var_set(' '.join(res_list))

def on_mouse_move(event):
    if not sweeping and not lock_frequency and not stream_out_state==-1:
        logf=xpixel_to_logf(event.x)

        if  logf_min_audio<logf<logf_max_audio:
            change_logf(logf)
            status_set_frequency()
            global f_current
            f_current=10**logf

        widgets=canvas_find_withtag("current")

        for track in visible_tracks:
            if spectrum_line[track] in widgets:
                trackbutton_motion(track)
            else:
                trackbutton_leave(track)

def recording_start():
    global recording
    recording=True

record_after=None

def on_mouse_press_1(event):
    try:
        global sweeping,record_after,lock_frequency
        sweeping=False

        if lock_frequency:
            lock_frequency=False
            play_stop()
            on_mouse_move(event)
        else:
            play_start()
            status_set_frequency()

            record_after=root_after(200,recording_start)

    except Exception as e:
        print("on_mouse_press_1:",e)

def on_mouse_press_3(event):
    global sweeping,record_after,lock_frequency
    sweeping=False

    if lock_frequency:
        lock_frequency=False
        play_stop()
        on_mouse_move(event)
    else:
        on_mouse_move(event)
        lock_frequency=True

        play_start()
        status_set_frequency()

        record_after=root_after(200,recording_start)

def on_mouse_release_1(event):
    global recording,sweeping,lock_frequency
    root_after_cancel(record_after)
    lock_frequency=False

    recording=False
    update_tracks_buttons()
    sweeping=False

    play_stop()
    status_set_frequency()

def on_mouse_release_3(event):
    global recording,sweeping
    root_after_cancel(record_after)

    recording=False
    update_tracks_buttons()
    sweeping=False

def on_mouse_scroll_win(event):
    fmod = int(-1 * (event.delta/120))
    scroll_mod(fmod)

def on_mouse_scroll_lin(event):
    if event.num == 4:
        fmod = -1
    elif event.num == 5:
        fmod = 1
    else:
        return

    scroll_mod(fmod)

def scroll_mod(mod,factor=0.01):
    if lock_frequency:
        global f_current
        if mod>0:
            f_new = ceil(f_current*(1.0+factor))
        else:
            f_new = floor(f_current*(1.0-factor))

        if f_new>0:
            log_f_new=log10(f_new)
            if logf_min_audio<log_f_new<logf_max_audio:
                change_logf(log_f_new)
                status_set_frequency()
                f_current=f_new

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
                            track_line_data[current_track][bucket*2+1]=db2y(float_db)
                        else:
                            print("wrong db value:",float_db)
                            continue

        except Exception as e:
            print("Load_csv_error:",e)

        global redraw_tracks_lines,redraw_fft_line
        redraw_tracks_lines=True
        redraw_fft_line=True

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
                global no_update
                no_update=True

                x1 = root.winfo_rootx() + canvas.winfo_x()
                y1 = root.winfo_rooty() + canvas.winfo_y()
                x2 = x1 + canvas_width
                y2 = y1 + canvas_height

                canvas_itemconfig('cursor', state='hidden')
                canvas_itemconfig('cursor_freq', state='hidden')

                canvas_delete("cursor_db_text")

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
                root_update()
                root_update_idletasks()
                root_after(200)

                ImageGrab_grab().crop((x1, y1, x2, y2)).save(filename)
                canvas_delete('mark')

                canvas_itemconfig('cursor', state='normal')
                update_tracks_buttons()

                global redraw_tracks_lines,redraw_fft_line
                redraw_tracks_lines=True
                redraw_fft_line=True

                change_logf(current_logf)

                root.attributes('-topmost', False)
                no_update=False
                ###################################
            else:
                print("Unknown file type")
    else:
        print("Cancel")

scale_factor_canvas_width_to_bucket_quant=1
canvas_width_m20=1
canvas_width_m10=1
canvas_height_by_dbrange_display=0
canvas_height=0

def init_lines():
    curr_line_data=[0.0]*(spectrum_buckets_quant*2)
    for i in range(spectrum_buckets_quant):
        curr_line_data[i*2]= 0

    global track_line_data
    track_line_data=[]
    for track in range(tracks):
        track_line_data.append(list(curr_line_data))

def root_configure(event=None):
    if not exiting:
        global canvas_width,x_min_audio,canvas_width_m10,canvas_width_m20,scale_factor_logf_to_xpixel,scale_factor_canvas_width_to_bucket_quant,canvas_height,canvas_height_m20,redraw_tracks_lines,redraw_fft_line,current_sample_modified,canvas_height_by_dbrange_display,track_line_data,fft_line_data_x,fft_line_data_y,fft_line_data_indexes
        canvas_width=canvas_winfo_width()

        x_min_audio=logf_to_xpixel(logf_min_audio)
        x_max_audio=logf_to_xpixel(logf_max_audio)

        canvas_width_audio=x_max_audio-x_min_audio

        canvas_width_m20=canvas_width-20
        canvas_width_m10=canvas_width-10

        scale_factor_logf_to_xpixel=canvas_width/logf_max_m_logf_min

        scale_factor_canvas_width_to_bucket_quant=canvas_width_audio/spectrum_buckets_quant

        canvas_height=canvas_winfo_height()
        canvas_height_m20=canvas_height-20

        canvas_height_by_dbrange_display=canvas_height/dbrange_display

        global new_bg
        new_bg=bg_org.zoom(ceil(2*canvas_width/10),ceil(2*canvas_height/100))
        canvas_itemconfigure(canv_bg,image=new_bg)

        canvas_delete("grid")
        for f,bold,lab in ((10,0,''),(20,2,'20Hz'),(30,0,''),(40,0,''),(50,0,''),(60,0,''),(70,0,''),(80,0,''),(90,0,''),(100,1,'100Hz'),
                    (200,0,''),(300,0,''),(400,0,''),(500,0,''),(600,0,''),(700,0,''),(800,0,''),(900,0,''),(1000,1,'1kHz'),
                    (2000,0,''),(3000,0,''),(4000,0,''),(5000,0,''),(6000,0,''),(7000,0,''),(8000,0,''),(9000,0,''),(10000,1,'10kHz'),
                    (20000,2,'20kHz'),(40000,1,'')):

            x=logf_to_xpixel(log10(f))

            if bold==2:
                canvas_create_line(x, 0, x, canvas_height, fill="gray20" , tags="grid",width=1, dash = (6, 4))
                canvas_create_text(x+2, canvas_height_m20, text=lab, anchor="nw", font=("Arial", 8), tags="grid")
            elif bold==1:
                canvas_create_line(x, 0, x, canvas_height, fill="gray20" , tags="grid",width=1, dash = (6, 4))
                canvas_create_text(x+2, canvas_height_m20, text=lab, anchor="nw", font=("Arial", 8), tags="grid")
            else:
                canvas_create_line(x, 0, x, canvas_height, fill="gray" , tags="grid",width=1,dash = (2, 4))

        for db,bold in ((0,1),(-10,0),(-20,0),(-30,0),(-40,0),(-50,0),(-60,0),(-70,0),(-80,0),(-90,0),(-100,0),(-110,0),(-120,0)):
            y=db2y(db)

            canvas_create_text(6, y+4, text=str(db)+"dBFS", anchor="nw", font=("Arial", 8), tags="grid")
            if bold:
                canvas_create_line(0, y, canvas_width,y, fill="gray20" , tags="grid",width=1)
            else:
                canvas_create_line(0, y, canvas_width,y, fill="gray" , tags="grid",width=1,dash = (2, 4))

        canvas_tag_lower("grid")

        redraw_tracks_lines=True
        redraw_fft_line=True
        current_sample_modified=True

        change_logf(current_logf)

        y_initval = db2y(dbinit)

        for track in range(tracks):
            curr_line_data=track_line_data[track]
            curr_spectrum_buckets=spectrum_buckets[track]
            for i in range(spectrum_buckets_quant):
                i2=i+i
                curr_line_data[i2]= int(x_min_audio+scale_factor_canvas_width_to_bucket_quant * i)
                curr_line_data[i2+1]=db2y(curr_spectrum_buckets[i])

        fft_line_data_x=[-1]*fft_points
        #fft_line_data_y=[db2y(dbmin)]*fft_points

        for i_fft in range(fft_points):
            x=logf_to_xpixel(log10(i_fft * samplerate_by_fft_size + 1e-12))
            fft_line_data_x[i_fft]=x

        fft_line_data_x[0]=logf_to_xpixel(log10(1))
        #fft_line_data_y[0]=db2y(dbmin)

        prev_x=-1
        fft_line_data_indexes_temp=[]
        fft_line_data_indexes_temp_append=fft_line_data_indexes_temp.append
        for i_fft in range(fft_points):
            x=fft_line_data_x[i_fft]
            if prev_x!=x:
                prev_x=x
                fft_line_data_indexes_temp_append(i_fft)

        fft_line_data_indexes=tuple(fft_line_data_indexes_temp)

def update_tracks_buttons():
    for c in range(tracks):
        trackbuttons[c].configure( image=ico[str(c+1) + '_' + ('sel' if c==current_track and rec_on else 'on' if c in visible_tracks else 'off')])

def db2y(db):
    return int(canvas_height - ( canvas_height_by_dbrange_display*(db-dbmin_display) ) )

def gui_update():
    if exiting:
        if stream_in:
            stream_in.stop()
            stream_in.close()

        play_stop()

        if stream_out:
            stream_out.close()

        root.withdraw()
        root.destroy()
        sys_exit(1)
    elif no_update:
        root_after(1,gui_update)
    else:
        try:
            global redraw_tracks_lines,redraw_fft_line,current_sample_modified,fft_line_data

            if redraw_fft_line:
                if fft_on:
                    #canvas_coords(fft_line, *(v for index in fft_line_data_indexes for v in (fft_line_data_x[index], db2y(20*fft_line_data_y[index])) ) )
                    canvas_coords(fft_line, *fft_line_data)
                    redraw_fft_line=False

            if redraw_tracks_lines:
                for track in range(tracks):
                    if track in visible_tracks:
                        canvas_coords( spectrum_line[track], *(track_line_data[track]) )
                        canvas_itemconfigure( spectrum_line[track], fill=spectrum_line_color[track], state='normal' )
                    else:
                        canvas_itemconfigure( spectrum_line[track], state='hidden' )

                redraw_tracks_lines=False

            if current_sample_modified:
                y=db2y(current_sample_db)

                canvas_delete("cursor_db_text")
                if not fft_on:
                    canvas_create_text(canvas_width_m20, y, text=str(round(current_sample_db))+"dB", anchor="center", font=("Arial", 8), tags=("cursor_db_text"),fill="black")

                canvas_coords(cursor_db,canvas_width-40, y, canvas_width, y)
                current_sample_modified=False

        except Exception as e:
            print("update_plot_error:",e)

        root_after(1,gui_update)

def xpixel_to_logf(x):
    return x /scale_factor_logf_to_xpixel + logf_min

def logf_to_xpixel(logf):
    return int(scale_factor_logf_to_xpixel * (logf - logf_min) )

def logf_to_bucket(logf):
    return int(floor(scale_factor_logf_to_bucket * (logf - logf_min_audio)))

def bucket_to_logf(i):
    return (i+0.5)/scale_factor_logf_to_bucket + logf_min_audio

phase_step=1.0
f=0
f_bucket=0

def change_logf(logf):
    global current_logf,current_bucket,current_bucket_x2,phase_step,f,f_bucket

    current_logf=logf
    current_bucket=logf_to_bucket(current_logf)
    current_bucket_x2=current_bucket+current_bucket

    f = 10**logf
    f_bucket=logf_to_bucket(log10(f))

    phase_step = two_pi_by_samplerate * f

    x=logf_to_xpixel(logf)

    canvas_delete('cursor_freq')
    canvas_create_text(x+2, 2, text=str(round(f))+"Hz", anchor="nw", font=("Arial", 8), fill="black",tags='cursor_freq')

    canvas_coords(cursor_f, x, 0, x, canvas_height)

played_bucket=0
played_bucket_callbacks=0

def audio_output_callback(outdata, frames, time, status):
    global phase,stream_out_state,played_bucket,played_bucket_callbacks,phase_step,two_pi,f_bucket

    out_channell_index=0
    if stream_out_state==0:
        for i in range(blocksize_out):
            outdata[i,out_channell_index]=0
    else:
        for i in range(blocksize_out):
            outdata[i,out_channell_index]=sin(phase)
            phase += phase_step
            phase %= two_pi

        if stream_out_state==1:
            stream_out_state=2
            for i in range(blocksize_out):
                outdata[i,out_channell_index]*=volume_ramp[i]
        elif stream_out_state==-1:
            stream_out_state=0
            for i in range(blocksize_out):
                outdata[i,out_channell_index]*=volume_ramp[blocksize_out_m1-i]

        if f_bucket!=played_bucket:
            played_bucket_callbacks=1
            played_bucket=f_bucket
        else:
            played_bucket_callbacks+=1

def sweep():
    global recording,sweeping,fft_on,rec_on,redraw_fft_line,lock_frequency
    lock_frequency=False

    prev_fft=fft_on
    fft_on=False
    redraw_fft_line=True
    fft_set()

    rec_on=True
    recording=True

    track_auto_enable()
    update_tracks_buttons()
    update_rec_button()

    global redraw_tracks_lines
    redraw_tracks_lines=True

    play_stop()

    root_update()

    change_logf(logf_min_audio)
    logf_sweep_step=logf_max_audio_m_logf_min_audio/sweep_steps

    sweeping=True

    play_start()
    for i in range(sweep_steps):
        logf=logf_min_audio+i*logf_sweep_step

        change_logf(logf)
        status_var_set('Sweeping (' + str(round(10**logf))+ ' Hz), Click on the graph to abort ...')

        root_update()
        root_after(sweeping_after)

        if not sweeping:
            break

    sweeping=False
    status_var_set('Sweeping done.')

    play_stop()

    recording=False

    fft_on=prev_fft
    redraw_fft_line=True
    fft_set()

def play_start():
    global stream_out_state
    stream_out_state=1
    canvas_itemconfig(cursor_f, fill='red')

def play_stop():
    global stream_out_state
    if stream_out_state==2:
        stream_out_state=-1

    canvas_itemconfig(cursor_f, fill='white')

exiting=False
no_update=False

def close_app():
    global recording,sweeping,exiting
    recording=False
    sweeping=False
    exiting=True

current_sample_db=-120

fft_fifo = deque(maxlen=fft_size)
fft_fifo_extend=fft_fifo.extend
new_samples_to_process=False
fft_line_data=[]

def audio_input_callback_thread():
    global fft_line_data,fft_line_data_x,redraw_fft_line,current_sample_db,rec_on,current_track,current_bucket,redraw_tracks_lines,new_samples_to_process
    while not exiting:
        if new_samples_to_process:
            if recording or lock_frequency:
                #current_sample_db = 20 * log10(sqrt( np_mean(record_blocks) ) + 1e-12)
                current_sample_db = 10 * log10( np_mean(record_blocks) + 1e-12)

                if rec_on:
                    if current_track is not None:
                        spectrum_buckets[current_track][current_bucket]=current_sample_db

                        track_line_data_current_track=track_line_data[current_track]
                        current_bucket_x2_p1=current_bucket_x2+1
                        if played_bucket_callbacks>record_blocks_len:
                            track_line_data_current_track[current_bucket_x2_p1]=db2y(current_sample_db)
                        else:
                            #track_line_data_current_track[current_bucket_x2_p1]=(track_line_data_current_track[current_bucket_x2_p1] + db2y(current_sample_db))*0.5
                            track_line_data_current_track[current_bucket_x2_p1]=( track_line_data_current_track[current_bucket_x2_p1]*record_blocks_len_m1 + db2y(current_sample_db) ) / record_blocks_len
                        redraw_tracks_lines=True
                    #if played_bucket_callbacks>record_blocks_len:
                        #if current_bucket<spectrum_buckets_quant:

            else:
                current_sample_db = 10 * log10( np_mean(record_blocks_short) + 1e-12)

            #trzeba sprawdzic czy sie zmienilo
            current_sample_modified=True

            if fft_on:
                if len(fft_fifo) == fft_size:
                    if not redraw_fft_line:
                        fft_line_data_y = np_log10( np_abs( (np_fft_rfft( fft_fifo*fft_window))[0:fft_points] ) / fft_size + 1e-12)
                        fft_line_data = [v for index in fft_line_data_indexes for v in (fft_line_data_x[index], db2y(20*fft_line_data_y[index])) ]

                        redraw_fft_line=True

            new_samples_to_process=False
        else:
            sleep(0.001)

def audio_input_callback(indata, frames, time_info, status):
    if status:
        print(status)
        return

    try:
        global record_blocks_index_to_replace,record_blocks_index_to_replace_short,recording,new_samples_to_process

        this_callback_mean=np_mean(np_square(indata[:, 0], dtype=float64))

        if recording or lock_frequency:
            record_blocks[record_blocks_index_to_replace]=this_callback_mean
            record_blocks_index_to_replace+=1
            record_blocks_index_to_replace%=record_blocks_len

        else:
            record_blocks_short[record_blocks_index_to_replace_short]=this_callback_mean
            record_blocks_index_to_replace_short+=1
            record_blocks_index_to_replace_short%=record_blocks_len_short

        if fft_on:
            fft_fifo_extend(indata[:, 0])

        new_samples_to_process=True

    except Exception as e:
        print("audio_input_callback_error:",e)

def go_to_homepage():
    try:
        if windows:
            status_var_set('opening: %s' % HOMEPAGE)
            startfile(HOMEPAGE)
        else:
            status_var_set('executing: xdg-open %s' % HOMEPAGE)
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

def refresh_devices():
    global apis,default_api_nr,api_name_var,devices,device_default_input,device_default_output

    apis = query_hostapis()
    default_api_nr=0
    print(f'\nApis:')
    for i,api in enumerate(apis):
        print('')
        for key,val in api.items():
            print('  ',key,':',val)
            if api['devices']:
                default_api_nr=i

    device_default_input_index,device_default_output_index = sd_default.device

    devices=query_devices()

    for dev in devices:
        if not windows:
            try:
                Stream(device=dev['index'], samplerate=samplerate, channels=1)
            except Exception as e_try:
                print('e_try:',e_try)
                continue

        if dev['index']==device_default_input_index:
            device_default_input=dev
            default_api_nr=dev['hostapi']
        if dev['index']==device_default_output_index:
            device_default_output=dev
            default_api_nr=dev['hostapi']


    api_name_var.set(apis[default_api_nr]['name'])

    print('\nDevices:')
    for dev in devices:
        print('')
        for key,val in dev.items():
            print('  ',key,':',val)

current_api=None
def api_mod():
    print('api_mod')

    global current_api,apis,devices,dev_out_cb,dev_in_cb

    apiname=api_name_var.get()
    print(apiname)

    current_api=[api for api in apis if api['name']==apiname][0]

    out_values=[ dev['name'] for dev in devices if dev['max_output_channels'] > 0 and dev['index'] in current_api['devices'] ]
    in_values=[ dev['name'] for dev in devices if dev['max_input_channels'] > 0 and dev['index'] in current_api['devices'] ]

    dev_out_cb.configure(values=out_values )
    dev_in_cb.configure(values=in_values )

    dev_out_name=dev_out_name_var.get()
    dev_in_name=dev_in_name_var.get()

    device_default_input_name=device_default_input['name']
    device_default_output_name=device_default_output['name']

    print('defaults:',device_default_input_name,device_default_output_name)

    if out_values:
        if dev_out_name not in out_values:
            if device_default_output_name in out_values:
                dev_out_name_var.set(device_default_output_name)
            else:
                dev_out_name_var.set(out_values[0])
    dev_out_mod()

    if in_values:
        if dev_in_name not in in_values:
            if device_default_input_name in in_values:
                dev_in_name_var.set(device_default_input_name)
            else:
                dev_in_name_var.set(in_values[0])
    dev_in_mod()

def dev_out_mod():
    global stream_out,dev_out_name_var

    if stream_out:
        stream_out.stop()

    dev_name=dev_out_name_var.get()

    try:
        device=[device for device in devices if device['name']==dev_name][0]['index']
        stream_out = OutputStream( samplerate=samplerate, channels=1, dtype="float32", blocksize=blocksize_out, callback=audio_output_callback, latency="low",device=device )
    except Exception as e:
        print('dev_out_mod - error:',e)
    else:
        stream_out.start()

def dev_in_mod():
    global stream_in,dev_in_name_var,dev_dict

    if stream_in:
        stream_in.stop()

    dev_name=dev_in_name_var.get()

    try:
        device=[device for device in devices if device['name']==dev_name][0]['index']
        stream_in = InputStream( samplerate=samplerate, channels=1, dtype="float32", blocksize=blocksize_in, callback=audio_input_callback, latency="low",device=device )
    except Exception as e:
        print('dev_in_mod - error:',e)
    else:
        stream_in.start()

def fft_window_mod():
    global fft_window,fft_window_var

    fft_window = eval(f'{fft_window_var.get()}({fft_size})')

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

def about_wrapper():
    get_about_dialog().show()

settings_shown=False
def settings_wrapper():
    global settings_shown,frame_options,api_cb,api_name_var,dev_out_cb,dev_in_cb

    try:
        values=[ api['name'] for api in apis if api['devices'] ]
        api_cb.configure(values=values)

        if api_name_var.get() not in values:
            if values:
                api_name_var.set(values[0]['name'])

        #dev_out_cb.configure(values=[dev['name'] for dev in devices if dev['max_output_channels'] > 0])
        #dev_in_cb.configure(values=[dev['name'] for dev in devices if dev['max_input_channels'] > 0])
    except Exception as e:
        print(e)

    if settings_shown:
        settings_shown=False
        frame_options.grid_forget()
    else:
        settings_shown=True
        frame_options.grid(sticky='news')

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

def rec_toggle():
    global rec_on,redraw_tracks_lines

    rec_on=False if rec_on else True
    redraw_tracks_lines=True
    update_rec_button()
    track_auto_enable()
    update_tracks_buttons()

def update_rec_button():
    rec_button.configure(image=ico["rec_on" if rec_on else "rec_off"])

def fft_toggle():
    global fft_on,stream_in,redraw_fft_line,sweeping

    sweeping=False

    fft_on=False if fft_on else True
    fft_set()
    fft_window_mod()
    redraw_fft_line=True

def fft_set():
    fft_button.configure(image=ico["fft_on" if fft_on else "fft_off"] )
    canvas_itemconfig(cursor_db, state='hidden' if fft_on else 'normal')

    canvas_itemconfig(fft_line, state='normal' if fft_on else 'hidden')

def flatline():
    global redraw_tracks_lines,current_track

    if current_track is not None:
        spectrum_buckets[current_track]=[dbinit]*spectrum_buckets_quant

        for i in range(spectrum_buckets_quant):
            track_line_data[current_track][i*2+1]=db2y(dbinit)

        redraw_tracks_lines=True

def trackbutton_motion(track):
    canvas_itemconfig(spectrum_line[track], fill='red')
    global spectrum_line_color
    spectrum_line_color[track]='red'
    status_var_set(f'Choose buffer {track+1} (use Ctrl to select active track or press number keys)')

def trackbutton_leave(track):
    canvas_itemconfig(spectrum_line[track], fill='black')
    global spectrum_line_color
    spectrum_line_color[track]='black'

def trackbutton_press(event,track):
    control_pressed=bool('Control' in str(event))
    track_pressed(track,control_pressed)

    global visible_tracks
    if track in visible_tracks:
        trackbutton_motion(track)

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
            track_pressed(track,control_pressed)

def track_auto_enable():
    global current_track,visible_tracks,redraw_tracks_lines

    if not visible_tracks:
        visible_tracks.add(0)

    if current_track is None:
        current_track=next(iter(visible_tracks))

def track_pressed(track,control_pressed):
    global current_track,visible_tracks,redraw_tracks_lines,sweeping,lock_frequency,rec_on

    lock_frequency=False
    sweeping=False

    try:
        prev_current_track=current_track

        if control_pressed:
            rec_on=True

            visible_tracks.add(track)
            current_track=track
        elif track in visible_tracks:
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

        update_tracks_buttons()
        update_rec_button()

        #recording=False
        play_stop()

        redraw_tracks_lines=True
        status_set_frequency()

    except Exception as e_kp:
        print("track_pressed:",track,control_pressed, e_kp)

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

fmin,fini,fmax=10,442,40000
fmin_audio,fmax_audio=20,20000

logf_min,logf_ini,logf_max=log10(fmin),log10(fini),log10(fmax)
logf_min_audio,logf_max_audio=log10(fmin_audio),log10(fmax_audio)

current_logf=logf_ini

current_track=0
visible_tracks={current_track}

two_pi = pi+pi
two_pi_by_samplerate = two_pi/samplerate

spectrum_buckets_quant=256
spectrum_sub_bucket_samples=4
sweep_steps=spectrum_buckets_quant*spectrum_sub_bucket_samples

logf_max_m_logf_min = logf_max-logf_min
logf_max_audio_m_logf_min_audio = logf_max_audio-logf_min_audio

scale_factor_logf_to_bucket=spectrum_buckets_quant/logf_max_audio_m_logf_min_audio

current_bucket=logf_to_bucket(current_logf)
current_bucket_x2=current_bucket+current_bucket

dbmin=-120.0
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

sweeping_after=int(1000*time_to_collect_sample*1.5/spectrum_sub_bucket_samples)

# 43
record_blocks_len=int((samplerate*time_to_collect_sample)/blocksize_in)
record_blocks_len_m1=record_blocks_len-1
record_blocks_len_short=ceil(record_blocks_len/5)

record_blocks=[0]*record_blocks_len
record_blocks_index_to_replace=0

record_blocks_short=[0]*record_blocks_len_short
record_blocks_index_to_replace_short=0

redraw_tracks_lines=True
redraw_fft_line=True
current_sample_modified=True

root = Tk()
root.protocol("WM_DELETE_WINDOW", close_app)

root_after = root.after
root_after_cancel = root.after_cancel
root_after_idle = root.after_idle
root_update = root.update
root_update_idletasks = root.update_idletasks

title=f"Simple Audio Sweeper {VER_TIMESTAMP}"
root.title(title)

style = Style()

ico = { img:PhotoImage(data = img_data) for img,img_data in image.items() }

ico_sas = ico['sas']
ico_sas_small = ico['sas_small']
bg_org=ico['bg']

main_icon_tuple = (ico_sas,ico_sas_small)

root.iconphoto(True, *main_icon_tuple)

theme_name='vista' if windows else 'clam'
try:
    style.theme_create( "dummy", parent=theme_name )
except Exception as e:
    print("cannot set theme - setting default")
    print(e)
    sys_exit(1)

bg_color = style.lookup('TFrame', 'background')

style.theme_use("dummy")
style_map = style.map

style_configure = style.configure

#works but not for every theme

style_map("TCheckbutton",indicatorbackground=[("disabled",bg_color),('','white')],indicatorforeground=[("disabled",'darkgray'),('','black')],foreground=[('disabled',"gray"),('',"black")])
style_map("TEntry", foreground=[("disabled",'darkgray'),('','black')],fieldbackground=[("disabled",bg_color),('','white')])

style_map("TButton",  fg=[('disabled',"gray"),('',"black")] )

style_configure("TButton", background = bg_color)
style_configure('TRadiobutton', background=bg_color)
style_configure("TCheckbutton", background = bg_color)
style_configure("TScale", background=bg_color)
style_configure('TScale.slider', background=bg_color)
style_configure('TScale.Horizontal.TScale', background=bg_color)
style.configure("TButton", relief="raised")

style_map("TEntry",relief=[("disabled",'flat'),('','sunken')],borderwidth=[("disabled",0),('',2)])
style_map("TButton",  relief=[('disabled',"flat"),('pressed', 'sunken'),('active',"raised")] )

style_map("TCheckbutton",relief=[('disabled',"flat"),('',"sunken")])

style_configure("TButton", anchor = "center")
style_configure("TCheckbutton",anchor='center',padding=(4, 0, 4, 0) )

if windows:
    #fix border problem ...
    style_configure("TCombobox",padding=1)

def widget_tooltip(widget,message):
    widget.bind("<Motion>", lambda event : status_var_set(message))
    widget.bind("<Leave>", lambda event : status_var_set(default_status))

APP_FILE = normpath(__file__)
APP_DIR = dirname(APP_FILE)

try:
    distro_info=Path(path_join(APP_DIR,'distro.info.txt')).read_text(encoding='utf-8')
except Exception as exception_1:
    print(exception_1)
    distro_info = 'Error. No distro.info.txt file.'
else:
    print(f'distro info:\n{distro_info}')

#for initialization only
scale_factor_logf_to_xpixel=1

root.rowconfigure(1, weight=1)
root.columnconfigure(0, weight=1)

default_status='Click and hold the mouse button on the spectrum graph...'
status_var = StringVar(value=default_status)
status_var_set = status_var.set

recording=False
sweeping=False

canvas = Canvas(root,height=300, width=800,relief='sunken',borderwidth=1,bg=bg_color)
canvas.grid(row=1, column=0, sticky="news", padx=4,pady=4)

buttons_right = Frame(root,bg=bg_color)
buttons_right.grid( row=1, column=1, sticky="news", padx=(0,6),pady=4 )
trackbuttons={}

canvas.bind("<Motion>", on_mouse_move)
canvas.bind("<ButtonPress-1>", on_mouse_press_1)
canvas.bind("<ButtonPress-3>", on_mouse_press_3)
canvas.bind("<ButtonRelease-1>", on_mouse_release_1)
canvas.bind("<ButtonRelease-3>", on_mouse_release_3)

if windows:
    canvas.bind("<MouseWheel>", on_mouse_scroll_win)
else:
    canvas.bind("<Button-4>", on_mouse_scroll_lin)
    canvas.bind("<Button-5>", on_mouse_scroll_lin)

canvas_itemconfig = canvas.itemconfig
canvas_delete = canvas.delete
canvas_create_line = canvas.create_line
canvas_create_text = canvas.create_text
canvas_create_image = canvas.create_image
canvas_coords = canvas.coords
canvas_itemconfigure=canvas.itemconfigure
canvas_find_withtag=canvas.find_withtag
canvas_winfo_width=canvas.winfo_width
canvas_winfo_height=canvas.winfo_height
canvas_tag_raise=canvas.tag_raise
canvas_tag_lower=canvas.tag_lower

cursor_f = canvas_create_line(logf_ini, 0, logf_ini, 0, width=1, fill="white", tags="cursor")
canvas.lower(cursor_f)
cursor_db = canvas_create_line(logf_max, 0, logf_max, 0, width=10, fill="white", tags="cursor")
canvas.lower(cursor_db)

fft_line=canvas_create_line( (0,0,0,0) , fill="gray36" , width=1, smooth=True,state='normal', tags='fft' )

spectrum_line_color={}
spectrum_line={}
for track in range(tracks):
    spectrum_line_color[track]='Black'
    spectrum_line[track]=canvas_create_line( (0,0,0,0) , width=1, smooth=True,state="normal", fill='Black', tags="track" )

canv_bg = canvas.create_image(0,0,image=bg_org)
canvas.lower(canv_bg)

for track_temp in range(tracks):
    buttontemp = trackbuttons[track_temp]=Button(buttons_right,takefocus=0)
    buttontemp.grid(row=track_temp,column=0,sticky='news',pady=(0,4))
    buttontemp.bind("<Button-1>", lambda event,track_local=track_temp : trackbutton_press(event,track=track_local) )
    buttontemp.bind("<Motion>", lambda event,track_local=track_temp : trackbutton_motion(track=track_local) )
    buttontemp.bind("<Leave>", lambda event,track_local=track_temp : trackbutton_leave(track=track_local) )

rec_button=Button(buttons_right,image=ico['rec_on'],command=rec_toggle,takefocus=0)
rec_button.grid(row=tracks,column=0,sticky='news')
widget_tooltip(rec_button,'Recording')

reset_button=Button(buttons_right,image=ico['reset'],command=flatline,takefocus=0)
reset_button.grid(row=tracks+1,column=0,sticky='news')
widget_tooltip(reset_button,'Reset all samples in current buffer')

Label(buttons_right).grid(row=tracks+2,column=0,sticky='news')
buttons_right.grid_rowconfigure(tracks+2,weight=1)

fft_button=Button(buttons_right,image=ico['fft_on'],command=fft_toggle,takefocus=0)
fft_button.grid(row=tracks+3,column=0,sticky='news')
widget_tooltip(fft_button,'FFT')

buttons_bottom = Frame(root,bg=bg_color)
buttons_bottom.grid(row=4, column=0, pady=4,padx=6,sticky="news",columnspan=2)

Label(buttons_bottom,textvariable=status_var,relief='sunken', anchor='nw',bd=1).grid(row=0, column=0, padx=0,sticky='news')

sweep_button=Button(buttons_bottom,image=ico['play'], command=sweep,takefocus=0)
sweep_button.grid(row=0, column=1, padx=5)
widget_tooltip(sweep_button,'Run frequency sweep.')

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

frame_options = LabelFrame(root,text='',bd=2,bg=bg_color,takefocus=False)
frame_options.grid(row=5,column=0,sticky='news',padx=4,pady=(4,2),columnspan=3)

api_name_var=StringVar()
Label(frame_options,text='API:',anchor='w').grid(row=0, column=0, sticky='wens',padx=1,pady=4)
api_cb = Combobox(frame_options,textvariable=api_name_var,state='readonly',width=10)
api_cb.grid(row=0, column=1, sticky='news',padx=1,pady=4)
api_cb.bind("<<ComboboxSelected>>", lambda event : api_mod())

dev_out_name_var=StringVar()
Label(frame_options,text='Out:',anchor='w').grid(row=0, column=2, sticky='wens',padx=1,pady=4)
dev_out_cb = Combobox(frame_options,textvariable=dev_out_name_var,state='readonly',width=16)
dev_out_cb.grid(row=0, column=3, sticky='news',padx=1,pady=4)
dev_out_cb.bind("<<ComboboxSelected>>", lambda event : dev_out_mod())

dev_in_name_var=StringVar()
Label(frame_options,text='In:',anchor='w').grid(row=0, column=4, sticky='wens',padx=1,pady=4)
dev_in_cb = Combobox(frame_options,textvariable=dev_in_name_var,state='readonly',width=16)
dev_in_cb.grid(row=0, column=5, sticky='news',padx=1,pady=4)
dev_in_cb.bind("<<ComboboxSelected>>", lambda event : dev_in_mod())

fft_window_var=StringVar(value='blackman')
Label(frame_options,text='FFT wnd:',anchor='w').grid(row=0, column=6, sticky='wens',padx=1,pady=4)
fft_window_cb = Combobox(frame_options,textvariable=fft_window_var,state='readonly',width=10,values=('ones','hanning','hamming','blackman','bartlett'))
fft_window_cb.grid(row=0, column=7, sticky='news',padx=1,pady=4)
fft_window_cb.bind("<<ComboboxSelected>>", lambda event : fft_window_mod())

frame_options.grid_columnconfigure((1,3,5,7), weight=1)
frame_options.grid_forget()

refresh_devices()

fft_window_mod()

api_mod()

root.bind('<Configure>', root_configure)
root.bind('<F1>', lambda event : about_wrapper() )

root.bind('<KeyPress>', KeyPress )

init_lines()
root_configure()
update_rec_button()
update_tracks_buttons()

fft_set()

root_after(200,gui_update)

Thread(target=audio_input_callback_thread).start()

root.mainloop()
