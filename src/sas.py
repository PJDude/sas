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

from tkinter import Tk,Toplevel,Frame, StringVar, Canvas, PhotoImage, LabelFrame
from tkinter.ttk import Button,Checkbutton,Style,Entry
from tkinter.filedialog import asksaveasfilename

from numpy import mean as np_mean,square as np_square,float64,float32, zeros, sin as np_sin, arange, pi as np_pi
from sounddevice import InputStream,OutputStream

from math import pi, sin, log10, ceil, floor
from PIL import ImageGrab,Image
from pathlib import Path
from time import strftime, localtime

import os
from os import name as os_name, system
from os.path import join as path_join, normpath,dirname

from sys import exit as sys_exit

from images import image
from dialogs import *

windows = bool(os_name=='nt')

if windows:
    from os import startfile

f_current=0

def status_set_frequency():
    status_var.set(str(round(f_current))+ ' Hz')

stream_out_playing=False
lock_frequency=False

def on_mouse_move(event):
    if not sweeping and not lock_frequency:
        logf=xpixel_to_logf(event.x)

        if logf<logf_max_audio and logf>logf_min_audio:
            change_logf(logf)
            status_set_frequency()
            global f_current
            f_current=10**logf

def recording_start():
    global recording
    recording=True

def lock_frequency_on():
    global lock_frequency
    lock_frequency=True

def lock_frequency_off():
    global lock_frequency
    lock_frequency=False

record_after=None

def on_mouse_press_1(event):
    global sweeping,record_after
    sweeping=False

    if lock_frequency:
        lock_frequency_off()
        play_stop()
        on_mouse_move(event)
    else:
        play_start()
        status_set_frequency()

    record_after=root.after(200,recording_start)

def on_mouse_press_3(event):
    global sweeping,record_after
    sweeping=False

    if lock_frequency:
        lock_frequency_off()
        play_stop()
        on_mouse_move(event)
    else:
        lock_frequency_off()
        on_mouse_move(event)
        lock_frequency_on()

        play_start()
        status_set_frequency()

        record_after=root.after(200,recording_start)

def on_mouse_release_1(event):
    global record_after,recording,sweeping
    root.after_cancel(record_after)
    lock_frequency_off()

    recording=False
    sweeping=False

    play_stop()
    status_set_frequency()

def on_mouse_release_3(event):
    global record_after,recording,sweeping
    root.after_cancel(record_after)

    recording=False
    sweeping=False

def on_mouse_scroll_win(event):
    fmod = int(-1 * (event.delta/120))
    scroll_mod(fmod)

def on_mouse_scroll_lin(event):
    if event.num == 4:
        fmod = -1
    elif event.num == 5:
        fmod = 1
    scroll_mod(fmod)

def scroll_mod(mod):
    if lock_frequency:
        global f_current
        if mod>0:
            f_new = ceil(f_current*1.01)
        else:
            f_new = floor(f_current*0.99)

        if f_new>0:
            log_f_new=log10(f_new)
            if log_f_new<logf_max_audio and log_f_new>logf_min_audio:
                change_logf(log_f_new)
                status_set_frequency()
                f_current=f_new

