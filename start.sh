#!/bin/bash

CUDA_ENABLED=${CUDA_ENABLED:-true}
DEVICE=""

if [ "${CUDA_ENABLED}" != "true" ]; then
    DEVICE="--device cpu"
fi

# Activate the virtual environment
source ~/.pyenv/versions/env/bin/activate

# Start the Flask app in the background
python app/main.py &

# Start the fish speech app
cd app && python3 -m tools.api_server \
    --listen 0.0.0.0:8080 \
    --llama-checkpoint-path "checkpoints/fish-speech-1.5" \
    --decoder-checkpoint-path "checkpoints/fish-speech-1.5/firefly-gan-vq-fsq-8x1024-21hz-generator.pth" \
    --decoder-config-name firefly_gan_vq \
    ${DEVICE}
