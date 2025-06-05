#!/bin/bash

# Install git
apt update && apt install -y git

# Run your bot
python bot.py
