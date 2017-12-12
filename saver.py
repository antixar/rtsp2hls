#!/usr/bin/python

import sys
import time
import os
from datetime import datetime
import logging
from logging import handlers
from shutil import copyfile, rmtree
import threading


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
if len(sys.argv) <= 1:
    logger.warning("no set any stream data!!!")
    sys.exit(1)
HLS_DIRS = sys.argv[1:]
logger.info("start to check chunks for %s" % HLS_DIRS)

STORAGE_DIR = os.environ.get("SAVE_STORAGE", "/tmp")
HLS_TMP_FOLDER = os.environ.get("HLS_TMP_FOLDER", "/tmp")
HLS_FRAGMENT_TIME = int(os.environ.get("HLS_FRAGMENT", "60"))
SAVE_MAX_TIME = int(os.environ.get("SAVE_MAX_TIME", "600"))
chunk_dir = "chunks"
PERIOD_SECONDS = 300
DAY_SECONDS = 3600 * 24
# ==============================================================

def get_current_date(delta=0):
    return datetime.fromtimestamp(time.time() - delta).strftime('%Y-%m-%d')

def get_current_hour(delta=0):
    return datetime.fromtimestamp(int((time.time() - delta)/ PERIOD_SECONDS) * PERIOD_SECONDS).strftime('%Y-%m-%d_%H-%M')

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
    
    src_dir = os.path.join(HLS_TMP_FOLDER, name)
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
    curr_time = time.time() - 0.1

    for i in range(len(new_chunks) - 1):
        if new_chunks[i][1] < last_time:
            continue
        chunk = os.path.join(dst_chunk_dir, "%d.ts" % len(old_chunks))
        dur_chunks[chunk] = new_dur_chunks.get(new_chunks[i][0], float(HLS_FRAGMENT_TIME))
        os.utime(new_chunks[i][0], (curr_time, curr_time))
        old_chunks.append((chunk, time.time()))
        copyfile(new_chunks[i][0],chunk)
        # logger.warning("add file: %s" % chunk)
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
            if tt > last_time:
                continue
            logger.info("folder %s was removed" % c)
            rmtree(c)
        if not scan_folder(d):
            logger.info("root folder %s was removed" % d)

            rmtree(d)
    return

def _check_func():
    logger.info("init old chunk folders")
    while True:
        time.sleep(PERIOD_SECONDS * 1.5)
        for s in HLS_DIRS:
            clean_dir(s)
    return  

def main():
    t = threading.Thread(target=_check_func)
    t.start()

    while True:
        time.sleep(HLS_FRAGMENT_TIME * 1.5)
        for s in HLS_DIRS:
            save_chunk(s)



main()






