#! /bin/bash
socat TCP4-LISTEN:1337,reuseaddr,fork EXEC:'python3 ./challenge.py'