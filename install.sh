#!/bin/bash
set -v
sudo apt-get update
sudo apt-get install fping
mkdir -p ~/.config/akita/proc.d
echo "akita was installed locally."
echo "Run with ./akita.py"
