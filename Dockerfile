# Use an Ubuntu base image
FROM --platform=linux/amd64 ubuntu:20.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    wget \
    llvm \
    libncurses5-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libffi-dev \
    liblzma-dev \
    && rm -rf /var/lib/apt/lists/*



# Install Git LFS
RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash && apt-get install -y git-lfs

# Install pyenv
RUN curl https://pyenv.run | bash
ENV PYENV_ROOT /root/.pyenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

# Install Python 3.11
RUN pyenv install 3.9
RUN pyenv global 3.9

# Create virtual environment
RUN pyenv virtualenv 3.9 env

# Upgrade pip to the latest version
RUN /bin/bash -c "source ~/.pyenv/versions/env/bin/activate && pip3 install --upgrade pip"

# Copy requirements files
COPY requirements.txt ./

# Install dependencies (use compatible versions)
RUN /bin/bash -c "source ~/.pyenv/versions/env/bin/activate && pip3 install -r requirements.txt"

# install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Copy the current directory contents into the container at /app
COPY . /app


# Make port 80 available to the world outside this container
EXPOSE 80

# Expose port 5000 for the Flask app
EXPOSE 5500

# Run the Flask app
CMD ["/bin/bash", "-c", "source ~/.pyenv/versions/env/bin/activate && python3 app/main.py"]
