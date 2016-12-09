# pybus

A service for finding buses around a stop in Singapore.

Setting up
----------

You will need an API key from [LTA DataMall](https://www.mytransport.sg/content/mytransport/home/dataMall.html). Create a file `data/hdrs.json` containing this key, like so:

    {
        "AccountKey": "your_key_here",
        "accept": "application/json"
    }

Then install requirements:

    $ cd pybus
    $ virtualenv .      # (if you want)
    $ pip install -r requirements.txt

To start
--------

    $ export FLASK_APP=pbapp.py
    $ flask run


