#!/usr/bin/env python3
"""
Create seasonal mean maps of MODIS and VIIRS NNR AOD data
Produces combined figures with MODIS, VIIRS, and difference plots
Uses natural log scale for AOD
Grid cells with no data are grayed out
"""

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.ticker as mticker
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configuration
OUTPUT_DIR = Path('./seasonal_maps')

# Dataset configurations
DATASETS = {
    'modis': {
        'name': 'MODIS',
        'base_dir': '/nobackup/NNR/VIIRS/noaa20/modis/nnr_003',
        'surface_types': {
            'dt_land': {
                'path': '/nobackup/NNR/VIIRS/noaa20/modis/nnr_003',
                'pattern': '*land.{year}{month:02d}*.nc4',
                'label': 'DT Land'
            },
            'dt_ocean': {
                'path': '/nobackup/NNR/VIIRS/noaa20/modis/nnr_003',
                'pattern': '*ocean.{year}{month:02d}*.nc4',
                'label': 'DT Ocean'
            },
            'db_deep': {
                'path': '/nobackup/NNR/VIIRS/noaa20/modis/nnr_003',
                'pattern': '*deep.{year}{month:02d}*.nc4',
                'label': 'DB Deep'
            }
        }
    },
    'viirs': {
        'name': 'VIIRS',
        'base_dir': '/nobackup/NNR/VIIRS/noaa20/nnr_001_v001_DAtest_v2',
        'surface_types': {
            'dt_land': {
                'path': '/nobackup/NNR/VIIRS/noaa20/nnr_001_v001_DAtest_v2',
                'pattern': '*dt_land.{year}{month:02d}*.nc4',
                'label': 'DT Land'
            },
            'dt_ocean': {
                'path': '/nobackup/NNR/VIIRS/noaa20/nnr_001_v001_DAtest_v2',
                'pattern': '*dt_ocean.{year}{month:02d}*.nc4',
                'label': 'DT Ocean'
            },
            'db_deep': {
                'path': '/nobackup/NNR/VIIRS/noaa20/nnr_001_v001_DAtest_v2',
                'pattern': '*db_deep.{year}{month:02d}*.nc4',
                'label': 'DB Deep'
            }
        }
    }
    }


def get_files_for_month(directory, pattern, year, month):
    """Get all files for a specific month using pattern"""
    dir_path = Path(directory)
    file_pattern = pattern.format(year=year, month=month)
    files = sorted(dir_path.glob(file_pattern))
    return files

def load_data(files, var_name='tau'):
    """Load and combine files, handling missing values"""
    datasets = []

    for file in files:
        try:
            ds = xr.open_dataset(file)
            # Replace fill values with NaN
            if var_name in ds:
                ds[var_name] = ds[var_name].where(ds[var_name] < 900)
            datasets.append(ds)
        except Exception as e:
            print(f"Warning: Could not read {file}: {e}")
            continue

    if not datasets:
        return None

    # Concatenate along time dimension
    combined = xr.concat(datasets, dim='time')
    return combined

def compute_mean(combined_ds, var_name='tau'):
    """Compute mean, handling NaN values"""
    if combined_ds is None or var_name not in combined_ds:
        return None

    # Compute mean along time dimension, ignoring NaN
    time_mean = combined_ds[var_name].mean(dim='time', skipna=True)

    # Squeeze out the lev dimension if it exists and has size 1
    if 'lev' in time_mean.dims and time_mean.sizes['lev'] == 1:
        time_mean = time_mean.isel(lev=0)

    return time_mean

def merge_surface_types(data_dict):
    """Merge different surface types into one dataset"""
    # Collect valid data arrays
    valid_data = []
    for key, data in data_dict.items():
        if data is not None:
            valid_data.append(data)

    if not valid_data:
        return None

    # Stack and compute mean, ignoring NaN
    stacked = xr.concat(valid_data, dim='surface')
    merged = stacked.mean(dim='surface', skipna=True)

    return merged

