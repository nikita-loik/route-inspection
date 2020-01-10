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
echo "===virtual environment .${venv_name} created==="
# G. If doesn't exist, add virtual environment path to .gitignore.
grep -qxF ".${venv_name}/" .gitignore || echo ".${venv_name}/" >> .gitignore
echo "===updated .gitignore with ".${venv_name}/"==="
# H. Add and commit .gitignore to git.
# NB Will report 'no changes added to commit' if .gitignore stayed the same.
git add .gitignore
git commit -m "Update .gitignore with '.${venv_name}/'"
echo "===added & committed .gitignore to git==="