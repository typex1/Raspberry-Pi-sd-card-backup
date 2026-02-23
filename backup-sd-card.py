#!/bin/bash

# Note:
# /dev/sda2 type ext4 -> this is the OS data itself!
# /dev/sda1 type vfat -> this is be small BOOT volume!

# Exit if not running on Raspberry Pi
if [[ ! -f /proc/device-tree/model ]] || ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "This script only runs on Raspberry Pi. Exiting."
    exit 1
fi

# Ensure rpi-clone is installed
if ! command -v rpi-clone &> /dev/null; then
    echo "rpi-clone not found. Please install it first:"
    echo "git clone https://github.com/billw2/rpi-clone.git && cd rpi-clone && sudo cp rpi-clone /usr/local/sbin"
    exit 1
fi

LOG=../logs/95-backup-sd-card.log

echo "------------------------------" >> "${LOG}"
date >> "${LOG}"

echo "Starting rpi-clone to /dev/sda..." >> "${LOG}"

# -f (force) is only needed for initial copy, afterwards, an incremental one suffices:
#{ time (yes; echo) | sudo rpi-clone -f sda ; } >> "${LOG}" 2>&1
{ time (yes; echo) | sudo rpi-clone sda ; } >> "${LOG}" 2>&1

echo "Backup completed with exit code $?" >> "${LOG}"

sleep 2

echo "Verifying backup integrity..." >> "${LOG}"

sudo mkdir -p /mnt/backup_check

# Try to mount the root partition of the backup
if sudo mount /dev/sda2 /mnt/backup_check 2>/dev/null; then
    echo "SUCCESS: Backup partition /dev/sda2 is mountable." >> "${LOG}"

    # Check for a critical file
    if [ -f /mnt/backup_check/etc/hostname ]; then
        echo "SUCCESS: System files found on backup." >> "${LOG}"
    fi

    sudo umount /mnt/backup_check
else
    echo "ERROR: Backup partition could not be mounted!" >> "${LOG}"
fi

# Fix cmdline.txt PARTUUID to match the backup disk
echo "Fixing cmdline.txt PARTUUID..." >> "${LOG}"

sudo mkdir -p /mnt/backup_boot

if sudo mount /dev/sda1 /mnt/backup_boot 2>/dev/null; then
    # Get the actual PARTUUID of the backup disk's root partition
    BACKUP_PARTUUID=$(sudo blkid /dev/sda2 | grep -o 'PARTUUID="[^"]*"' | cut -d'"' -f2)

    if [ -n "$BACKUP_PARTUUID" ]; then
        # Update cmdline.txt with the correct PARTUUID
        sudo sed -i "s/root=PARTUUID=[^ ]*/root=PARTUUID=${BACKUP_PARTUUID}/" /mnt/backup_boot/cmdline.txt
        echo "SUCCESS: Updated cmdline.txt to use PARTUUID=${BACKUP_PARTUUID}" >> "${LOG}"
    else
        echo "ERROR: Could not determine backup disk PARTUUID" >> "${LOG}"
    fi

    sudo umount /mnt/backup_boot
else
    echo "ERROR: Could not mount boot partition to fix cmdline.txt" >> "${LOG}"
fi
