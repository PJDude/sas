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

from tkinter import DoubleVar, BooleanVar,Canvas

from tkinter.ttk import Frame,Label,Scale,Button,Checkbutton
import sounddevice as sd
from math import pi, sin, log10, sqrt
from array import array
from numpy import mean,square,float64, min as np_min, max as np_max

from sys import exit as sys_exit

import tkinter as tk

class SimpleAudioSweeper:
    fmin,fini,fmax=10,442,25000

    log10fmin,log10fini,log10fmax=log10(fmin),log10(fini),log10(fmax)
    two_pi = 2.0 * pi
    internal_samples_quant=200

    log10fmax_m_log10fmin = log10fmax-log10fmin

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
    blocksize_record = 512

    def __init__(self, root):
        self.root = root
        self.root.title("Small Audio Sweeper v1.0001")
        #for initialization only
        self.scalex_factor=0

        self.db=-24
        y=self.db2y(self.db)

        root.rowconfigure(1, weight=1)
        root.columnconfigure(0, weight=1)

        self.log10freq_var = DoubleVar(value=self.log10fini)
        self.recording_var = BooleanVar(value=False)

        self.log10freq_var_get=self.log10freq_var.get
        self.log10freq_var_set=self.log10freq_var.set

        self.slider = Scale(root, from_=self.log10fmin, to=self.log10fmax, variable=self.log10freq_var, command=self.scale_mod)
        self.slider.grid(row=0, column=0, sticky="news", padx=10,pady=3)

        self.canvas = Canvas(root,height=300, width=800,relief='sunken',borderwidth=1,bg='lightgray')
        self.canvas.grid(row=1, column=0, sticky="news", padx=20,pady=3)

        self.cursor_f = self.canvas.create_line(self.log10fini, 0, self.log10fini, y, width=2, fill="white")
        self.cursor_db = self.canvas.create_line(0, y, self.log10fmax, y, width=10, fill="white")

        self.dbrange_change()

        btns = Frame(root)
        btns.grid(row=4, column=0, pady=10,sticky="ewns")
        Button(btns, text="▶▶▶", command=self.sweep,width=4).grid(row=0, column=1, padx=5)
        Button(btns, text="▶", command=self.start,width=2).grid(row=0, column=2, padx=5)
        Button(btns, text="▪",  command=self.stop,width=2).grid(row=0, column=3, padx=5)
        Button(btns, text="✕",  command=self.clear,width=2).grid(row=0, column=4, padx=5)
        Button(btns, text="S",  command=self.save,width=2).grid(row=0, column=5, padx=5)
        Checkbutton(btns, text="Rec",  variable=self.recording_var,width=3,command=self.recording_var_toggle).grid(row=0, column=6, padx=5)

        self.recording_var_toggle()

        btns.columnconfigure(0,weight=1)

        self.samplerate = 44100
        self.stream = None
        self.phase = 0.0

        self.two_pi_by_samplerate = self.two_pi/self.samplerate

        self.running = False

        self.current_log10freq=self.log10fini
        self.current_log10freq_scalex=self.scalex(self.current_log10freq)

        self.current_freq = self.fini

        self.slider.set(self.log10fini)

        self.samples = array('f',[0] * self.blocksize_play)

        self.stream_in = sd.InputStream(
            samplerate=self.samplerate, channels=1, dtype="float32",
            blocksize=self.blocksize_record, callback=self.mic_callback
        )
        self.initialize_internal_dbarray()

        self.stream_in.start()

        self.root.bind('<Configure>', self.root_configure)

    def recording_var_toggle(self):
        self.recording=self.recording_var.get()
        #print(f'{self.recording=}')

    def save(self):
        print("savefile")

    def clear(self):
        self.canvas.delete("fline")

    def initialize_internal_dbarray(self):
        self.internal_dbarray=[self.dbinit]*self.internal_samples_quant

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

        for f,bold in ((10,0),(20,1),(30,0),(40,0),(50,0),(60,0),(70,0),(80,0),(90,0),(100,1),
                    (200,0),(300,0),(400,0),(500,0),(600,0),(700,0),(800,0),(900,0),(1000,1),
                    (2000,0),(3000,0),(4000,0),(5000,0),(6000,0),(7000,0),(8000,0),(9000,0),(10000,1),
                    (20000,1)):
            xf=log10(f)
            x=self.scalex(xf)

            if bold:
                self.canvas.create_line(x, 0, x, self.canvas_winfo_height, fill="black" , tags="grid",width=1)
                self.canvas.create_text(x+2, self.canvas_winfo_height-20, text=str(f)+"Hz", anchor="nw", font=("Arial", 8), tags="grid")
            else:
                self.canvas.create_line(x, 0, x, self.canvas_winfo_height, fill="gray" , tags="grid",width=1,dash = (5, 2))

        self.scale_mod(self.current_log10freq)
        self.draw_db_grid()

    def db2y(self,db):
        return self.canvas_winfo_height-( self.canvas_winfo_height*(db-self.dbmin_display)/self.dbrange_display )

    def update_plot(self):
        try:
            self.draw_spectrum()
        except Exception as e:
            print("update_plot_2:",e)

        self.root.after(10, self.update_plot)

    def draw_spectrum(self):
        spectrum_line=[]

        canvas_width=self.canvas_winfo_width
        internal_samples_quant=self.internal_samples_quant

        for x,db in enumerate(self.internal_dbarray):
            x_canv=float(x/internal_samples_quant)*canvas_width
            spectrum_line.extend([x_canv,self.db2y(db)])

        self.canvas.delete("spectrum")
        self.spectrum_line=self.canvas.create_line(spectrum_line, fill="darkred" , tags="spectrum",width=2,smooth=1)

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

        self_samples=self.samples

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

        flog_quant=self.log10fmax_m_log10fmin/self.internal_samples_quant

        self.recording_var.set(True)
        self.recording_var_toggle()

        for x in range(self.internal_samples_quant):
            logf=self.log10fmin+x*flog_quant

            self.current_log10freq=logf
            self.log10freq_var_set(logf)
            self.scale_mod(logf)
            self.root.update()
            self.root.after(30)

        self.stop()

        self.recording_var.set(False)
        self.recording_var_toggle()

    def start(self):
        if self.stream:
            return

        if not self.running:
            self.running = True

            self.stream = sd.RawOutputStream(
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
            self.db = 20 * log10(sqrt(mean(square(indata[:, 0], dtype=float64))) + 1e-12)

            if self.recording:
                self.internal_dbarray[self.scale_freq(self.current_log10freq)]=self.db

            curr_db_min=np_min(self.internal_dbarray)
            curr_db_max=np_max(self.internal_dbarray)

            curr_db_mean=mean(self.internal_dbarray)

            curr_db_range=curr_db_max-curr_db_min

            curr_margin=max(curr_db_range,self.db_margin)

            prev_dbmax_display = self.dbmax_display
            prev_dbmax_display = self.dbmax_display

            new_dbmax_display=round(min(self.dbmax, curr_db_mean+curr_margin) )
            new_dbmin_display=round(max(self.dbmin, curr_db_mean-curr_margin) )

            if prev_dbmax_display != new_dbmax_display or prev_dbmax_display != new_dbmax_display:
                self.dbmax_display=new_dbmax_display
                self.dbmin_display=new_dbmin_display

                self.dbrange_change()

            self.canvas.delete("db_text")

            y=self.db2y(self.db)

            self.canvas.create_text(self.canvas_winfo_width-20, y, text=str(round(self.db))+"dB", anchor="center", font=("Arial", 8), tags="db_text",fill="black")

            self.canvas.coords(self.cursor_db,0, y, self.canvas_winfo_width, y)

        except Exception as e:
            print("mic_callback:",e)

if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleAudioSweeper(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.after(200,app.update_plot)

    root.mainloop()
