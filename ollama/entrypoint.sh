#!/bin/sh
set -e

echo "Starting Ollama server..."
ollama serve &

echo "Waiting for Ollama to be ready..."
until curl -s http://localhost:11434/api/tags > /dev/null; do
  sleep 1
done

echo "Pulling models..."
ollama pull gemma3:4b-it-qat
ollama pull gpt-oss:20b-cloud

echo "Ollama is ready."
wait
