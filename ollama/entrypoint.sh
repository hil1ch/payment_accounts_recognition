#!/bin/sh
set -e

echo "Starting Ollama server..."
ollama serve &

echo "Waiting for Ollama to be ready..."
until curl -s http://localhost:11434/api/tags > /dev/null; do
  sleep 1
done

echo "Pulling models..."
ollama pull deepseek-ocr:3b-bf16
ollama pull gemma3:4b-it-qat

echo "Ollama is ready."
wait
