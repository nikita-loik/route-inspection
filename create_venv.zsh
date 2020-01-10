#!/bin/zsh
# A. Get virtual environment name.
# A.1. Get working directory name (without full path).
dir_name=${PWD##*/}
# A.2. Replace '-' with '_' in a name.
venv_stem="${dir_name//-/_}"
# A.3. Get virtual environment name.
venv_name="venv_${venv_stem}"
echo "===creating virtual environment ${venv_name}==="
# B. Create virtual environment.
virtualenv -p python3 ".${venv_name}"
# C. Activate virtual environment.
source ".${venv_name}/bin/activate"
# D. Install jupyter.
pip install jupyter
# E. Install IPython kernel.
python -m ipykernel install --user --name="${venv_name}"
# F. Install requirements.
pip install -r requirements.txt
echo "===virtual environment created==="
