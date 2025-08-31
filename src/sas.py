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
from tkinter import Tk,DoubleVar, BooleanVar, StringVar, IntVar, Canvas, PhotoImage
from tkinter.ttk import Frame,Label,Button,Checkbutton,Style,Entry

from sounddevice import InputStream,RawOutputStream
from math import pi, sin, log10

from numpy import mean as np_mean,square as np_square,float64, zeros, sin as np_sin

from PIL import ImageGrab,Image

from tkinter.filedialog import asksaveasfilename

from pathlib import Path

from time import strftime, localtime

import os
from os import name as os_name
from sys import exit as sys_exit

from images import image

windows = bool(os_name=='nt')

def on_mouse_move(event):
    if not sweeping:
        logf=xpixel_to_logf(event.x)

        if logf<logf_max_audio and logf>logf_min_audio:
            change_logf(logf)
            status_var.set(str(round(10**logf))+ ' Hz')

def recording_start():
    global recording
    recording=True

def on_mouse_press(event):
    global sweeping
    sweeping=False

    start_out()

    global record_after
    record_after=root.after(200,recording_start)

def on_mouse_release(event):
    global record_after
    root.after_cancel(record_after)

    global recording
    recording=False

    global sweeping
    sweeping=False

    stop_out()

def save_csv():
    global slower_update
    slower_update=True

    time_postfix=strftime('%Y_%m_%d_%H_%M_%S',localtime())
    filename = asksaveasfilename(title = "Save CSV",initialfile = f'sas_{time_postfix}.csv',defaultextension=".csv",filetypes=[("All Files","*.*"),("CSV Files","*.csv")])

    if filename:
        try:
            with open(filename, 'w') as f:
                f.write("frequency[Hz],level[dB]\n")
                for i,db in enumerate(spectrum_buckets):
                    logf=scale_bucket_to_logf(i)
                    f.write(f"{round(100*(10**logf))/100},{round(1000*db)/1000}\n")
        except Exception as e:
            print("save_csv_error:",e)

    slower_update=False

def save_image():
    global slower_update
    slower_update=True
    time_postfix=strftime('%Y_%m_%d_%H_%M_%S',localtime())
    filename = asksaveasfilename(title = "Save Image",initialfile = f'sas_{time_postfix}.png',defaultextension=".png",filetypes=[("All Files","*.*"),("PNG Files","*.png")])

    if filename:
        if os.path.exists(filename):
            print("Name already exists!")
        else:
            path, file = os.path.split(filename)
            name, ext = os.path.splitext(file)

            if ext.lower() in ['.gif', '.png']:
                x1 = root.winfo_rootx() + canvas.winfo_x()
                y1 = root.winfo_rooty() + canvas.winfo_y()
                x2 = x1 + canvas.winfo_width()
                y2 = y1 + canvas.winfo_height()

                canvas.itemconfig('cursor', state='hidden')
                root.lift()
                root.attributes('-topmost', True)

                ###################################
                root.update()
                root.update_idletasks()
                root.after(200)

                ImageGrab.grab().crop((x1, y1, x2, y2)).save(filename)

                canvas.itemconfig('cursor', state='normal')
                root.attributes('-topmost', False)
                ###################################
            else:
                print("Unknown file type")
    else:
        print("Cancel")

    slower_update=False

def clear():
    canvas.delete("fline")

scale_factor_canvas_width_to_buckets_quant=1
canvas_winfo_width_m20=1

