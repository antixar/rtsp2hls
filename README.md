# CCTV solution
## Convert rtsp streams from IP cameras to HLS stream service
This solution has to use minimal hardware resources and can be start on RaspbarryPi boards etc
Flow of trasformation: *rtsp stream => flv => nginx + rtmp module => HLS*

# Functions
 - real time HLS stream (with delay equal a one chunk duration)
 - keep VOD record folders
 - clean old folders
 # INSTALL
 1. install last Docker version
 1. Copy Dockerfile.arm32v7 => Dockerfile for board with ARM arch or Dockerfile.ubuntu for x86-64 arch
 or use docker-compose templates
 1. Build image: docker build -t rtsp2rtmp
 1. Start docker with option:
```
 docker run -d -it --rm --name rtsp2rtmp_server \
        -p <needed_host_port>:80 \
        -e SAVE_MAX_TIME=<save_limit_time_in_seconds> \
        -e HLS_FRAGMENT=<duration_size_in_seconds> \
        -e RTSP_STREAM_<stream_name_1>="<rtsp_stream_url_1>" \
        -e RTSP_STREAM_<stream_name_2>="<rtsp_stream_url_2>" \
        .......
```

# HLS URL examples

## online streams:
 * stream_name_1: http://<your_server>/hls/stream_name_1/index.m3u8
 * stream_name_2: http://<your_server>/hls/stream_name_2/index.m3u8

## VOD streams:
 * stream_name_1: http://<your_server>//storage/stream_name_1/2017-12-12/2017-12-12_17-40/index.m3u8
 * stream_name_2: http://<your_server>//storage/stream_name_2/2017-12-12/2017-12-12_17-45/index.m3u8
Autoindex is active for  the location http://<your_server>//storage/... 