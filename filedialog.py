import os.path as pa
import tkinter as tk
from tkinter import filedialog

def get_openfile(fname, filetypes=''):
    '''開く既存ファイル名を取得 filetypes省略時はPNG'''
    root = tk.Tk()
    root.withdraw()

    if filetypes == '':
        filetypes = [("PNG files", "*.png"),]
        
    filename = filedialog.askopenfilename(
        title='Open File',
        initialdir='.',
        initialfile=fname,
        filetypes=filetypes
    )
    
    root.destroy()

    if not pa.exists(filename):
        return ''
    else:
        return filename


def get_savefile(fname, filetypes=''):
    '''保存ファイル名を取得 filetypes省略時はPNG'''
    root = tk.Tk()
    root.withdraw()

    if filetypes == '':
        filetypes = [("PNG files", "*.png"),]
        
    filename = filedialog.asksaveasfilename(
        title='Save File',
        initialdir='.',
        initialfile=fname,
        filetypes=filetypes
    )
    root.destroy()
    return filename


