# Use an Ubuntu base image
FROM nvidia/cuda:11.8.0-runtime-ubuntu20.04

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
    apt-transport-https \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Git LFS
RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash && apt-get install -y git-lfs

# Install pyenv
RUN curl https://pyenv.run | bash
ENV PYENV_ROOT /root/.pyenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

# Install Python 3.10
RUN pyenv install 3.10
RUN pyenv global 3.10

# Create virtual environment
RUN pyenv virtualenv 3.10 env

# Upgrade pip to the latest version
RUN /bin/bash -c "source ~/.pyenv/versions/env/bin/activate && pip install --upgrade pip && pip3 install --upgrade cython && pip3 install spacy==3.4.4"

# Copy requirements files
COPY requirements.txt ./

# Install dependencies (use compatible versions)
RUN /bin/bash -c "source ~/.pyenv/versions/env/bin/activate && pip install -r requirements.txt"

# Download all NLTK data to a central location (/usr/share/nltk_data)
RUN /bin/bash -c "source ~/.pyenv/versions/env/bin/activate && python -m nltk.downloader -d /usr/share/nltk_data all"

# Install additional Python packages
RUN /bin/bash -c "source ~/.pyenv/versions/env/bin/activate && pip install flask-cors ffmpeg-python Pillow pydub resemble-enhance pydantic && pip install --upgrade TTS"

# Install ImageMagick
RUN apt-get update && apt-get install -y --fix-missing imagemagick

# Set ffmpeg location (optional if installed in a standard path)
ENV FFMPEG_PATH="/usr/bin/ffmpeg"
ENV NLTK_DATA="/usr/share/nltk_data"

# After installing ImageMagick
RUN echo '<policymap>' > /etc/ImageMagick-6/policy.xml && \
    echo '  <policy domain="coder" rights="read|write" pattern="PDF" />' >> /etc/ImageMagick-6/policy.xml && \
    echo '  <policy domain="coder" rights="read|write" pattern="EPS" />' >> /etc/ImageMagick-6/policy.xml && \
    echo '  <policy domain="coder" rights="read|write" pattern="SVG" />' >> /etc/ImageMagick-6/policy.xml && \
    echo '</policymap>' >> /etc/ImageMagick-6/policy.xml
ENV IMAGEMAGICK_BINARY="/usr/bin/convert"

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Install image libraries
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libfreetype6-dev \
    zlib1g-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# Copy the current directory contents into the container at /app
COPY . /app

# Set ownership of the app directory
RUN chown -R root:root /app

# Make port 80 available to the world outside this container
EXPOSE 80

# Expose port 5500 for the Flask app
EXPOSE 5500

# Run the Flask app
CMD ["/bin/bash", "-c", "source ~/.pyenv/versions/env/bin/activate && python app/main.py"]

# Expose port 8080 for the fish speech
EXPOSE 8080          

# Run the fish speech app
CMD ["/bin/bash", "-c", "source ~/.pyenv/versions/env/bin/activate && cd app && python3 -m tools.api_server \
    --listen 0.0.0.0:8080 \
    --llama-checkpoint-path "checkpoints/fish-speech-1.5" \
    --decoder-checkpoint-path "checkpoints/fish-speech-1.5/firefly-gan-vq-fsq-8x1024-21hz-generator.pth" \
    --decoder-config-name firefly_gan_vq"]