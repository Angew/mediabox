# Copyright 2023 Petr Kmoch
# This file is licensed under the MIT License; please see accompanying
# LICENSE file or https://opensource.org/license/mit/

import os.path
import shutil
import sys
import tkinter as tk
import tkinter.filedialog
from tkinter import ttk

import pyperclip as clip
import yt_dlp as yt



class SilentLogger():
    def debug(*args): pass
    def info(*args): pass
    def warning(*args): pass
    def error(*args): pass
    def critical(*args): pass



class Runtime():
    progress_download_unknown = 25
    progress_postprocess = 80
    progress_copy = 90
    
    def __init__(self):
        self._is_setup = False
        self.max = None

    def setup(self, max_exact, max_approx):
        if self._is_setup:
            return
        self._is_setup = True
        if max_exact is not None:
            self.max = max_exact
        elif max_approx is not None:
            self.max = max_approx

    def set_progress(self, progressor, value):
        if self.max is not None:
            progressor.set(min(100 * value / self.max, self.progress_postprocess))
        else:
            progressor.set(self.progress_download_unknown)



class MainWindow(tk.Tk):
    default_format_extensions = {
        "audio": "mp3",
        "video": "mp4"
    }

    def __init__(self, *args, **kwargs):
        self.ffmpeg_location = kwargs["ffmpeg_location"]
        del kwargs["ffmpeg_location"]
        super().__init__(*args, **kwargs)

        sticky_all = (tk.N, tk.S, tk.W, tk.E)
        pad = 5

        self.url = tk.StringVar()
        self.url.trace_add("write", self.config_changed)
        self.file = tk.StringVar()
        self.file.trace_add("write", self.config_changed)
        self.format = tk.StringVar()
        self.format.set("audio")
        self.format.trace_add("write", self.format_changed)
        self.state = tk.StringVar()
        self.progress = tk.DoubleVar()

        self.title("Media downloader")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        frm_main = ttk.Frame(self)
        frm_main.columnconfigure(0, weight=1)
        frm_main.rowconfigure(3, weight=1)
        frm_main.grid(column=0, row=0, sticky=sticky_all)

        frm_input = ttk.LabelFrame(frm_main, text="Input")
        frm_input.columnconfigure(1, weight=1)
        frm_input["padding"] = pad
        frm_input.grid(column=0, row=0, sticky="nwe", padx=pad, pady=pad)

        ttk.Label(frm_input, text="URL:", anchor=tk.E).grid(column=0, row=0, sticky=tk.E, padx=(pad, 0), pady=pad)
        self.ent_url = ttk.Entry(frm_input, textvariable=self.url, width=30)
        self.ent_url.grid(column=1, row=0, sticky=sticky_all, pady=pad)

        self.btn_paste = ttk.Button(frm_input, text="Paste", command=self.paste_url)
        self.btn_paste.grid(column=2, row=0, padx=pad, pady=pad)

        frm_output = ttk.LabelFrame(frm_main, text="Output")
        frm_output.columnconfigure(1, weight=1)
        frm_output["padding"] = pad
        frm_output.grid(column=0, row=1, sticky="nwe", padx=pad, pady=pad)

        ttk.Label(frm_output, text="File:", anchor=tk.E).grid(column=0, row=0, sticky=tk.E, padx=(pad, 0), pady=pad)
        self.ent_file = ttk.Entry(frm_output, textvariable=self.file, width=75)
        self.ent_file.grid(column=1, row=0, sticky=sticky_all, pady=pad)

        self.btn_browse = ttk.Button(frm_output, text="Browse", command=self.browse_file)
        self.btn_browse.grid(column=2, row=0, padx=pad, pady=pad)

        ttk.Label(frm_output, text="Format:", anchor=tk.E).grid(column=0, row=1, sticky=tk.E, padx=(pad, 0), pady=pad)
        frm_format = ttk.Frame(frm_output)
        frm_format.grid(column=1, row=1, sticky=tk.W)

        self.rb_video = ttk.Radiobutton(frm_format, text="Video", variable=self.format, value="video")
        self.rb_video.grid(column=0, row=0, pady=pad)
        self.rb_audio = ttk.Radiobutton(frm_format, text="Audio", variable=self.format, value="audio")
        self.rb_audio.grid(column=1, row=0, pady=pad)

        frm_run = ttk.Frame(frm_main)
        frm_run.columnconfigure(2, weight=1)
        frm_run.grid(column=0, row=2, sticky="nwe")

        self.btn_run = ttk.Button(frm_run, text="\N{BLACK MEDIUM RIGHT-POINTING TRIANGLE}", command=self.run)
        self.btn_run.grid(column=0, row=0, padx=pad, pady=pad, sticky=tk.W)

        self.lbl_state = ttk.Label(frm_run, textvariable=self.state)
        self.lbl_state.grid(column=1, row=0, padx=pad, pady=pad)

        self.prg_run = ttk.Progressbar(frm_run, orient=tk.HORIZONTAL, mode="determinate", variable=self.progress)
        self.prg_run.grid(column=2, row=0, sticky=(tk.W, tk.E), padx=pad, pady=pad)

        self.config_changed()

    def set_state_idle(self):
        self.state.set("")
        self.progress.set(0)

    def set_state_downloading(self):
        self.state.set("Downloading...")

    def set_state_postprocessing(self):
        self.progress.set(Runtime.progress_postprocess)
        self.state.set("Converting...")

    def set_state_copying(self):
        self.progress.set(Runtime.progress_copy)
        self.state.set("Copying...")

    def set_state_done(self):
        self.progress.set(100)
        self.state.set("Done!")

    def config_changed(self, *args):
        self.set_state_idle()
        if self.url.get() and self.file.get():
            self.btn_run.state(["!disabled"])
        else:
            self.btn_run.state(["disabled"])

    def format_changed(self, *args):
        file = self.file.get()
        if file:
            d, f = os.path.split(file)
            f = os.path.splitext(f)[0]
            e = self.default_format_extensions[self.format.get()]
            self.file.set(os.path.join(d, f"{f}.{e}"))

    def paste_url(self):
        pasted = clip.paste().strip()
        if pasted.startswith("http") and not "\n" in pasted:
            self.url.set(pasted)

    def browse_file(self):
        ext = self.default_format_extensions[self.format.get()]
        file = tk.filedialog.asksaveasfilename(defaultextension=ext, filetypes=[(f".{ext} Files", ext)])
        if not file:
            return
        self.file.set(file)

    def on_download_progress(self, prg):
        status = prg["status"]
        if status == "error":
            raise RuntimeError("Something went wrong")
        elif status == "finished":
            self.set_state_postprocessing()
        elif status == "downloading":
            self.runtime.setup(prg.get("total_bytes"), prg.get("total_bytes_estimate"))
            self.runtime.set_progress(self.progress, prg.get("downloaded_bytes"))
        self.update()

    def on_postprocessing_progress(self, prg):
        self.update()

    def run(self):
        ydl_opts = {
            "ffmpeg_location": self.ffmpeg_location,
            "format": self.default_format_extensions["video"],
            "keepvideo": True,
            "logging": SilentLogger(),
            "outtmpl": "%(id)s.%(ext)s",
            "postprocessor_hooks": [self.on_postprocessing_progress],
            "progress_hooks": [self.on_download_progress],
            "quiet": True,
        }
        if self.format.get() == "audio":
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": self.default_format_extensions[self.format.get()]
            }]
        self.runtime = Runtime()
        self.set_state_downloading()
        with yt.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.url.get())
        self.set_state_copying()
        downloaded = f"{info['id']}.{self.default_format_extensions[self.format.get()]}"
        shutil.copy2(downloaded, self.file.get())
        self.set_state_done()



def main(args):
    main_window = MainWindow(ffmpeg_location=args[1])
    main_window.mainloop()



if __name__ == "__main__":
    main(sys.argv)
