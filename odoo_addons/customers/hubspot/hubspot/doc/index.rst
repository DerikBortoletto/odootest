Module Dependency Installation  for Ubuntu
==========================================
First you needs to install **pyrecord** and **tzlocal** package using following command
::
    sudo pip3 install pyrecord==1.0.1
    sudo pip3 install tzlocal

You needs to install two more packages **hubspot-connection** and **hubspot-contacts** to install those packages we have provided one zip file
(*hubspot_api.zip*). You need to extract zip file. Inside extracted directory there are two packages **hubspot-connection-1.0rc8** and
**hubspot-contacts-1.0rc1**. You needs to go inside two directories and install two packages using following command.
::
    sudo python setup.py install


You can refer following screenshots

1. Zip file inside hubspot module

.. image:: https://apps.odoocdn.com/apps/assets/15.0/hubspot/img/setup_screen/1.png


2. After extract zip file

.. image:: https://apps.odoocdn.com/apps/assets/15.0/hubspot/img/setup_screen/2.png


3. Jump to `hubspot-connection-1.0rc8` directory and install package

.. image:: https://apps.odoocdn.com/apps/assets/15.0/hubspot/img/setup_screen/3.png

4. Jump to `hubspot-contacts-1.0rc1` directory and install package

.. image:: https://apps.odoocdn.com/apps/assets/15.0/hubspot/img/setup_screen/4.png

builtins

5. Make sure all packages are installed properly by using command
::
    pip freeze

.. image:: https://apps.odoocdn.com/apps/assets/15.0/hubspot/img/setup_screen/5.png
