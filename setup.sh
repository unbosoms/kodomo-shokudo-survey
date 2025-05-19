#!/bin/bash
# Setup script for kodomo-shokudo-survey

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== こども食堂アンケート集計システム セットアップ ===${NC}"
echo

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
if command -v python3 &>/dev/null; then
    PYTHON_CMD=python3
elif command -v python &>/dev/null; then
    PYTHON_CMD=python
else
    echo -e "${RED}Python not found. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Python version: $PYTHON_VERSION"

# Check if Python version is at least 3.8
if [[ $(echo "$PYTHON_VERSION < 3.8" | bc) -eq 1 ]]; then
    echo -e "${RED}Python 3.8 or higher is required. Found version $PYTHON_VERSION${NC}"
    exit 1
fi

# Create virtual environment
echo
echo -e "${YELLOW}Creating virtual environment...${NC}"
if [ -d "venv" ]; then
    echo "Virtual environment already exists."
else
    $PYTHON_CMD -m venv venv
    echo "Virtual environment created."
fi

# Activate virtual environment
echo
echo -e "${YELLOW}Activating virtual environment...${NC}"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Unix/Linux/MacOS
    source venv/bin/activate
fi
echo "Virtual environment activated."

# Install dependencies
echo
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
echo "Dependencies installed."

# Create .env file from template if it doesn't exist
echo
echo -e "${YELLOW}Setting up environment variables...${NC}"
if [ -f ".env" ]; then
    echo ".env file already exists."
else
    cp .env.template .env
    echo ".env file created from template."
    echo -e "${YELLOW}Please edit the .env file to add your API keys and other settings.${NC}"
fi

# Create directories if they don't exist
echo
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p static/img
echo "Directories created."

# Final instructions
echo
echo -e "${GREEN}=== Setup Complete ===${NC}"
echo
echo -e "To run the application:"
echo -e "  1. Edit the ${YELLOW}.env${NC} file to add your API keys and settings"
echo -e "  2. Activate the virtual environment (if not already activated):"
echo -e "     ${YELLOW}source venv/bin/activate${NC} (Unix/Linux/MacOS)"
echo -e "     ${YELLOW}venv\\Scripts\\activate${NC} (Windows)"
echo -e "  3. Run the application:"
echo -e "     ${YELLOW}python app.py${NC}"
echo
echo -e "To run tests:"
echo -e "  ${YELLOW}python test_app.py${NC}"
echo
echo -e "To deploy to Vercel:"
echo -e "  1. Install Vercel CLI: ${YELLOW}npm install -g vercel${NC}"
echo -e "  2. Run: ${YELLOW}vercel${NC}"
echo
echo -e "${GREEN}Thank you for using こども食堂アンケート集計システム!${NC}"