def process_dataset(dataset_key, dataset_config, year, months, var_name):
    """Process one dataset (MODIS or VIIRS)"""
    dataset_name = dataset_config['name']
    surface_types = dataset_config['surface_types']

    print(f"\n  Processing {dataset_name}")

    data_dict = {}

    # Process each surface type
    for surf_key, surf_config in surface_types.items():
        surf_label = surf_config['label']
        surf_path = surf_config['path']
        surf_pattern = surf_config['pattern']

        print(f"    Surface type: {surf_label}")

        # Get files
        files = []
        for month in months:
            files.append(get_files_for_month(surf_path, surf_pattern, year, month))
        print(f"      Files found: {len(files)}")

        if files:
            combined = load_data(files, var_name)
            mean_data = compute_mean(combined, var_name)
            data_dict[surf_key] = mean_data
        else:
            data_dict[surf_key] = None

    # Create merged
    print(f"    Creating merged data for {dataset_name}")
    merged = merge_surface_types(data_dict)

    return data_dict, merged

def process_season(year, season, months, dataset_keys=None):
    """Process one season of data"""
    if dataset_keys is None:
        dataset_keys = ['modis', 'viirs']

    print(f"\n{'='*60}")
    print(f"Processing {year}-{months}")
    print(f"Datasets: {', '.join([DATASETS[k]['name'] for k in dataset_keys])}")
    print(f"{'='*60}")

    # Create output directory
    season_dir = OUTPUT_DIR / f"{year}{season}"
    season_dir.mkdir(parents=True, exist_ok=True)

    # Process each variable
    for var_name in ['tau', 'tau_']:
        print(f"\nProcessing variable: {var_name}")

        # Process both datasets
        modis_data = {}
        viirs_data = {}
        modis_merged = None
        viirs_merged = None

        if 'modis' in dataset_keys:
            modis_data, modis_merged = process_dataset(
                'modis', DATASETS['modis'], year, months, var_name
            )

        if 'viirs' in dataset_keys:
            viirs_data, viirs_merged = process_dataset(
                'viirs', DATASETS['viirs'], year, months, var_name
            )

        # Create combined figures for each surface type
        print(f"\n  Creating combined figures")

        for surf_key in ['dt_land', 'dt_ocean', 'db_deep']:
            modis_surf = modis_data.get(surf_key)
            viirs_surf = viirs_data.get(surf_key)

            if modis_surf is not None or viirs_surf is not None:
                surf_label = DATASETS['modis']['surface_types'][surf_key]['label']
                output_file = season_dir / f"combined_{var_name}_{surf_key}_{year}{season}.pdf"

                title = f"{surf_label} - {var_name} - {year}-{season}"
                plot_combined_figure(
                    modis_surf, viirs_surf, title, output_file
                )

        # Create combined figure for merged data
        if modis_merged is not None or viirs_merged is not None:
            output_file = month_dir / f"combined_{var_name}_merged_{year}{season}.pdf"
            title = f"Merged All Surface Types - {var_name} - {year}-{season}"
            plot_combined_figure(
                modis_merged, viirs_merged, title, output_file
            )

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Create seasonal mean AOD maps')
    parser.add_argument('year', type=int, help='Year (e.g., 2019)')
    parser.add_argument('season', type=int, help='Season (DJF,MAM,JJA,SON)')
    parser.add_argument('--datasets', nargs='+', choices=list(DATASETS.keys()),
                       default=['modis', 'viirs'],
                       help='Datasets to process (default: modis viirs)')
    parser.add_argument('--output-dir', type=str,
                       help='Output directory (default: ./seasonal_maps)')

    args = parser.parse_args()

    seasons = {'DJF': [12,1,2],
               'MAM': [3,4,5],
               'JJA': [6,7,8],
               'SON': [9,10,11]}


    # Validate month
    if args.season not in seasons:
        print(f"Error: Month must be in {list(seasons.keys())}")
        return

    # Set output directory if provided
    if args.output_dir:
        global OUTPUT_DIR
        OUTPUT_DIR = Path(args.output_dir)

    # Process the month
    process_season(args.year, season, seasons[season], args.datasets)

    print(f"\n{'='*60}")
    print(f"Processing complete!")
    print(f"Output directory: {OUTPUT_DIR / f'{args.year}{args.season}'}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()            
