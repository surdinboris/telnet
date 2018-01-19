
from tkinter import *
import time


def handle_click():
    print('Clicked!')


root = Tk()
Button(root, text='Click me', command=handle_click).pack()
root.mainloop()

def handle_click():
    win = Toplevel(root, title='Hi!')
    win.transient()
    Label(win, text='Please wait...').pack()
    i = 500
    def callback():
        nonlocal i, win
        print(i)
        i -= 1
        if not i:
            win.destroy()
        else:
            root.after(1000, callback)
    root.after(1000, callback)
