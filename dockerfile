# Use official Python runtime as a base image
FROM python:3.11-slim

# Set working directory in the container
WORKDIR /app

# Install necessary system dependencies
RUN apt-get update && apt-get install -y \
    git \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Prepare SSH folder and add GitHub to known_hosts
RUN mkdir -p /root/.ssh
RUN ssh-keyscan github.com >> /root/.ssh/known_hosts

# Copy SSH keys (make sure ssh_keys folder exists next to Dockerfile)
COPY ssh_keys/id_ed25519 /root/.ssh/id_ed25519
COPY ssh_keys/id_ed25519.pub /root/.ssh/id_ed25519.pub

# Fix SSH key permissions
RUN chmod 600 /root/.ssh/id_ed25519
RUN chmod 644 /root/.ssh/id_ed25519.pub

# Configure Git user details
RUN git config --global user.name "kalhara_j"
RUN git config --global user.email "kalharajay@gmail.com"

# Copy your requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your project files into the container
COPY . .

# Run your bot script
CMD ["python", "bot.py"]