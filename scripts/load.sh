#!/bin/bash

DEST='/media/sam/CIRCUITPY'
LIB_DEST="$DEST/lib"

cp *.py $DEST
cp lib/* $LIB_DEST
cp "config/$1.json" "$DEST/config.json"
