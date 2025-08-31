#!/usr/bin/python3

####################################################################################
#
#  Copyright (c) 2022-2025 Piotr Jochymek
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

from os import name as os_name
from tkinter import Frame,BooleanVar,Toplevel,Label

def set_geometry_by_parent(widget,parent):
    x_offset = int(parent.winfo_rootx()+0.5*(parent.winfo_width()-widget.winfo_width()))
    y_offset = int(parent.winfo_rooty()+0.5*(parent.winfo_height()-widget.winfo_height()))

    widget.geometry(f'+{x_offset}+{y_offset}')

locked_by_child={}

class GenericDialog:
    def __init__(self,parent,icon,bg_color,title,pre_show=None,post_close=None,min_width=400,min_height=300):
        self.bg_color=bg_color

        self.icon = icon
        self.widget = widget = Toplevel(parent,bg=self.bg_color,bd=0, relief='flat')
        widget.withdraw()
        widget.update()
        widget.protocol("WM_DELETE_WINDOW", lambda : self.hide())

        global locked_by_child
        locked_by_child[widget]=None

        self.set_mins(min_width,min_height)

        self.focus=None

        widget.iconphoto(False, *icon)

        widget.title(title)
        widget.bind('<Escape>', lambda event : self.hide() )
        widget.bind('<KeyPress-Return>', self.return_bind)
        widget.bind("<FocusIn>",lambda event : self.focusin() )

        self.parent=parent

        self.pre_show=pre_show
        self.post_close=post_close

        self.area_main = Frame(widget,bg=self.bg_color)
        self.area_main.pack(side='top',expand=1,fill='both')

        #only grid here
        self.area_main.grid_columnconfigure(0, weight=1)

        self.area_buttons_all = Frame(widget,bg=self.bg_color)
        self.area_buttons_all.pack(side='bottom',expand=0,fill='x')

        self.area_buttons = Frame(self.area_buttons_all,bg=self.bg_color)
        self.area_buttons.grid(row=0,column=3,sticky='we')

        self.area_mark = Frame(self.area_buttons_all,bg=self.bg_color)
        self.area_mark.grid(row=0,column=0,sticky='we')

        self.area_dummy = Frame(self.area_buttons_all,bg=self.bg_color)
        self.area_dummy.grid(row=0,column=5,sticky='we')

        self.area_buttons_all.grid_columnconfigure(2, weight=1)
        self.area_buttons_all.grid_columnconfigure(4, weight=1)

        self.wait_var=BooleanVar()
        self.wait_var.set(False)

        self.do_command_after_show=None
        self.command_on_close=None

        self.focus_restore=False

    def set_mins(self,min_width,min_height):
        self.widget.minsize(min_width, min_height)

    def return_bind(self,event):
        widget=event.widget
        try:
            widget.invoke()
        except:
            pass

    def unlock(self):
        self.wait_var.set(True)

    def focusin(self):
        global locked_by_child
        #print('\nlocked_by_child\n',[print(k,v) for k,v in locked_by_child.items()])
        if child_widget := locked_by_child[self.widget]:
            child_widget.focus_set()

    def show(self,wait=True,now=True):
        self.parent.config(cursor="watch")
        if now:
            self.parent.update()

        widget = self.widget

        if self.pre_show:
            self.pre_show(new_widget=widget)

        widget.wm_transient(self.parent)

        global locked_by_child
        locked_by_child[self.parent]=widget

        self.focus_restore=True
        self.pre_focus=self.parent.focus_get()

        if now:
            widget.update()

        set_geometry_by_parent(widget,self.parent)

        self.wait_var.set(False)
        self.res_bool=False

        widget.deiconify()

        if now:
            try:
                widget.update()
            except Exception as e:
                print(e)

        if self.focus:
            self.focus.focus_set()

        set_geometry_by_parent(widget,self.parent)

        if self.do_command_after_show:
            commnad_res = self.do_command_after_show()

            if commnad_res:
                self.hide()
                return

        #windows re-show workaround
        try:
            widget.iconphoto(False, *self.icon)
        except Exception as e:
            print(e)

        if wait:
            widget.wait_variable(self.wait_var)

    def show_postprocess(self):
        self.parent.update()
        self.widget.update()
        set_geometry_by_parent(self.widget,self.parent)

    def hide(self,force_hide=False):
        widget = self.widget

        global locked_by_child
        if locked_by_child[widget]:
            return

        if not force_hide and self.command_on_close:
            self.command_on_close()
        else:
            widget.withdraw()

            try:
                widget.update()
            except Exception as e:
                pass

            locked_by_child[self.parent]=None

            if self.focus_restore:
                if self.pre_focus:
                    self.pre_focus.focus_set()
                else:
                    self.parent.focus_set()

            self.wait_var.set(True)
            self.parent.config(cursor="")

            if self.post_close:
                self.post_close()
