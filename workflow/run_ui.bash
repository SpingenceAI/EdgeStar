#!/bin/bash

# Check if directory is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <directory>"
  exit 1
fi

# Navigate to the specified directory
cd "$1" || exit

# Run the Streamlit app
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
