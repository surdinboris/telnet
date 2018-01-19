
import tkinter as tk
from tkinter import ttk,messagebox

class Window():

    def __init__(self, root):

        self.frame = tk.Frame(root)
        self.frame.grid()

        self.i = 0
        self.labelVar = tk.StringVar()
        self.labelVar.set("This is the first text: %d" %self.i)

        self.label = tk.Label(self.frame, text = self.labelVar.get(), textvariable = self.labelVar)
        self.label.grid(column = 0, row = 0)

        self.button = tk.Button(self.frame, text = "Update", command = lambda :self.updateLabel())
        self.button.grid(column = 1, row = 0)

        self.enableButton = tk.Button(self.frame, text = "Enable Update Button", state = 'disabled', command = lambda :self.enable())
        self.enableButton.grid(column = 2, row = 0)

    def updateLabel(self):

        self.i += 1
        self.labelVar.set("This is the new text: %d" %self.i)
        self.button.config(state = 'disabled')
        self.enableButton.config(state = 'active')

    def enable(self):

        self.button.config(state = 'active')
        self.enableButton.config(state = 'disabled')

root = tk.Tk()
window = Window(root)
root.mainloop()