

## Starting the Grinder

    $ cd Solana-Wallet-Grinder
    $ python3 -m venv venv
    $ source ./venv/bin/activate
    $ pip3 install -r requirements.txt
    $ python3 main.py

## Performance Stats

     Performance is exponential, over time it gets much faster on high clock speed machines
     |
     On AMD Ryzen 9 7950X3D:
        After 20 hours: Speed (Last 10 sec interval): 22,274,018,994.77 addresses/sec
     On AMD EPYC 7313P: 
        After a few hours: Speed (Last 10 sec interval): 6,221,655,628.46 addresses/sec
