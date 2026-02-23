# Raspberry Pi SD card backup

* Needs Linux package "rpi-clone" to be installed
* Assumes that a backup sd-card is available ad /dev/sda (e.g. via USB -> SD card adapter)
* Is able to run **incremental backups** (that's why I do not use dd any more)
