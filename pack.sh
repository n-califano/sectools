# pack everything into a single executable .pyz
# to keep the code modular in multiple files during development but
# copy only a single file on the target machine 
python -m zipapp ./ -m "privesc:main" -o privesc.pyz