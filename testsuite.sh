#!/bin/bash
set -ex

git clone https://github.com/sfz/tests.git /tmp/suite

out=$(sfzlint --no-pickle "/tmp/suite/sfz1 basic tests")
if [ -n "${out}" ]; then
  echo "v1 tests failed"
  exit 1
fi
out=$(sfzlint --no-pickle "/tmp/suite/sfz2 basic tests")
if [ -n "${out}" ]; then
  echo "v2 tests failed"
  exit 2
fi

rm -rf /tmp/suite
