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

from tkinter import DoubleVar, BooleanVar, IntVar, Canvas

from tkinter.ttk import Frame,Label,Scale,Button,Checkbutton,Radiobutton,Style,Entry

from sounddevice import InputStream,RawOutputStream
from math import pi, sin, log10, sqrt

from numpy import mean,square,float64,float32, min as np_min, max as np_max, zeros, arange, sin as np_sin

from sys import exit as sys_exit

from PIL import ImageGrab,Image

from tkinter.filedialog import asksaveasfilename

import os

from tkinter import Tk

from time import strftime, localtime

from os import name as os_name

# sep,stat,scandir,readlink,rmdir,system,getcwd,

windows = bool(os_name=='nt')

class SimpleAudioSweeper:
    fmin,fini,fmax=10,442,40000
    fmin_audio,fmax_audio=20,20000

    log10fmin,log10fini,log10fmax=log10(fmin),log10(fini),log10(fmax)
    log10fmin_audio,log10fmax_audio=log10(fmin_audio),log10(fmax_audio)

    two_pi = 2.0 * pi
    internal_samples_quant=200

    log10fmax_m_log10fmin = log10fmax-log10fmin
    log10fmax_audio_m_log10fmin_audio = log10fmax_audio-log10fmin_audio

    dbmin_display=dbmin=-90.0
    dbinit=-50.0
    dbmax_display=dbmax=0.0

    dbrange=dbmax-dbmin
    db_margin=dbrange/4.0

    dbrange_display=1

    def dbrange_change(self):
        self.dbrange_display=self.dbmax_display-self.dbmin_display
        self.draw_db_grid()

    canvas_winfo_height=1
    canvas_winfo_width=1

    blocksize_play = 512
    #blocksize_record = 4096

    blocksize_record = 128
    record_blocks=[0,0,0,0,0,0]

    def __init__(self, root):
        self.root = root
        self.root.title("Small Audio Sweeper v1.0001")

                ######################################
        style = Style()

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
        self.scalex_factor=0

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

        self.dbrange_change()

        btns = Frame(root)
        btns.grid(row=4, column=0, pady=10,sticky="ewns")

        Radiobutton(btns,text="Manual Frequency", variable=self.mode_var, value=0, command=self.mode_set).grid(row=0, column=0, padx=5)
        self.button_play=Button(btns, text="▶", command=self.start,width=2)
        self.button_play.grid(row=0, column=1, padx=5)

        self.button_stop=Button(btns, text="▪",  command=self.stop,width=2)
        self.button_stop.grid(row=0, column=2, padx=5)

        self.cb_rec=Checkbutton(btns, text="Rec",  variable=self.recording_var,width=3,command=self.recording_var_toggle)
        self.cb_rec.grid(row=0, column=3, padx=5)

        Radiobutton(btns,text="Frequency Sweep", variable=self.mode_var, value=1, command=self.mode_set).grid(row=0, column=6, padx=5)
        self.button_sweep=Button(btns, text="▶▶▶", command=self.sweep,width=4)
        self.button_sweep.grid(row=0, column=7, padx=5)

        Radiobutton(btns,text="FFT", variable=self.mode_var, value=2, command=self.mode_set).grid(row=0, column=10, padx=5)

        Button(btns, text="S",  command=self.save,width=2).grid(row=0, column=15, padx=5)

        self.recording_var_toggle()

        btns.columnconfigure(4,weight=1)
        btns.columnconfigure(9,weight=1)
        btns.columnconfigure(14,weight=1)

        self.samplerate = 44100
        self.stream = None
        self.phase = 0.0

        self.two_pi_by_samplerate = self.two_pi/self.samplerate

        self.running = False

        self.current_log10freq=self.log10fini
        self.current_log10freq_scalex=self.scalex(self.current_log10freq)

        self.current_freq = self.fini

        self.slider.set(self.log10fini)

        #self.samples = array('f',[0] * self.blocksize_play)
        #self.samples = zeros(self.blocksize_play,dtype="float64")

        self.stream_in = InputStream(
            samplerate=self.samplerate, channels=1, dtype="float32",
            blocksize=self.blocksize_record, callback=self.mic_callback
        )
        self.initialize_internal_dbarray()

        self.stream_in.start()

        self.root.bind('<Configure>', self.root_configure)

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
            self.stop()

        elif mode==2:
            self.slider.configure(state='disabled')
            self.log10freq_var_set(self.log10fmin_audio)
            self.scale_mod(self.log10fmin_audio)
            self.button_play.configure(state='disabled')
            self.button_stop.configure(state='disabled')
            self.cb_rec.configure(state='disabled')
            self.button_sweep.configure(state='disabled')
            self.stop()

        else:
            print("unknown mode:",mode)
            self.slider.configure(state='disabled')

    def recording_var_toggle(self):
        self.recording=self.recording_var.get()
        #print(f'{self.recording=}')

    def save(self):
        #%Y_%m_%d_
        time_postfix=strftime('%H_%M_%S',localtime())
        filename = asksaveasfilename(title = "Save Image",initialfile = f'sas_image_{time_postfix}.png',defaultextension=".png",filetypes=[("All Files","*.*"),("PNG Files","*.png")])

        if filename:
            if os.path.exists(filename):
                print("Name already exists!")
            else:
                path, file = os.path.split(filename)
                name, ext = os.path.splitext(file)

                #self.canvas.update()

                if ext.lower() in ['.gif', '.png']:
                    x1 = root.winfo_rootx() + self.canvas.winfo_x()
                    y1 = root.winfo_rooty() + self.canvas.winfo_y()
                    x2 = x1 + self.canvas.winfo_width()
                    y2 = y1 + self.canvas.winfo_height()

                    self.canvas.itemconfig(self.cursor_f, state='hidden')
                    self.canvas.itemconfig(self.cursor_db, state='hidden')
                    self.root.lift()
                    self.root.attributes('-topmost', True)

                    ###################################
                    self.root.update()
                    self.root.update_idletasks()
                    root.after(200)

                    ImageGrab.grab().crop((x1, y1, x2, y2)).save(filename)

                    self.canvas.itemconfig(self.cursor_f, state='normal')
                    self.canvas.itemconfig(self.cursor_db, state='normal')
                    self.root.attributes('-topmost', False)
                    ###################################
                else:
                    print("Unknown file type")
        else:
            print("Cancel")

    def clear(self):
        self.canvas.delete("fline")

    def initialize_internal_dbarray(self):
        self.internal_dbarray=[self.dbinit]*self.internal_samples_quant
        self.dbarray_modified=True

    def draw_db_grid(self):
        self.canvas.delete("grid_db")

        for db,bold in ((10,0),(0,1),(-10,0),(-20,0),(-30,0),(-40,0),(-50,0),(-60,0),(-70,0),(-80,0),(-90,1)):
            y=self.db2y(db)

            self.canvas.create_text(6, y+4, text=str(db)+"dB", anchor="nw", font=("Arial", 8), tags="grid_db")
            if bold:
                self.canvas.create_line(0, y, self.canvas_winfo_width,y, fill="black" , tags="grid_db",width=1)
            else:
                self.canvas.create_line(0, y, self.canvas_winfo_width,y, fill="gray" , tags="grid_db",width=1,dash = (5, 2))

    def root_configure(self,event=None):
        self.root.update()

        self.canvas_winfo_width=self.canvas.winfo_width()
        self.scalex_factor=self.canvas_winfo_width/self.log10fmax_m_log10fmin
        self.scale_freq_factor=float(self.internal_samples_quant)/self.log10fmax_m_log10fmin

        self.canvas.delete("grid")

        self.canvas_winfo_height=self.canvas.winfo_height()

        for f,bold,lab in ((10,0,''),(20,1,'20Hz'),(30,0,''),(40,0,''),(50,0,''),(60,0,''),(70,0,''),(80,0,''),(90,0,''),(100,1,'100Hz'),
                    (200,0,''),(300,0,''),(400,0,''),(500,0,''),(600,0,''),(700,0,''),(800,0,''),(900,0,''),(1000,1,'1kHz'),
                    (2000,0,''),(3000,0,''),(4000,0,''),(5000,0,''),(6000,0,''),(7000,0,''),(8000,0,''),(9000,0,''),(10000,1,'10kHz'),
                    (20000,1,'20kHz'),(40000,1,'')):
            xf=log10(f)
            x=self.scalex(xf)

            if bold:
                self.canvas.create_line(x, 0, x, self.canvas_winfo_height, fill="black" , tags="grid",width=1)
                self.canvas.create_text(x+2, self.canvas_winfo_height-20, text=lab, anchor="nw", font=("Arial", 8), tags="grid")
            else:
                self.canvas.create_line(x, 0, x, self.canvas_winfo_height, fill="gray" , tags="grid",width=1,dash = (5, 2))

        self.scale_mod(self.current_log10freq)
        self.draw_db_grid()

    def db2y(self,db):
        return self.canvas_winfo_height - ( self.canvas_winfo_height*(db-self.dbmin_display)/self.dbrange_display )

    def update_plot(self):
        try:
            self.draw_spectrum()
        except Exception as e:
            print("update_plot_2:",e)

        self.root.after(10, self.update_plot)

    dbarray_modified=False

    def draw_spectrum(self):
        if self.dbarray_modified:
            spectrum_data=[]

            canvas_width=self.canvas_winfo_width
            internal_samples_quant=self.internal_samples_quant

            x_factor=canvas_width/internal_samples_quant
            self_db2y=self.db2y

            for x,db in enumerate(self.internal_dbarray):
                spectrum_data.extend([x_factor*x,self_db2y(db)])
            try:
                self.canvas.delete(self.spectrum_line)
            except:
                pass

            self.spectrum_line=self.canvas.create_line(spectrum_data, fill="darkred" , width=2, smooth=1)
            self.dbarray_modified=False

    def scalex(self,x):
        return self.scalex_factor * (x - self.log10fmin)

    def scale_freq(self,f):
        return round(self.scale_freq_factor * (f - self.log10fmin))

    def scale_mod(self,log10freq):
        self.current_log10freq = float(log10freq)
        x=self.current_log10freq_scalex=self.scalex(self.current_log10freq)

        self.current_freq = 10**self.current_log10freq
        self.phaseinc = self.two_pi_by_samplerate * self.current_freq

        y=self.canvas_winfo_height

        self.canvas.delete("freq")
        self.canvas.create_text(x+2, 2, text=str(round(self.current_freq))+"Hz", anchor="nw", font=("Arial", 8), tags="freq",fill="black")

        self.canvas.coords(self.cursor_f, x, 0, x, y)

    def audio_callback(self, outdata, frames, time, status):
        if status:
            print("status:",status)

        phase = self.phase

        self_phaseinc = self.phaseinc
        self_two_pi = self.two_pi

        #print(self.blocksize_play,len(outdata))
        #self.samples = zeros(self.blocksize_play,dtype="float64")
        #self_samples=self.samples
        self_samples=zeros(self.blocksize_play,dtype="float32")

        ##############################
        for i in range(self.blocksize_play):
            self_samples[i]=sin(phase)

            phase += self_phaseinc
            if phase >= self_two_pi:
                phase -= self_two_pi

        self.phase = phase

        outdata[:] = self_samples.tobytes()

    def sweep(self):
        self.stop()
        self.start()
        self.current_log10freq=self.log10fmin
        self.log10freq_var_set(self.log10fmin)
        self.scale_mod(self.log10fmin)

        #flog_quant=self.log10fmax_m_log10fmin/self.internal_samples_quant
        flog_quant=self.log10fmax_audio_m_log10fmin_audio/self.internal_samples_quant

        self.recording_var.set(True)
        self.recording_var_toggle()

        for x in range(self.internal_samples_quant):
            logf=self.log10fmin_audio+x*flog_quant

            self.current_log10freq=logf
            self.log10freq_var_set(logf)
            self.scale_mod(logf)
            self.root.update()
            self.root.after(100)

        self.stop()

        self.recording_var.set(False)
        self.recording_var_toggle()

    def start(self):
        if self.stream:
            return

        if not self.running:
            self.running = True

            self.stream = RawOutputStream(
                samplerate=self.samplerate,
                channels=1,
                dtype='float32',
                blocksize=self.blocksize_play,
                callback=self.audio_callback
            )
            self.stream.start()

    def stop(self):
        if self.running:
            self.running = False
            try:


                self.stream.stop()
                self.stream.close()
            finally:
                self.stream = None

    def on_close(self):

        if self.recording:
            self.stream_in.close()

        self.stop()

        self.root.withdraw()
        self.root.destroy()
        sys_exit(1)

    def mic_callback(self, indata, frames, time_info, status):
        if status:
            return

        try:
            block_mean=mean(square(indata[:, 0], dtype=float64))
            self.record_blocks.pop(0)
            self.record_blocks.append(block_mean)

            record_blocks_len=len(self.record_blocks)

            #print(self.record_blocks)

            #self.db = 20 * log10(sqrt(block_mean) + 1e-12)

            #self.db = 20 * log10(sqrt( mean(self.record_blocks) ) + 1e-12)
            self.db = 10 * log10( mean(self.record_blocks) + 1e-12)

            if self.recording:
                self.internal_dbarray[self.scale_freq(self.current_log10freq)]=self.db
                self.dbarray_modified=True

            #curr_db_min=np_min(self.internal_dbarray)
            #curr_db_max=np_max(self.internal_dbarray)

            #curr_db_mean=mean(self.internal_dbarray)

            #curr_db_range=curr_db_max-curr_db_min

            #curr_margin=max(curr_db_range,self.db_margin)

            #prev_dbmax_display = self.dbmax_display
            #prev_dbmax_display = self.dbmax_display

            #new_dbmax_display=round(min(self.dbmax, curr_db_mean+curr_margin) )
            #new_dbmin_display=round(max(self.dbmin, curr_db_mean-curr_margin) )

            #if prev_dbmax_display != new_dbmax_display or prev_dbmax_display != new_dbmax_display:
            #    self.dbmax_display=new_dbmax_display
            #    self.dbmin_display=new_dbmin_display

            #    self.dbrange_change()


            y=self.db2y(self.db)

            self.canvas.delete("db_text")
            self.canvas.create_text(self.canvas_winfo_width-20, y, text=str(round(self.db))+"dB", anchor="center", font=("Arial", 8), tags="db_text",fill="black")

            self.canvas.coords(self.cursor_db,0, y, self.canvas_winfo_width, y)

        except Exception as e:
            print("mic_callback:",e)

if __name__ == "__main__":
    root = Tk()
    app = SimpleAudioSweeper(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.after(200,app.update_plot)

    root.mainloop()
