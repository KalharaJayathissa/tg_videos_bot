# Use official Python runtime as a base image
FROM python:3.11-slim

# Set working directory in the container
WORKDIR /app



# Copy your requirements file (if you have one)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y git


# Copy the rest of your project files into the container
COPY . .

# Set environment variables (optional, e.g., bot token)
# ENV BOT_TOKEN=your_bot_token_here

# Run your bot script
CMD ["python", "bot.py"]
