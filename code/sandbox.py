import sys

import yt_dlp as yt


if __name__ != "__main__":
    raise NotImplementedError("Module not intended for importing")


def progress_hook(d):
    print("!!")
    if d["status"] == "downloading":
        print(f"{d['downloaded_bytes']}/{d['total_bytes']}")

def postprocessor_hook(d):
    print(d["status"], d["postprocessor"])


class MyLogger:
    def debug(self, msg):
        # For compatibility with youtube-dl, both debug and info are passed into debug
        # You can distinguish them by the prefix '[debug] '
        if msg.startswith('[debug] '):
            pass
        else:
            self.info(msg)

    def info(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass


postprocessor = {
    "key": "FFmpegExtractAudio",
    "preferredcodec": "mp3",
}

ydl_opts = {
    "keepvideo": True,
    "format": "mp4",
    "postprocessors": [postprocessor],
    "ffmpeg_location": "d:/AdditionalPrograms/FFmpeg/ffmpeg-3.4.1-win64-static/bin",
    "outtmpl": {
        "default": "%(id)s.%(ext)s"
    },
    "quiet": True,

    "postprocessor_hooks": [postprocessor_hook],
    "progress_hooks": [progress_hook],
    "logger": MyLogger(),
}

with yt.YoutubeDL(ydl_opts) as ydl:
    i = ydl.extract_info("https://www.youtube.com/watch?v=sOlnTG8kRho")

    # print(i["id"])
    # print(i["video_ext"])
    # print(i["audio_ext"])