def save_csv():
    global slower_update
    slower_update=True

    time_postfix=strftime('%Y_%m_%d_%H_%M_%S',localtime())
    filename = asksaveasfilename(title = "Save CSV",initialfile = f'sas_{time_postfix}.csv',defaultextension=".csv",filetypes=[("All Files","*.*"),("CSV Files","*.csv")])

    if filename:
        try:
            with open(filename, 'w') as f:
                f.write("# Created with " + title + " #\n")
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
                global no_update
                no_update=True

                x1 = root.winfo_rootx() + canvas.winfo_x()
                y1 = root.winfo_rooty() + canvas.winfo_y()
                x2 = x1 + canvas.winfo_width()
                y2 = y1 + canvas.winfo_height()

                canvas.delete("freq")

                canvas.itemconfig('cursor', state='hidden')
                canvas.itemconfig('cursor_freq', state='hidden')

                canvas.delete("cursor_db_text")

                root.lift()
                root.attributes('-topmost', True)

                canvas.create_text(39, 3, text="Created with " + title, anchor="nw", font=("Arial", 8), fill=bg_color,tags=('mark'))
                canvas.create_text(39, 4, text="Created with " + title, anchor="nw", font=("Arial", 8), fill=bg_color,tags=('mark'))
                canvas.create_text(39, 5, text="Created with " + title, anchor="nw", font=("Arial", 8), fill=bg_color,tags=('mark'))
                canvas.create_text(41, 3, text="Created with " + title, anchor="nw", font=("Arial", 8), fill=bg_color,tags=('mark'))
                canvas.create_text(41, 4, text="Created with " + title, anchor="nw", font=("Arial", 8), fill=bg_color,tags=('mark'))
                canvas.create_text(41, 5, text="Created with " + title, anchor="nw", font=("Arial", 8), fill=bg_color,tags=('mark'))
                canvas.create_text(40, 3, text="Created with " + title, anchor="nw", font=("Arial", 8), fill=bg_color,tags=('mark'))
                canvas.create_text(40, 5, text="Created with " + title, anchor="nw", font=("Arial", 8), fill=bg_color,tags=('mark'))

                canvas.create_text(40, 4, text="Created with " + title, anchor="nw", font=("Arial", 8), fill="black",tags=('mark'))

                ###################################
                root.update()
                root.update_idletasks()
                root.after(200)

                ImageGrab.grab().crop((x1, y1, x2, y2)).save(filename)
                canvas.delete('mark')

                canvas.itemconfig('cursor', state='normal')

                change_logf(current_logf)

                root.attributes('-topmost', False)
                no_update=False
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
        global canvas_winfo_width,x_min_audio,canvas_winfo_width_m20,scale_factor_logf_to_pixels,scale_factor_logf_to_buckets,scale_factor_canvas_width_to_buckets_quant,canvas_winfo_height,canvas_winfo_height_m20,dbarray_modified,db_modified
        canvas_winfo_width=canvas.winfo_width()

        x_min_audio=scale_logf_to_pixels(logf_min_audio)
        x_max_audio=scale_logf_to_pixels(logf_max_audio)

        canvas_winfo_width_audio=x_max_audio-x_min_audio

        canvas_winfo_width_m20=canvas_winfo_width-20

        scale_factor_logf_to_pixels=canvas_winfo_width/logf_max_m_logf_min

        scale_factor_logf_to_buckets=spectrum_buckets_quant/logf_max_audio_m_logf_min_audio

        scale_factor_canvas_width_to_buckets_quant=canvas_winfo_width_audio/spectrum_buckets_quant

        canvas.delete("grid")

        canvas_winfo_height=canvas.winfo_height()
        canvas_winfo_height_m20=canvas_winfo_height-20

        canvas_create_line=canvas.create_line
        canvas_create_text=canvas.create_text
        for f,bold,lab in ((10,0,''),(20,2,'20Hz'),(30,0,''),(40,0,''),(50,0,''),(60,0,''),(70,0,''),(80,0,''),(90,0,''),(100,1,'100Hz'),
                    (200,0,''),(300,0,''),(400,0,''),(500,0,''),(600,0,''),(700,0,''),(800,0,''),(900,0,''),(1000,1,'1kHz'),
                    (2000,0,''),(3000,0,''),(4000,0,''),(5000,0,''),(6000,0,''),(7000,0,''),(8000,0,''),(9000,0,''),(10000,1,'10kHz'),
                    (20000,2,'20kHz'),(40000,1,'')):
            x=scale_logf_to_pixels(log10(f))

            if bold==2:
                canvas_create_line(x, 0, x, canvas_winfo_height, fill="gray20" , tags="grid",width=1, dash = (6, 4))
                canvas_create_text(x+2, canvas_winfo_height_m20, text=lab, anchor="nw", font=("Arial", 8), tags="grid")
            elif bold==1:
                canvas_create_line(x, 0, x, canvas_winfo_height, fill="gray20" , tags="grid",width=1, dash = (6, 4))
                canvas_create_text(x+2, canvas_winfo_height_m20, text=lab, anchor="nw", font=("Arial", 8), tags="grid")
            else:
                canvas_create_line(x, 0, x, canvas_winfo_height, fill="gray" , tags="grid",width=1,dash = (2, 4))

        for db,bold in ((10,0),(0,1),(-10,0),(-20,0),(-30,0),(-40,0),(-50,0),(-60,0),(-70,0),(-80,0),(-90,1)):
            y=db2y(db)

            canvas_create_text(6, y+4, text=str(db)+"dB", anchor="nw", font=("Arial", 8), tags="grid")
            if bold:
                canvas_create_line(0, y, canvas_winfo_width,y, fill="gray20" , tags="grid",width=1)
            else:
                canvas_create_line(0, y, canvas_winfo_width,y, fill="gray" , tags="grid",width=1,dash = (2, 4))

        dbarray_modified=True
        db_modified=True

        change_logf(current_logf)

