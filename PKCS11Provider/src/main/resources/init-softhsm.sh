#!/bin/bash
softhsm2-util --init-token --slot 0 --label softhsm --pin 1234 --so-pin 1234
