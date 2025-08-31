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
from tkinter import Tk,DoubleVar, BooleanVar, IntVar, Canvas, PhotoImage
from tkinter.ttk import Frame,Label,Scale,Button,Checkbutton,Radiobutton,Style,Entry

from sounddevice import InputStream,RawOutputStream
from math import pi, sin, log10

from numpy import mean as np_mean,square as np_square,float64,float32, min as np_min, max as np_max, zeros, arange, sin as np_sin

from PIL import ImageGrab,Image

from tkinter.filedialog import asksaveasfilename

from pathlib import Path

from time import strftime, localtime

import os
from os import name as os_name
from sys import exit as sys_exit

from images import image

windows = bool(os_name=='nt')

VERSION_FILE='version.txt'

def get_ver_timestamp():
    try:
        timestamp=Path(os.path.join(os.path.dirname(__file__),VERSION_FILE)).read_text(encoding='ASCII').strip()
    except Exception as e_ver:
        print(e_ver)
        timestamp=''
    return timestamp

VER_TIMESTAMP = get_ver_timestamp()

class SimpleAudioSweeper:
    fmin,fini,fmax=10,442,40000
    fmin_audio,fmax_audio=20,20000

    log10fmin,log10fini,log10fmax=log10(fmin),log10(fini),log10(fmax)
    log10fmin_audio,log10fmax_audio=log10(fmin_audio),log10(fmax_audio)

    two_pi = pi+pi
    frequency_buckets_quant=256

    log10fmax_m_log10fmin = log10fmax-log10fmin
    log10fmax_audio_m_log10fmin_audio = log10fmax_audio-log10fmin_audio

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

    def __init__(self, root):
        self.root = root
        self.root.title(f"Small Audio Sweeper {VER_TIMESTAMP}")

        style = Style()

        self_ico = self.ico = { img:PhotoImage(data = img_data) for img,img_data in image.items() }

        theme_name='vista' if windows else 'clam',
        try:
            style.theme_create( "dummy", parent=theme_name )
        except Exception as e:
            print("cannot set theme - setting default")
            print(e)
            #self.cfg.set(CFG_THEME,self.default_theme)
            sys_exit(1)

        bg_color = self.bg_color = style.lookup('TFrame', 'background')

        style.theme_use("dummy")
        style_map = style.map

        style_configure = style.configure

        #works but not for every theme

        style_map("TCheckbutton",indicatorbackground=[("disabled",self.bg_color),('','white')],indicatorforeground=[("disabled",'darkgray'),('','black')],foreground=[('disabled',"gray"),('',"black")])
        style_map("TEntry", foreground=[("disabled",'darkgray'),('','black')],fieldbackground=[("disabled",self.bg_color),('','white')])

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
        self.scale_freq_factor_pixels=0

        self.db=-24
        y=self.db2y(self.db)

        root.rowconfigure(1, weight=1)
        root.columnconfigure(0, weight=1)

        self.log10freq_var = DoubleVar(value=self.log10fini)
        self.recording_var = BooleanVar(value=False)
        self.mode_var = IntVar(value=0)

        self.log10freq_var_get=self.log10freq_var.get
        self.log10freq_var_set=self.log10freq_var.set

        self.slider = Scale(root, from_=self.log10fmin, to=self.log10fmax, variable=self.log10freq_var, command=self.scale_mod)
        self.slider.grid(row=0, column=0, sticky="news", padx=10,pady=3)

        self.canvas = Canvas(root,height=300, width=800,relief='sunken',borderwidth=1,bg=self.bg_color)
        self.canvas.grid(row=1, column=0, sticky="news", padx=20,pady=3)

        self.cursor_f = self.canvas.create_line(self.log10fini, 0, self.log10fini, y, width=2, fill="white", tags="cursor")
        self.cursor_db = self.canvas.create_line(0, y, self.log10fmax, y, width=10, fill="white", tags="cursor")

        btns = Frame(root)
        btns.grid(row=4, column=0, pady=10,sticky="ewns")

        Radiobutton(btns,text="Manual Frequency", variable=self.mode_var, value=0, command=self.mode_set).grid(row=0, column=0, padx=5)
        self.button_play=Button(btns,image=self_ico['empty'],compound='center', text="▶", command=self.start_out)
        self.button_play.grid(row=0, column=1, padx=5)

        self.button_stop=Button(btns,image=self_ico['empty'],compound='center', text="⏹", command=self.stop_out)
        self.button_stop.grid(row=0, column=2, padx=5)

        self.cb_rec=Checkbutton(btns, text="Rec",  variable=self.recording_var,width=3,command=self.recording_var_toggle)
        self.cb_rec.grid(row=0, column=3, padx=5)

        Radiobutton(btns,text="Frequency Sweep", variable=self.mode_var, value=1, command=self.mode_set).grid(row=0, column=6, padx=5)
        self.button_sweep=Button(btns,image=self_ico['empty'],compound='center',text="▶", command=self.sweep)
        self.button_sweep.grid(row=0, column=7, padx=5)

        Radiobutton(btns,text="FFT", variable=self.mode_var, value=2, command=self.mode_set,state='disabled').grid(row=0, column=10, padx=5)

        Button(btns,image=self_ico['empty'],compound='center', text="🖫",  command=self.save_csv).grid(row=0, column=14, padx=5)
        Button(btns,image=self_ico['empty'],compound='center', text="💾",  command=self.save_image).grid(row=0, column=15, padx=5)

        self.recording_var_toggle()

        btns.columnconfigure(4,weight=1)
        btns.columnconfigure(9,weight=1)
        btns.columnconfigure(13,weight=1)

        self.samplerate = 44100
        self.phase = 0.0

        self.two_pi_by_samplerate = self.two_pi/self.samplerate

        self.current_log10freq=self.log10fini
        self.current_log10freq_scalex=self.scalex(self.current_log10freq)

        self.current_freq = self.fini

        self.slider.set(self.log10fini)

        self.stream_in = InputStream( samplerate=self.samplerate, channels=1, dtype="float32", blocksize=self.blocksize_in, callback=self.audio_input_callback, latency="low" )
        self.stream_out = RawOutputStream( samplerate=self.samplerate, channels=1,dtype='float32', blocksize=self.blocksize_out, callback=self.audio_output_callback, latency="low" )
        self.stream_out_playing=False

        self.internal_dbarray=[self.dbinit]*self.frequency_buckets_quant
        self.spectrum_line_data=[0]*self.frequency_buckets_quant*2

        self.dbarray_modified=True
        self.db_modified=True

        self.root.bind('<Configure>', self.root_configure)

        self.stream_in.start()

    def mode_set(self):
        mode=self.mode_var.get()

        if mode==0:
            self.slider.configure(state='normal')
            self.log10freq_var_set(self.log10fini)
            self.scale_mod(self.log10fini)
            self.button_play.configure(state='normal')
            self.button_stop.configure(state='normal')
            self.cb_rec.configure(state='normal')
            self.button_sweep.configure(state='disabled')

        elif mode==1:
            self.slider.configure(state='disabled')
            self.log10freq_var_set(self.log10fmin_audio)
            self.scale_mod(self.log10fmin_audio)
            self.button_play.configure(state='disabled')
            self.button_stop.configure(state='disabled')
            self.cb_rec.configure(state='disabled')
            self.button_sweep.configure(state='normal')
            self.stop_out()

        elif mode==2:
            self.slider.configure(state='disabled')
            self.log10freq_var_set(self.log10fmin_audio)
            self.scale_mod(self.log10fmin_audio)
            self.button_play.configure(state='disabled')
            self.button_stop.configure(state='disabled')
            self.cb_rec.configure(state='disabled')
            self.button_sweep.configure(state='disabled')
            self.stop_out()

        else:
            print("unknown mode:",mode)
            self.slider.configure(state='disabled')

    def recording_var_toggle(self):
        self.recording=self.recording_var.get()
        #print(f'{self.recording=}')

    def save_csv(self):
        self.slower_update=True
        time_postfix=strftime('%Y_%m_%d_%H_%M_%S',localtime())
        filename = asksaveasfilename(title = "Save CSV",initialfile = f'sas_{time_postfix}.csv',defaultextension=".csv",filetypes=[("All Files","*.*"),("CSV Files","*.csv")])
        if filename:
            print("save_csv:",filename)

        self.slower_update=False

    def save_image(self):
        self.slower_update=True
        time_postfix=strftime('%Y_%m_%d_%H_%M_%S',localtime())
        filename = asksaveasfilename(title = "Save Image",initialfile = f'sas_{time_postfix}.png',defaultextension=".png",filetypes=[("All Files","*.*"),("PNG Files","*.png")])

        if filename:
            if os.path.exists(filename):
                print("Name already exists!")
            else:
                path, file = os.path.split(filename)
                name, ext = os.path.splitext(file)

                if ext.lower() in ['.gif', '.png']:
                    x1 = root.winfo_rootx() + self.canvas.winfo_x()
                    y1 = root.winfo_rooty() + self.canvas.winfo_y()
                    x2 = x1 + self.canvas.winfo_width()
                    y2 = y1 + self.canvas.winfo_height()

                    self.canvas.itemconfig(self.cursor_f, state='hidden')
                    self.canvas.itemconfig(self.cursor_f_text, state='hidden')
                    self.canvas.itemconfig(self.cursor_db, state='hidden')
                    self.root.lift()
                    self.root.attributes('-topmost', True)

                    ###################################
                    self.root.update()
                    self.root.update_idletasks()
                    root.after(200)

                    ImageGrab.grab().crop((x1, y1, x2, y2)).save(filename)

                    self.canvas.itemconfig(self.cursor_f, state='normal')
                    self.canvas.itemconfig(self.cursor_f_text, state='normal')
                    self.canvas.itemconfig(self.cursor_db, state='normal')
                    self.root.attributes('-topmost', False)
                    ###################################
                else:
                    print("Unknown file type")
        else:
            print("Cancel")

        self.slower_update=False

    def clear(self):
        self.canvas.delete("fline")

    canvas_width_to_internal_samples_quant_factor=1
    canvas_winfo_width_m20=1

    def root_configure(self,event=None):
        if not self.exiting:
            #self.root.update()

            canvas=self.canvas
            canvas_create_line=canvas.create_line
            canvas_create_text=canvas.create_text

            canvas_winfo_width=self.canvas_winfo_width=canvas.winfo_width()
            self.canvas_winfo_width_m20=canvas_winfo_width-20

            self.scale_freq_factor_pixels=canvas_winfo_width/self.log10fmax_m_log10fmin
            self.scale_freq_factor_buckets=self.frequency_buckets_quant/self.log10fmax_m_log10fmin
            self.canvas_width_to_internal_samples_quant_factor=canvas_winfo_width/self.frequency_buckets_quant

            canvas.delete("grid")

            canvas_winfo_height=self.canvas_winfo_height=canvas.winfo_height()
            canvas_winfo_height_m20=canvas_winfo_height-20

            self_scalex=self.scalex
            for f,bold,lab in ((10,0,''),(20,1,'20Hz'),(30,0,''),(40,0,''),(50,0,''),(60,0,''),(70,0,''),(80,0,''),(90,0,''),(100,1,'100Hz'),
                        (200,0,''),(300,0,''),(400,0,''),(500,0,''),(600,0,''),(700,0,''),(800,0,''),(900,0,''),(1000,1,'1kHz'),
                        (2000,0,''),(3000,0,''),(4000,0,''),(5000,0,''),(6000,0,''),(7000,0,''),(8000,0,''),(9000,0,''),(10000,1,'10kHz'),
                        (20000,1,'20kHz'),(40000,1,'')):
                x=self_scalex(log10(f))

                if bold:
                    canvas_create_line(x, 0, x, canvas_winfo_height, fill="black" , tags="grid",width=1)
                    canvas_create_text(x+2, canvas_winfo_height_m20, text=lab, anchor="nw", font=("Arial", 8), tags="grid")
                else:
                    canvas_create_line(x, 0, x, canvas_winfo_height, fill="gray" , tags="grid",width=1,dash = (5, 2))

            #canvas.delete("grid_db")

            self_db2y=self.db2y
            for db,bold in ((10,0),(0,1),(-10,0),(-20,0),(-30,0),(-40,0),(-50,0),(-60,0),(-70,0),(-80,0),(-90,1)):
                y=self_db2y(db)

                canvas_create_text(6, y+4, text=str(db)+"dB", anchor="nw", font=("Arial", 8), tags="grid")
                if bold:
                    canvas_create_line(0, y, canvas_winfo_width,y, fill="black" , tags="grid",width=1)
                else:
                    canvas_create_line(0, y, canvas_winfo_width,y, fill="gray" , tags="grid",width=1,dash = (5, 2))

            self.dbarray_modified=True
            self.db_modified=True

            self.scale_mod(self.current_log10freq)

    def db2y(self,db):
        #return self.canvas_winfo_height - ( self.canvas_winfo_height*(db-self.dbmin_display)/self.dbrange_display )
        return self.canvas_winfo_height - ( self.canvas_winfo_height*(db-self.dbmin_display)/self.dbrange_display )

    slower_update=False
    def gui_update(self):
        if self.exiting:
            self.stream_in.stop()
            self.stream_in.close()
            self.stop_out()
            self.stream_out.close()

            self.root.withdraw()
            self.root.destroy()
            sys_exit(1)
        else:
            try:
                self_canvas=self.canvas
                self_db2y=self.db2y
                canvas_width=self.canvas_winfo_width
                x_factor=self.canvas_width_to_internal_samples_quant_factor

                if self.dbarray_modified:
                    spectrum_line_data=self.spectrum_line_data

                    for x,db in enumerate(self.internal_dbarray):
                        x2=x+x
                        spectrum_line_data[x2:x2+2]=[x_factor*x,self_db2y(db)]

                    try:
                        self_canvas.delete(self.spectrum_line)
                    except:
                        pass
                    finally:
                        self.spectrum_line=self_canvas.create_line(spectrum_line_data, fill="darkred" , width=2, smooth=0)
                        self.dbarray_modified=False

                if self.db_modified:
                    y=self_db2y(self.db)

                    self_canvas.delete("db_text")
                    self_canvas.create_text(self.canvas_winfo_width_m20, y, text=str(round(self.db))+"dB", anchor="center", font=("Arial", 8), tags="db_text",fill="black")

                    self_canvas.coords(self.cursor_db,0, y, canvas_width, y)
                    self.db_modified=False

            except Exception as e:
                print("update_plot_error:",e)

            if self.slower_update:
                self.root.after(1,self.gui_update)
            else:
                self.root.after_idle(self.gui_update)

    def scalex(self,x):
        return self.scale_freq_factor_pixels * (x - self.log10fmin)

    def scale_freq(self,f):
        return round(self.scale_freq_factor_buckets * (f - self.log10fmin))

    def scale_mod(self,log10freq):
        self.current_log10freq = float(log10freq)
        x=self.current_log10freq_scalex=self.scalex(self.current_log10freq)

        self.current_freq = 10**self.current_log10freq
        self.phaseinc = self.two_pi_by_samplerate * self.current_freq

        y=self.canvas_winfo_height

        self.canvas.delete("freq")
        self.cursor_f_text=self.canvas.create_text(x+2, 2, text=str(round(self.current_freq))+"Hz", anchor="nw", font=("Arial", 8), tags="freq",fill="black")

        self.canvas.coords(self.cursor_f, x, 0, x, y)

    def audio_output_callback(self, outdata, frames, time, status):
        if status:
            print("status:",status)

        phase = self.phase

        self_phaseinc = self.phaseinc
        self_two_pi = self.two_pi

        #print(self.blocksize_out,len(outdata))
        #self.samples = zeros(self.blocksize_out,dtype="float64")
        #self_samples=self.samples
        self_samples=zeros(self.blocksize_out,dtype="float32")

        ##############################
        for i in range(self.blocksize_out):
            self_samples[i]=sin(phase)

            phase += self_phaseinc
            if phase > self_two_pi:
                phase -= self_two_pi

        self.phase = phase

        outdata[:] = self_samples.tobytes()

    def sweep(self):
        self.stop_out()
        self.start_out()
        self.current_log10freq=self.log10fmin
        self.log10freq_var_set(self.log10fmin)
        self.scale_mod(self.log10fmin)

        flog_bucket=self.log10fmax_audio_m_log10fmin_audio/self.frequency_buckets_quant

        self.recording_var.set(True)
        self.recording_var_toggle()

        self.slower_update=True
        for x in range(self.frequency_buckets_quant):
            logf=self.log10fmin_audio+x*flog_bucket

            self.current_log10freq=logf
            self.log10freq_var_set(logf)
            self.scale_mod(logf)
            self.root.update()
            self.root.after(100)

        self.stop_out()

        self.slower_update=False

        self.recording_var.set(False)
        self.recording_var_toggle()

    def start_out(self):
        if not self.stream_out_playing:
            self.stream_out.start()
            self.stream_out_playing=True

    def stop_out(self):
        if self.stream_out_playing:
            self.stream_out.stop()
            self.stream_out_playing=False

    exiting=False
    def close_app(self):
        self.exiting=True

    def audio_input_callback(self, indata, frames, time_info, status):
        #print("audio_input_callback",frames,time_info,status)

        if status:
            return
        try:
            block_mean=np_mean(np_square(indata[:, 0], dtype=float64))
            self.record_blocks[self.record_blocks_index_to_replace]=block_mean

            #self.db = 20 * log10(sqrt(block_mean) + 1e-12)

            #self.db = 20 * log10(sqrt( np_mean(self.record_blocks) ) + 1e-12)
            self.db = 10 * log10( np_mean(self.record_blocks) + 1e-12)
            self.db_modified=True

            if self.recording:
                self.internal_dbarray[self.scale_freq(self.current_log10freq)]=self.db
                self.dbarray_modified=True

            self.record_blocks_index_to_replace+=1
            self.record_blocks_index_to_replace%=self.record_blocks_len

        except Exception as e:
            print("audio_input_callback_error:",e)

if __name__ == "__main__":
    root = Tk()
    app = SimpleAudioSweeper(root)
    root.protocol("WM_DELETE_WINDOW", app.close_app)
    root.after(200,app.gui_update)

    root.mainloop()