def root_configure(event=None):
    if not exiting:
        global canvas_winfo_width
        canvas_winfo_width=canvas.winfo_width()

        global x_min_audio
        x_min_audio=scale_logf_to_pixels(logf_min_audio)
        x_max_audio=scale_logf_to_pixels(logf_max_audio)

        canvas_winfo_width_audio=x_max_audio-x_min_audio

        global canvas_winfo_width_m20
        canvas_winfo_width_m20=canvas_winfo_width-20

        global scale_factor_logf_to_pixels
        scale_factor_logf_to_pixels=canvas_winfo_width/logf_max_m_logf_min

        global scale_factor_logf_to_buckets
        #scale_factor_logf_to_buckets=spectrum_buckets_quant/logf_max_m_logf_min
        scale_factor_logf_to_buckets=spectrum_buckets_quant/logf_max_audio_m_logf_min_audio

        global scale_factor_canvas_width_to_buckets_quant
        scale_factor_canvas_width_to_buckets_quant=canvas_winfo_width_audio/spectrum_buckets_quant

        canvas.delete("grid")

        global canvas_winfo_height
        canvas_winfo_height=canvas.winfo_height()
        global canvas_winfo_height_m20
        canvas_winfo_height_m20=canvas_winfo_height-20

        canvas_create_line=canvas.create_line
        canvas_create_text=canvas.create_text
        for f,bold,lab in ((10,0,''),(20,1,'20Hz'),(30,0,''),(40,0,''),(50,0,''),(60,0,''),(70,0,''),(80,0,''),(90,0,''),(100,1,'100Hz'),
                    (200,0,''),(300,0,''),(400,0,''),(500,0,''),(600,0,''),(700,0,''),(800,0,''),(900,0,''),(1000,1,'1kHz'),
                    (2000,0,''),(3000,0,''),(4000,0,''),(5000,0,''),(6000,0,''),(7000,0,''),(8000,0,''),(9000,0,''),(10000,1,'10kHz'),
                    (20000,1,'20kHz'),(40000,1,'')):
            x=scale_logf_to_pixels(log10(f))

            if bold:
                canvas_create_line(x, 0, x, canvas_winfo_height, fill="black" , tags="grid",width=1)
                canvas_create_text(x+2, canvas_winfo_height_m20, text=lab, anchor="nw", font=("Arial", 8), tags="grid")
            else:
                canvas_create_line(x, 0, x, canvas_winfo_height, fill="gray" , tags="grid",width=1,dash = (5, 2))

        for db,bold in ((10,0),(0,1),(-10,0),(-20,0),(-30,0),(-40,0),(-50,0),(-60,0),(-70,0),(-80,0),(-90,1)):
            y=db2y(db)

            canvas_create_text(6, y+4, text=str(db)+"dB", anchor="nw", font=("Arial", 8), tags="grid")
            if bold:
                canvas_create_line(0, y, canvas_winfo_width,y, fill="black" , tags="grid",width=1)
            else:
                canvas_create_line(0, y, canvas_winfo_width,y, fill="gray" , tags="grid",width=1,dash = (5, 2))

        global dbarray_modified
        dbarray_modified=True

        global db_modified
        db_modified=True

        change_logf(current_logf)

def db2y(db):
    return canvas_winfo_height - ( canvas_winfo_height*(db-dbmin_display)/dbrange_display )

slower_update=False
def gui_update():
    if exiting:
        stream_in.stop()
        stream_in.close()
        stop_out()
        stream_out.close()

        root.withdraw()
        root.destroy()
        sys_exit(1)
    else:
        try:
            canvas_width=canvas_winfo_width

            global dbarray_modified
            if dbarray_modified:
                global spectrum_line_data
                #global spectrum_line

                for i,db in enumerate(spectrum_buckets):
                    i2=i+i
                    spectrum_line_data[i2:i2+2]=[x_min_audio+scale_factor_canvas_width_to_buckets_quant*i,db2y(db)]

                canvas.delete("spectrum")
                canvas.create_line(spectrum_line_data, fill="darkred" , width=2, smooth=0,tags="spectrum")
                dbarray_modified=False

            global db_modified
            if db_modified:
                global db_curr
                y=db2y(db_curr)

                canvas.delete("db_text")
                canvas.create_text(canvas_winfo_width_m20, y, text=str(round(db_curr))+"dB", anchor="center", font=("Arial", 8), tags=("db_text",'cursor'),fill="black")

                canvas.coords(cursor_db,0, y, canvas_width, y)

                db_modified=False

        except Exception as e:
            print("update_plot_error:",e)

        if slower_update:
            root.after(1,gui_update)
        else:
            root.after_idle(gui_update)

def xpixel_to_logf(x):
    return x /scale_factor_logf_to_pixels + logf_min

