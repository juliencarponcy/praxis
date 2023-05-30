========
praxis
========

Package to perform geopsatial data science / data engineering test for the position at Green Praxis

Install
-------

* Make sure you have conda installed
* download https://github.com/juliencarponcy/praxis 
* or, if you have git installed:
       
``git clone https://github.com/juliencarponcy/praxis`` 
    
* Navigate into the root folder
      
``cd praxis``
    
* Create environment called praxis (you can change the name of the environment by modifying the praxis.yaml file
    
``conda env create -f praxis.yaml``

Usage
-----

* Activate notebooks by command line using:

``conda activate praxis``

* Do this in the virtual environment to make modules in the repo available:

``pip install -e .``

* Launch Jupyter
``jupyter-notebook``