def db2y(db):
    return canvas_winfo_height - ( canvas_winfo_height*(db-dbmin_display)/dbrange_display )

slower_update=False
def gui_update():
    if exiting:
        stream_in.stop()
        stream_in.close()
        play_stop()
        stream_out.close()

        root.withdraw()
        root.destroy()
        sys_exit(1)
    elif no_update:
        root.after(1,gui_update)
    else:
        try:
            canvas_width=canvas_winfo_width

            global dbarray_modified,db_modified
            if dbarray_modified:
                spectrum_line_data=[0]*spectrum_buckets_quant*2

                for i,db in enumerate(spectrum_buckets):
                    i2=i+i
                    spectrum_line_data[i2:i2+2]=[x_min_audio+scale_factor_canvas_width_to_buckets_quant*i,db2y(db)]

                canvas.delete("spectrum")
                canvas.create_line(spectrum_line_data, fill="black" , width=1, smooth=1,tags="spectrum")
                dbarray_modified=False

            if db_modified:
                global db_curr
                y=db2y(db_curr)

                canvas.delete("cursor_db_text")
                canvas.create_text(canvas_winfo_width_m20, y, text=str(round(db_curr))+"dB", anchor="center", font=("Arial", 8), tags=("cursor_db_text"),fill="black")

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
    return (i+0.5)/scale_factor_logf_to_buckets + logf_min_audio

def change_logf(logf):
    global current_logf, phase_step, generated_logf
    current_logf = logf

    f = 10**logf

    phase_step = two_pi_by_samplerate * f

    canvas.delete("cursor_freq")

    x=scale_logf_to_pixels(logf)

    cursor_f_text=canvas.create_text(x+2, 2, text=str(round(f))+"Hz", anchor="nw", font=("Arial", 8), fill="black",tags=('cursor_freq'))

    canvas.coords(cursor_f, x, 0, x, canvas_winfo_height)

played_bucket=0
played_bucket_callbacks=0

def audio_output_callback(outdata, frames, time, status):
    global phase,phase_step
    for i in range(blocksize_out):
        outdata[i,0]=sin(phase)
        phase += phase_step
        phase %= two_pi

    bucket=scale_logf_to_buckets(log10(phase_step / two_pi_by_samplerate))

    global played_bucket,played_bucket_callbacks

    if bucket!=played_bucket:
        played_bucket_callbacks=0
        played_bucket=bucket

    played_bucket_callbacks+=1

def sweep():
    play_stop()
    play_start()

    global current_logf,recording,sweeping,slower_update
    current_logf=logf_min

    change_logf(logf_min_audio)

    flog_bucket_width=logf_max_audio_m_logf_min_audio/spectrum_buckets_quant

    recording=True
    sweeping=True

    slower_update=True
    for i in range(spectrum_buckets_quant):
        logf=logf_min_audio+(i+0.3)*flog_bucket_width

        current_logf=logf
        change_logf(logf)
        status_var.set('Sweeping (' + str(round(10**logf))+ ' Hz), Click on the graph to abort ...')

        root.update()
        root.after(int(1000*time_to_collect_sample*1.5))

        if not sweeping:
            break

    sweeping=False
    status_var.set('Sweeping done.')

    play_stop()

    slower_update=False

    recording=False

def play_start():
    global stream_out_playing
    if not stream_out_playing:
        stream_out.start()
        stream_out_playing=True
        canvas.itemconfig(cursor_f, fill='red')


