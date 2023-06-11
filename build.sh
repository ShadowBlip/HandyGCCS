#!/bin/bash
rm -rf build dist src/handycon.egg-info
sudo rm -rf /usr/lib/python3*/site-packages/handycon*
sudo rm /usr/bin/handycon  
python -m build --wheel --no-isolation
sudo python -m installer dist/*.whl
