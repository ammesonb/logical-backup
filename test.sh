#!/bin/bash
DEBUG=
if [ -n "${1}" ]; then
  DEBUG="-vv"
fi

pytest --cov=logical_backup --cov-report term-missing $DEBUG tests/
