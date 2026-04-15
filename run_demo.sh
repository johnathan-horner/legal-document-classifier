#!/bin/bash

# Legal Document Classification System - Streamlit Demo Launcher
# Launches the demo frontend with proper environment setup

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Legal Document Classification Demo${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install Streamlit requirements
echo -e "${YELLOW}Installing Streamlit dependencies...${NC}"
pip install -r streamlit_requirements.txt

# Set environment variables
export API_BASE_URL=${API_BASE_URL:-"http://localhost:8000"}

# Launch Streamlit app
echo -e "${GREEN}Launching Streamlit demo...${NC}"
echo -e "${YELLOW}Demo will open in your browser at http://localhost:8501${NC}"
echo -e "${YELLOW}Demo Mode is enabled by default - no backend required!${NC}"
echo

streamlit run app.py --server.port 8501 --server.address localhost