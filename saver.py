#!/usr/bin/python

import sys
import time
import os
from datetime import datetime
import logging
from logging import handlers
from shutil import copyfile, rmtree
import threading
import subprocess
from dateutil.tz import tzlocal
from pytz import timezone
import calendar


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
form = logging.Formatter("%(levelname)s - %(message)s")
form2 = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(form2)
logger.addHandler(ch)
fh = handlers.RotatingFileHandler(os.environ.get("LOG_FILENAME", "/tmp/log.log"), 
maxBytes=(1048576*5), backupCount=7)
fh.setFormatter(form2)
logger.addHandler(fh)

# =============================================================
STORAGE_DIR = os.environ.get("SAVE_STORAGE", "/tmp")
TMP_FOLDER = os.path.join(os.environ.get("TMP_FOLDER", "/tmp") , "hls")
HLS_FRAGMENT_TIME = int(os.environ.get("HLS_FRAGMENT", "60"))
SAVE_MAX_TIME = int(os.environ.get("SAVE_MAX_TIME", "600"))
NAME_LOCALHOST = os.environ.get("NAME_LOCALHOST", "http://127.0.0.1")
MODE_DEBUG = os.environ.get("MODE_DEBUG", "False")
SCREEN_MIN_DELAY = int(os.environ.get("SCREEN_MIN_DELAY", "5"))
MIN_SCREEN_START_TIME = int(os.environ.get("MIN_SCREEN_START_TIM", "0"))
CURRENT_TIMEZONE = os.environ.get("CURRENT_TIMEZONE", "Europe/London")
chunk_dir = "chunks"
screen_dir = "screens"
PERIOD_SECONDS = 300
DAY_SECONDS = 3600 * 24
DEFAULT_SENS = 0.08
# ==============================================================

if len(sys.argv) <= 1:
    logger.warning("no set any stream data!!!")
    sys.exit(1)
HLS_DIRS = sys.argv[1:]
logger.info("start to check chunks for %s" % HLS_DIRS)

SENS_SCREENS = {}
for k, v in os.environ.items():
    if not k.startswith("RTSP_SENS_"):
        continue
    SENS_SCREENS[k.replace("RTSP_SENS_", "")] = float(v)

SENS_SCREENS = {n:SENS_SCREENS.get(n, DEFAULT_SENS) for n in HLS_DIRS}
# ================================================================

def timezone2shift(tz=CURRENT_TIMEZONE):
    if not tz:
        return None
    try:
        t = datetime.now(timezone(tz)).timetuple()
        t = calendar.timegm(t)
        t -= int(time.time())
    except Exception as e:
        print("bad format time zone: %s" % str(e))
        return None
    return t

def get_current_time():
    return time.time() + timezone2shift()



def get_current_date(delta=0):
    return datetime.fromtimestamp(get_current_time() - delta).strftime('%Y-%m-%d')

def get_current_hour(delta=0):
    return datetime.fromtimestamp(int((get_current_time() - delta)/ PERIOD_SECONDS) * PERIOD_SECONDS).strftime('%Y-%m-%d_%H-%M')

def scan_folder(dirname):
    res = []
    if not os.path.exists(dirname):
        return []
    for filename in os.listdir(dirname):
        chunk = os.path.join(dirname, filename)
        if chunk.endswith("m3u8"):
            continue
        access_time = os.path.getmtime(chunk)
        res.append((chunk, access_time))
    return sorted(res, key=lambda item: item[1])  


def parse_m3u8(dir_name, index_file):
    if not os.path.exists(index_file):
        return {}
    res = {}
    last_duration = 0
    with open(index_file, "r") as f:
        for line in f:
            if not last_duration and line.startswith("#EXTINF:"):
                last_duration = float(line[len("#EXTINF:"):].split(",")[0].strip())
            elif last_duration:
                res[os.path.join(dir_name, line[:-1])] = last_duration
                last_duration = 0
    return res
    