def play_stop():
    global stream_out_playing
    if stream_out_playing:
        stream_out.stop()
        stream_out_playing=False
        canvas.itemconfig(cursor_f, fill='white')

exiting=False
no_update=False

def close_app():
    global recording,sweeping,exiting
    recording=False
    sweeping=False
    exiting=True

def audio_input_callback(indata, frames, time_info, status):
    #print("audio_input_callback",frames,time_info,status)

    if status:
        print(status)
        return

    try:
        global record_blocks,record_blocks_index_to_replace,db_curr,db_modified,spectrum_buckets,dbarray_modified

        this_callback_mean=np_mean(np_square(indata[:, 0], dtype=float64))

        if recording or lock_frequency:
            record_blocks[record_blocks_index_to_replace]=this_callback_mean
            record_blocks_index_to_replace+=1
            record_blocks_index_to_replace%=record_blocks_len

            #db_curr = 20 * log10(sqrt( np_mean(record_blocks) ) + 1e-12)
            db_curr = 10 * log10( np_mean(record_blocks) + 1e-12)
        else:
            db_curr = 10 * log10( this_callback_mean + 1e-12)

        db_modified=True

        if recording or lock_frequency:
            if played_bucket_callbacks>record_blocks_len:
                i=round( scale_factor_logf_to_buckets * (current_logf - logf_min_audio) )
                if i>=0 and i<spectrum_buckets_quant:
                    spectrum_buckets[i]=db_curr
                    dbarray_modified=True

    except Exception as e:
        print("audio_input_callback_error:",e)

def go_to_homepage():
    try:
        if windows:
            status_var.set('opening: %s' % HOMEPAGE)
            startfile(HOMEPAGE)
        else:
            status_var.set('executing: xdg-open %s' % HOMEPAGE)
            system("xdg-open " + HOMEPAGE)
    except Exception as e:
        print('go_to_homepage error:',e)

dialog_shown=False

def pre_show(new_widget=None):
    global dialog_shown
    dialog_shown=True

def post_close():
    global slower_update,dialog_shown
    slower_update=False
    dialog_shown=False

about_dialog_created = False
def get_about_dialog():
    global slower_update,about_dialog_created,about_dialog
    slower_update=True

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
    global slower_update
    slower_update=True

    get_about_dialog().show()

license_dialog_created=False
def get_license_dialog():
    global slower_update, license_dialog, license_dialog_created
    slower_update=True

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
    global slower_update
    slower_update=True

    get_license_dialog().show()

VERSION_FILE='version.txt'

HOMEPAGE='https://github.com/PJDude/sas'

try:
    VER_TIMESTAMP=Path(os.path.join(os.path.dirname(__file__),VERSION_FILE)).read_text(encoding='ASCII').strip()
except Exception as e_ver:
    print(e_ver)
    VER_TIMESTAMP=''

samplerate = 44100

fmin,fini,fmax=10,442,40000
fmin_audio,fmax_audio=20,20000

logf_min,logf_ini,logf_max=log10(fmin),log10(fini),log10(fmax)
logf_min_audio,logf_max_audio=log10(fmin_audio),log10(fmax_audio)

two_pi = pi+pi
two_pi_np = np_pi+np_pi

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

blocksize_out = 128
blocksize_in = 128

time_to_collect_sample=0.125 #[s]
#1/4s - 86 paczek
#record_blocks_len=int((samplerate/4)/blocksize_in)

# 43
record_blocks_len=int((samplerate*time_to_collect_sample)/blocksize_in)

record_blocks=[0]*record_blocks_len
record_blocks_index_to_replace=0

dbarray_modified=True
db_modified=True

root = Tk()
root.protocol("WM_DELETE_WINDOW", close_app)

title=f"Simple Audio Sweeper {VER_TIMESTAMP}"
root.title(title)

style = Style()

ico = { img:PhotoImage(data = img_data) for img,img_data in image.items() }

ico_sas = ico['sas']
ico_sas_small = ico['sas_small']

main_icon_tuple = (ico_sas,ico_sas_small)

root.iconphoto(True, *main_icon_tuple)

