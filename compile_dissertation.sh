# !/bin/bash

pandoc "./dissertation.md" --lua-filter="./filters/columns/columns.lua" --output "./dissertation.pdf"