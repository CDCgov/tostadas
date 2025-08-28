#!/bin/bash -ue
set -x
cat batch_1.csv | head -n 1 > submission_report.csv
for f in batch_1.csv; do
    tail -n +2 "$f" >> submission_report.csv
done