theme_name='vista' if windows else 'clam',
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

style_map("TEntry",relief=[("disabled",'flat'),('','sunken')],borderwidth=[("disabled",0),('',2)])
style_map("TButton",  relief=[('disabled',"flat"),('',"raised")] )
style_map("TCheckbutton",relief=[('disabled',"flat"),('',"sunken")])

style_configure("TButton", anchor = "center")
style_configure("TCheckbutton",anchor='center',padding=(4, 0, 4, 0) )

if windows:
    #fix border problem ...
    style_configure("TCombobox",padding=1)

def widget_tooltip(widget,message,type_info_or_help=True):
    widget.bind("<Motion>", lambda event : status_var.set(message))
    widget.bind("<Leave>", lambda event : status_var.set(default_status))

APP_FILE = normpath(__file__)
APP_DIR = dirname(APP_FILE)

try:
    distro_info=Path(path_join(APP_DIR,'distro.info.txt')).read_text()
except Exception as exception_1:
    print(exception_1)
    distro_info = 'Error. No distro.info.txt file.'
else:
    print(f'distro info:\n{distro_info}')

#for initialization only
scale_factor_logf_to_pixels=0

db=-24
y=db2y(db)

root.rowconfigure(1, weight=1)
root.columnconfigure(0, weight=1)

default_status='Click and hold the mouse button on the spectrum graph...'
status_var = StringVar(value=default_status)

recording=False
sweeping=False

canvas = Canvas(root,height=300, width=800,relief='sunken',borderwidth=1,bg=bg_color)
canvas.grid(row=1, column=0, sticky="news", padx=4,pady=4)

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


cursor_f = canvas.create_line(logf_ini, 0, logf_ini, y, width=2, fill="white", tags="cursor")
cursor_db = canvas.create_line(0, y, logf_max, y, width=10, fill="white", tags="cursor")

btns = Frame(root,bg=bg_color)
btns.grid(row=4, column=0, pady=4,padx=4,sticky="news")

Label(btns,textvariable=status_var,relief='sunken', anchor='nw',bd=1).grid(row=0, column=0, padx=5,sticky='news')

sweep_button=Button(btns,image=ico['play'], command=sweep)
sweep_button.grid(row=0, column=1, padx=5)

widget_tooltip(sweep_button,'Run frequency sweep.')

Label(btns,image=ico['empty'],relief='flat').grid(row=0, column=2, padx=5,sticky='news')

csv_button=Button(btns,image=ico['csv'], command=save_csv)
csv_button.grid(row=0, column=3, padx=5)
widget_tooltip(csv_button,'Save CSV file')

image_button=Button(btns,image=ico['save'], command=save_image)
image_button.grid(row=0, column=4, padx=5)
widget_tooltip(image_button,'Save Image file')

Label(btns,image=ico['empty'],relief='flat').grid(row=0, column=5, padx=4,sticky='news')

home_button=Button(btns,image=ico['home'], command=go_to_homepage)
home_button.grid(row=0, column=6, padx=5)
widget_tooltip(home_button,f'Visit project homepage ({HOMEPAGE})')

license_button=Button(btns,image=ico['license'], command=license_wrapper )
license_button.grid(row=0, column=7, padx=5)
widget_tooltip(license_button,'Show License')

about_button=Button(btns,image=ico['about'],  command=about_wrapper )
about_button.grid(row=0, column=8, padx=5)
widget_tooltip(about_button,'About')

btns.columnconfigure(0,weight=1)

phase = 0.0

two_pi_by_samplerate = two_pi/samplerate

current_logf=logf_ini

stream_out = OutputStream( samplerate=samplerate, channels=1, dtype='float32', blocksize=blocksize_out, callback=audio_output_callback, latency="low" )
stream_in = InputStream( samplerate=samplerate, channels=1, dtype="float32", blocksize=blocksize_in, callback=audio_input_callback, latency="low" )

spectrum_buckets=[dbinit]*spectrum_buckets_quant

root.bind('<Configure>', root_configure)
root.bind('<F1>', lambda event : about_wrapper() )

stream_in.start()

root.after(200,gui_update)

root.mainloop()
