#Install pybb with pip

    pip install pybbm

#Install pybb with the git repo (with sudo if necessary)

    git clone https://github.com/beukueb/pybbm.git
    cd pybbm
    [sudo] python setup.py install --record pybbmfiles.txt

#To uninstall

    [sudo] pip uninstall pybbm
    cat pybbmfiles.txt | xargs [sudo] rm -rf