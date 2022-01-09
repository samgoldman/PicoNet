#!/bin/bash

if [ $2 == "local" ]; then
    DEST="./local"
    LIB_DEST="./local/lib"
else
    DEST="/media/sam/$2"
    LIB_DEST="$DEST/lib"
fi

cp *.py $DEST
cp lib/* $LIB_DEST
cp "config/$1.json" "$DEST/config.json"

if [ $2 == "local" ]; then
    cd 'local'
    python code.py
    cd ..
fi