def save_chunk(name):
    
    src_dir = os.path.join(TMP_FOLDER, name)
    if not os.path.exists(src_dir):
        logger.warning("no found HLS folder: %s" % src_dir)
        return False

    dst_dir = os.path.join(STORAGE_DIR, name, get_current_date(), get_current_hour())
    dst_chunk_dir = os.path.join(dst_dir, chunk_dir)
    if not os.path.exists(dst_dir):
        logger.info("create the new dst folder: %s" % dst_dir)
        os.makedirs(dst_dir)
    if not os.path.exists(dst_chunk_dir):
        os.makedirs(dst_chunk_dir)

    src_index_file = os.path.join(src_dir, "index.m3u8")
    if not os.path.exists(src_index_file):
        logger.warning("no found HLS index file: %s" % src_index_file)
        return False

    new_chunks = scan_folder(src_dir)
    if len(new_chunks) < 2:
        return False

    
    old_chunks = scan_folder(dst_chunk_dir)
    last_time = 0
    if old_chunks:
        last_time = old_chunks[-1][1]
    else:
        prev_dst_dir =  os.path.join(
            STORAGE_DIR, name,
            get_current_date(PERIOD_SECONDS),
            get_current_hour(PERIOD_SECONDS))
        prev_old_chunks = scan_folder(prev_dst_dir)
        if prev_old_chunks:
            last_time = prev_old_chunks[-1][1]

    dst_index_file = os.path.join(dst_dir, "index.m3u8")

    dur_chunks = parse_m3u8(dst_dir, dst_index_file)
    new_dur_chunks = parse_m3u8(src_dir, src_index_file)

    for i in range(len(new_chunks) - 1):
        if new_chunks[i][1] < last_time:
            continue
        chunk = os.path.join(dst_chunk_dir, "%d.ts" % len(old_chunks))
        dur_chunks[chunk] = new_dur_chunks.get(new_chunks[i][0], float(HLS_FRAGMENT_TIME))
        os.utime(new_chunks[i][0], (1330712280, 1330712292))
        old_chunks.append((chunk, time.time()))
        copyfile(new_chunks[i][0],chunk)
        logger.debug("add file: %s => %s" % (new_chunks[i][0], chunk))
    if not dur_chunks:
        return False

    os.utime(new_chunks[-1][0], (time.time(), time.time()))

    with open(dst_index_file, "w") as f:
        f.write("#EXTM3U\n")
        f.write("#EXT-X-VERSION:3\n")
        
        f.write("#EXT-X-TARGETDURATION:%d\n" % int(sorted(dur_chunks.values())[-1]))
        f.write("#EXT-X-MEDIA-SEQUENCE:0\n")
        f.write("#EXT-X-PLAYLIST-TYPE:VOD\n")
        for chunk, _ in old_chunks:
            f.write("#EXTINF:%.3f,\n" % dur_chunks.get(chunk, float(HLS_FRAGMENT_TIME)))
            f.write(chunk_dir + "/" + os.path.basename(chunk) + "\n")
        f.write("#EXT-X-ENDLIST\n")
    
    return True

def clean_dir(name):
    shift = SAVE_MAX_TIME
    if shift < (PERIOD_SECONDS * 2):
        shift = PERIOD_SECONDS * 2
    root_dir = os.path.join(STORAGE_DIR, name)
    last_time = time.time() - shift


    for d, t in scan_folder(root_dir) or []:
        if t > last_time + (3600 * 24):
            continue
        logger.info("check day dir: %s" % d)
        for c, tt in scan_folder(d):
            if tt > last_time or c.endswith(screen_dir):
                continue
            logger.info("folder %s was removed" % c)
            rmtree(c)
        if len(scan_folder(d)) <= 1:
            logger.info("root folder %s was removed" % d)
            rmtree(d)

    return