def scale_logf_to_pixels(logf):
    return scale_factor_logf_to_pixels * (logf - logf_min)

def scale_logf_to_buckets(logf):
    return round(scale_factor_logf_to_buckets * (logf - logf_min_audio))

def scale_bucket_to_logf(i):
    #return i/scale_factor_logf_to_buckets + logf_min_audio
    return (i+0.5)/scale_factor_logf_to_buckets + logf_min_audio

def change_logf(logf):
    global current_logf
    current_logf = logf

    f = 10**logf

    global phase_step
    phase_step = two_pi_by_samplerate * f

    canvas.delete("freq")

    x=scale_logf_to_pixels(logf)
    cursor_f_text=canvas.create_text(x+2, 2, text=str(round(f))+"Hz", anchor="nw", font=("Arial", 8), fill="black",tags=('cursor','freq'))

    canvas.coords(cursor_f, x, 0, x, canvas_winfo_height)

def audio_output_callback(outdata, frames, time, status):
    if status:
        print("status:",status)

    global phase
    phase_local=phase

    #print(blocksize_out,len(outdata))
    #samples = zeros(blocksize_out,dtype="float64")
    samples=zeros(blocksize_out,dtype="float32")

    ##############################
    for i in range(blocksize_out):
        samples[i]=sin(phase_local)

        phase_local += phase_step
        if phase_local > two_pi:
            phase_local -= two_pi

    phase=phase_local

    outdata[:] = samples.tobytes()

def sweep():
    stop_out()
    start_out()

    global current_logf
    current_logf=logf_min

    change_logf(logf_min_audio)

    flog_bucket_width=logf_max_audio_m_logf_min_audio/spectrum_buckets_quant

    global recording
    recording=True

    global sweeping
    sweeping=True

    global slower_update
    slower_update=True
    for i in range(spectrum_buckets_quant):
        logf=logf_min_audio+(i+0.3)*flog_bucket_width

        current_logf=logf
        change_logf(logf)
        status_var.set('Sweeping (' + str(round(10**logf))+ ' Hz) ...')

        root.update()
        root.after(100)

        if not sweeping:
            break

    sweeping=False
    status_var.set('Sweeping done.')

    stop_out()

    slower_update=False

    recording=False

def start_out():
    global stream_out_playing
    if not stream_out_playing:
        stream_out.start()
        stream_out_playing=True

def stop_out():
    global stream_out_playing
    if stream_out_playing:
        stream_out.stop()
        stream_out_playing=False

exiting=False
def close_app():
    global recording
    recording=False
    global sweeping
    sweeping=False
    global exiting
    exiting=True

def audio_input_callback(indata, frames, time_info, status):
    #print("audio_input_callback",frames,time_info,status)

    if status:
        return
    try:
        global record_blocks_index_to_replace
        record_blocks[record_blocks_index_to_replace]=np_mean(np_square(indata[:, 0], dtype=float64))

        #db_curr = 20 * log10(sqrt( np_mean(record_blocks) ) + 1e-12)

        global db_curr
        db_curr = 10 * log10( np_mean(record_blocks) + 1e-12)
        global db_modified

        db_modified=True

        if recording:
            i=round( scale_factor_logf_to_buckets * (current_logf - logf_min_audio) )
            if i>=0 and i<spectrum_buckets_quant:
                global spectrum_buckets
                spectrum_buckets[i]=db_curr

                global dbarray_modified
                dbarray_modified=True

        record_blocks_index_to_replace+=1
        record_blocks_index_to_replace%=record_blocks_len

    except Exception as e:
        print("audio_input_callback_error:",e)

VERSION_FILE='version.txt'

try:
    VER_TIMESTAMP=Path(os.path.join(os.path.dirname(__file__),VERSION_FILE)).read_text(encoding='ASCII').strip()
except Exception as e_ver:
    print(e_ver)
    VER_TIMESTAMP=''

fmin,fini,fmax=10,442,40000
fmin_audio,fmax_audio=20,20000

logf_min,logf_ini,logf_max=log10(fmin),log10(fini),log10(fmax)
logf_min_audio,logf_max_audio=log10(fmin_audio),log10(fmax_audio)

