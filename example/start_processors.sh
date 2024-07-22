#!/bin/bash

echo "Starting 5 workers..."

for i in $(seq 1 5)
do
    python processor/processor.py $i &
done

wait
