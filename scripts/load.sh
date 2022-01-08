#!/bin/bash

DEST="/media/sam/$2"
LIB_DEST="$DEST/lib"

cp *.py $DEST
cp lib/* $LIB_DEST
cp "config/$1.json" "$DEST/config.json"
