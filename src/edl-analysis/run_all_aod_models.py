import numpy as np
import pandas as pd
import sys
from aeronet_modis_ocean.run_ocean_models import run_ocean
from aeronet_modis_land.run_land_models import run_land
from aeronet_modis_deep.run_deep_models import run_deep

def run_main():
    run_ocean(start_dir="aeronet_modis_ocean/")
    run_land(start_dir="aeronet_modis_land/")
    run_deep(start_dir="aeronet_modis_deep/")

if __name__ == '__main__':
    run_main()