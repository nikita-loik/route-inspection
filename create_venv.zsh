#!/bin/zsh
echo "===CREATING VIRTUAL ENVIRONMENT==="
virtualenv -p python3 venv_route_inspection
source venv_route_inspection/bin/activate
pip install jupyter
python -m ipykernel install --user
pip install -r requirements.txt
echo "===VIRTUAL ENVIRONMENT CREATED==="