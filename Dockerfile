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
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libfreetype6-dev \
    imagemagick \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Git LFS
RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash && apt-get install -y git-lfs

# Install pyenv
RUN curl https://pyenv.run | bash
ENV PYENV_ROOT /root/.pyenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

# Install Python 3.9
RUN pyenv install 3.9
RUN pyenv global 3.9

# Create virtual environment
RUN pyenv virtualenv 3.9 env

# Upgrade pip to the latest version
RUN /bin/bash -c "source ~/.pyenv/versions/env/bin/activate && pip install --upgrade pip"

# Copy requirements files
COPY requirements.txt ./

# Install dependencies (use compatible versions)
RUN /bin/bash -c "source ~/.pyenv/versions/env/bin/activate && pip install -r requirements.txt"

# Download all NLTK data to a central location (/usr/share/nltk_data)
RUN /bin/bash -c "source ~/.pyenv/versions/env/bin/activate && python -m nltk.downloader -d /usr/share/nltk_data all"

# Install additional Python packages
RUN /bin/bash -c "source ~/.pyenv/versions/env/bin/activate && pip install flask-cors && pip uninstall --yes python-ffmpeg && pip install ffmpeg-python"
RUN /bin/bash -c "source ~/.pyenv/versions/env/bin/activate && pip install --upgrade Pillow"

# Set ffmpeg location (optional if installed in a standard path)
ENV FFMPEG_PATH="/usr/bin/ffmpeg"
ENV NLTK_DATA="/usr/share/nltk_data"

# Configure ImageMagick policies
RUN echo '<policymap>' > /etc/ImageMagick-6/policy.xml && \
    echo '  <policy domain="coder" rights="read|write" pattern="PDF" />' >> /etc/ImageMagick-6/policy.xml && \
    echo '  <policy domain="coder" rights="read|write" pattern="EPS" />' >> /etc/ImageMagick-6/policy.xml && \
    echo '  <policy domain="coder" rights="read|write" pattern="SVG" />' >> /etc/ImageMagick-6/policy.xml && \
    echo '</policymap>' >> /etc/ImageMagick-6/policy.xml
ENV IMAGEMAGICK_BINARY="/usr/bin/convert"

# Copy the current directory contents into the container at /app
COPY . /app

# Make port 80 available to the world outside this container
EXPOSE 80

# Expose port 5500 for the Flask app
EXPOSE 5500

# Run the Flask app
CMD ["/bin/bash", "-c", "source ~/.pyenv/versions/env/bin
