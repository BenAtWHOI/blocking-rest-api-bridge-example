#!/bin/bash

echo "Starting 5 workers..."

for i in {1..5}
do
    python processor/processor.py &
done

wait