def check_screen(name):
    logger.info("check screens: %s" % name)
    root_dir = os.path.join(STORAGE_DIR, name)
    curr_dir = os.path.join(STORAGE_DIR, name, get_current_date(), get_current_hour())
    for d, _ in scan_folder(root_dir) or []:
        sdir = os.path.join(d, screen_dir)
        if not os.path.exists(sdir):
            os.makedirs(sdir)
        loaded_files = [sdir]
        for s, _ in scan_folder(sdir) or []:
            b = "_".join(os.path.basename(s).split("_")[:-1])
            b = os.path.join(d, b)
            if b not in loaded_files:
                loaded_files.append(b)


        for c, create_time_dir in scan_folder(d):
            if c in loaded_files:
                # logger.warning("ignore upload folder: %s" % c)
                continue
            elif c == curr_dir:
                # logger.warning("ignore current folder: %s" % c)
                continue
            elif create_time_dir < MIN_SCREEN_START_TIME:
                # logger.warning("FFFFFFFFFFF")
                continue
            dst_dir = os.path.join(os.path.dirname(TMP_FOLDER), screen_dir, name)
            if os.path.exists(dst_dir):
                rmtree(dst_dir)
            os.makedirs(dst_dir)

            url = "%s/storage/%s/%s/index.m3u8" % (NAME_LOCALHOST, name, "/".join(c.split("/")[-2:]))
            # """timeout  -s 9 -t 60 ffmpeg  -loglevel warning -i '%s' -vf "select=gt(scene\,0.08)"  -s 480x300 -r 1/6 -f image2 %s/%%03d.png""" % (url, dst_dir),
            logger.info("SCREEN: try to found screens for %s, created time: %s" % (c, create_time_dir))
            # cmd = """timeout  -s 9 -t 90 ffmpeg  -loglevel warning -i '{url}' -an -vf fps=1/{min_delay}  -s 480x300 -f image2 {dpath}/temp_%03d.png""".format(min_delay=SCREEN_MIN_DELAY, url=url, dpath=dst_dir)
            cmd = """timeout  -s 9 -t 70 ffmpeg  -loglevel warning -i '{url}' -an   -q:v 2 -vf select="eq(pict_type\,PICT_TYPE_I)" -vsync 0 -f image2 {dpath}/temp_%03d.png""".format(url=url, dpath=dst_dir)
            
            # 
            return_code = subprocess.call(cmd, shell=True)
            screen_files = scan_folder(dst_dir) or []

            if return_code and not screen_files:
                logger.warning("SCREEN: cmd error %s => %s" %(cmd, return_code))
                # continue
            else:
                logger.info("SCREEN: found %s i-frames" % len(screen_files))
                cmd = """timeout  -s 9 -t 90 ffmpeg  -loglevel warning -i '{dpath}/temp_%03d.png' -an -vf "select=gt(scene\,{sens})" -f image2 {dpath}/%03d.png""".format(url=url,sens=SENS_SCREENS[name], dpath=dst_dir)
                logger.warning(cmd)
                return_code = subprocess.call(cmd, shell=True)
            
            for s in sorted([sc for sc, _ in screen_files]):
                os.remove(s)
            if return_code:
                logger.warning("SCREEN cmd error: %s => %s" % (cmd, return_code))
            screen_files = scan_folder(dst_dir) or []

            if not screen_files:
                ff = os.path.join(dst_dir, "empty.txt")
                with open(ff, "w") as f:
                    f.write("empty\n")
                logger.info("SCREEN: gen gup for %s" % c)
                screen_files.append(ff)
            else:
                screen_files = sorted([sc for sc, _ in screen_files])

            if len(screen_files) > 20:

                cmd ="""ffmpeg -loglevel warning  -pattern_type glob -i %s/*.png -filter_complex tile=5x4  -f image2 %s/output.png""" % ( dst_dir, dst_dir)
                subprocess.call(cmd, shell=True)
                screen_files = ["%s/output.png" % dst_dir]   
            for i in range(len(screen_files)):
                ext = screen_files[i].split(".")[-1]
                dst_screen_file = os.path.join(os.path.basename(c) + "_%d.%s" % (i + 1, ext))
                dst_screen_file = os.path.join(sdir, dst_screen_file)
                copyfile(screen_files[i], dst_screen_file)
            logger.debug("SCREEN: save screen %s files for %s" % (len(screen_files), c))

    return

def _check_func():
    logger.info("init old chunk folders")
    while True:
        time.sleep(PERIOD_SECONDS * 1.5)
        for s in HLS_DIRS:
            try:
                clean_dir(s)
            except Exception as e:
                logger.error(str(e))
                if MODE_DEBUG == "True":
                    raise
    return

def _check_screen():
    logger.info("init old chunk folders")
    while True:
        
        for s in HLS_DIRS:
            try:
                check_screen(s)
            except Exception as e:
                logger.error(str(e))
                if MODE_DEBUG == "True":
                    raise
        time.sleep(HLS_FRAGMENT_TIME * 10)
    return  

def main():
    t1 = threading.Thread(target=_check_func)
    t1.start()

    t2 = threading.Thread(target=_check_screen)
    t2.start()

    
    while True:
        time.sleep(HLS_FRAGMENT_TIME * 1.5)
        for s in HLS_DIRS:
            try:
                save_chunk(s)
            except Exception as e:
                logger.error(str(e))
                if MODE_DEBUG == "True":
                    raise



main()







