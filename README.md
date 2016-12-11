# pybus

A service for finding buses around a stop in Singapore.

Setting up
----------

Install requirements:

    $ cd pybus
    $ virtualenv .      # (if you want)
    $ pip install -r requirements.txt

Next, you will need an API key from [LTA DataMall](https://www.mytransport.sg/content/mytransport/home/dataMall.html). Create an environment variable named `PYBUS_ACCOUNTKEY` containing this key, like so:

    $ export PYBUS_ACCOUNTKEY=<your_key_here>

Or, roll your own startup script. Idea for a name: `runapp` is included in the root `.gitignore`.

To start
--------

    $ export FLASK_APP=pbapp.py
    $ flask run


