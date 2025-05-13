#!/bin/bash
rclone mount google: ~/GoogleDrive \
  --vfs-cache-mode writes \
  --daemon
