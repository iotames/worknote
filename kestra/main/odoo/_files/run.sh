#!/bin/bash

ARG_OPT="$1"

echo "---------ARG_OPT(${ARG_OPT})-------"

chmod +x /home/santic/odoorun/run.sh

if [ -z "${ARG_OPT}" ]; then
    echo "-----EMPTY---ARG_OPT: updaate......"
    /home/santic/odoorun/run.sh update
    exit 0
fi

if [ "${ARG_OPT}" = "update" ]; then
    echo "------update......"
    /home/santic/odoorun/run.sh update
    exit 0
fi
if [ "${ARG_OPT}" = "restart" ]; then
    echo "----restart......"
    docker restart odoowebtest
    exit 0
fi