two_pi = pi+pi
spectrum_buckets_quant=256

logf_max_m_logf_min = logf_max-logf_min
logf_max_audio_m_logf_min_audio = logf_max_audio-logf_min_audio

dbmin_display=dbmin=-90.0
dbinit=-50.0
dbmax_display=dbmax=0.0

dbrange=dbmax-dbmin
db_margin=dbrange/4.0

dbrange_display=dbmax_display-dbmin_display

canvas_winfo_height=1
canvas_winfo_width=1

blocksize_out = 512
blocksize_in = 128

record_blocks_len=4
record_blocks=[0]*record_blocks_len
record_blocks_index_to_replace=0

dbarray_modified=True
db_modified=True

root = Tk()
root.protocol("WM_DELETE_WINDOW", close_app)

root.title(f"Small Audio Sweeper {VER_TIMESTAMP}")

style = Style()

ico = { img:PhotoImage(data = img_data) for img,img_data in image.items() }

theme_name='vista' if windows else 'clam',
try:
    style.theme_create( "dummy", parent=theme_name )
except Exception as e:
    print("cannot set theme - setting default")
    print(e)
    sys_exit(1)

bg_color = bg_color = style.lookup('TFrame', 'background')

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

style_map("TEntry",relief=[("disabled",'flat'),('','sunken')],borderwidth=[("disabled",0),('',2)])
style_map("TButton",  relief=[('disabled',"flat"),('',"raised")] )
style_map("TCheckbutton",relief=[('disabled',"flat"),('',"sunken")])

style_configure("TButton", anchor = "center")
style_configure("TCheckbutton",anchor='center',padding=(4, 0, 4, 0) )

if windows:
    #fix border problem ...
    style_configure("TCombobox",padding=1)

######################################

#for initialization only
scale_factor_logf_to_pixels=0

db=-24
y=db2y(db)

root.rowconfigure(1, weight=1)
root.columnconfigure(0, weight=1)

status_var = StringVar(value='Click and hold the mouse button on the spectrum graph...')

recording=False
sweeping=False

canvas = Canvas(root,height=300, width=800,relief='sunken',borderwidth=1,bg=bg_color)
canvas.grid(row=1, column=0, sticky="news", padx=4,pady=4)

canvas.bind("<Motion>", on_mouse_move)
canvas.bind("<ButtonPress>", on_mouse_press)
canvas.bind("<ButtonRelease>", on_mouse_release)

cursor_f = canvas.create_line(logf_ini, 0, logf_ini, y, width=2, fill="white", tags="cursor")
cursor_db = canvas.create_line(0, y, logf_max, y, width=10, fill="white", tags="cursor")

btns = Frame(root)
btns.grid(row=4, column=0, pady=4,padx=4,sticky="news")

button_sweep=Label(btns,textvariable=status_var,relief='sunken')
button_sweep.grid(row=0, column=0, padx=5,sticky='news')


button_sweep=Button(btns,image=ico['empty'],compound='center',text="▶", command=sweep)
button_sweep.grid(row=0, column=2, padx=5)

Button(btns,image=ico['empty'],compound='center', text="🖫",  command=save_csv).grid(row=0, column=14, padx=5)
Button(btns,image=ico['empty'],compound='center', text="💾",  command=save_image).grid(row=0, column=15, padx=5)

btns.columnconfigure(0,weight=1)

samplerate = 44100
phase = 0.0

two_pi_by_samplerate = two_pi/samplerate

current_logf=logf_ini

stream_in = InputStream( samplerate=samplerate, channels=1, dtype="float32", blocksize=blocksize_in, callback=audio_input_callback, latency="low" )
stream_out = RawOutputStream( samplerate=samplerate, channels=1,dtype='float32', blocksize=blocksize_out, callback=audio_output_callback, latency="low" )
stream_out_playing=False

spectrum_buckets=[dbinit]*spectrum_buckets_quant
spectrum_line_data=[0]*spectrum_buckets_quant*2

root.bind('<Configure>', root_configure)

stream_in.start()

root.after(200,gui_update)

root.mainloop()
