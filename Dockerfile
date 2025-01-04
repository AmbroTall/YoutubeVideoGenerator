# Use an Ubuntu base image
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

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
    libsox-dev \
    cmake \
    libasound-dev \
    portaudio19-dev \
    libportaudio2 \
    libportaudiocpp0 \
    && rm -rf /var/lib/apt/lists/*

# Install Git LFS
RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash && apt-get install -y git-lfs

# Install pyenv
RUN curl https://pyenv.run | bash
ENV PYENV_ROOT /root/.pyenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

# Install Python 3.12
RUN pyenv install 3.12
RUN pyenv global 3.12

# Create virtual environment
RUN pyenv virtualenv 3.12 env


# Copy requirements files
COPY requirements.txt ./

# Install dependencies (use compatible versions)
RUN /bin/bash -c "source ~/.pyenv/versions/env/bin/activate && pip install -r requirements.txt"


# Download all NLTK data to a central location (/usr/share/nltk_data)
RUN /bin/bash -c "source ~/.pyenv/versions/env/bin/activate && python -m nltk.downloader -d /usr/share/nltk_data all"

# Install additional Python packages
RUN /bin/bash -c "source ~/.pyenv/versions/env/bin/activate && pip install --upgrade pydantic && pip install --upgrade pydantic && pip install flask-cors ffmpeg-python pydub"

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

RUN /bin/bash -c "source ~/.pyenv/versions/env/bin/activate && pip install onnxruntime pyaudio"
# Copy the current directory contents into the container at /app
COPY . /app

# Set ownership of the app directory
RUN chown -R root:root /app

# Make port 80 available to the world outside this container
EXPOSE 80

# Expose port 5500 for the Flask app
EXPOSE 5500

# Expose port 8080 for the fish speech
EXPOSE 8080          

# Copy the start script into the container
COPY start.sh /app/start.sh

# Make the start script executable
RUN chmod +x /app/start.sh

# Run the start script
CMD ["/app/start.sh"]
