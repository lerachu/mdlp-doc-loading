#!/bin/bash
docker run -v /mnt/c/Users/йа/Desktop/загрузка/info:/app/info -v /mnt/c/Users/йа/Desktop/загрузка/XML:/app/XML  -e DISPLAY=:0 -v /tmp/.X11-unix:/tmp/.X11-unix --rm zagruzka
