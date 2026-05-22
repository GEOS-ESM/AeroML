#!/usr/bin/env python3
"""
Create monthly mean ts of MODIS and VIIRS NNR AOD data
Global and over specific target regions
Sample MODIS and VIIRS together
"""
import argparse
import numpy as np
import pandas as pd
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
OUTPUT_DIR = Path('./monthly_ts')

# Define target regions [lon_min, lon_max, lat_min, lat_max]
REGIONS = {
    'Global': [-180, 180, -90, 90],
    'North_America': [-130, -60, 20, 60],
    'South_America': [-85, -35, -55, 15],
    'Europe': [-10, 40, 35, 70],
    'East_Asia': [100, 150, 20, 50],
    'Australia': [112, 155, -45, -10],
    'North_Africa': [-20, 40, 10, 36],     # Captures the Sahara and Sahel
    'South_Africa': [10, 40, -35, -10],    # Southern half of the African continent
    'Mid_Atlantic': [-45, -15, 0, 30]      # Off the coast of Africa (great for dust transport)
}

# Dataset configurations
DATASETS = {
    'modis': {
        'name': 'MODIS',
        'base_dir': '/nobackup/NNR/VIIRS/noaa20/modis/nnr_003_refine_e/Level3',
        'surface_types': {
            'dt_land': {
                'path': '/nobackup/NNR/VIIRS/noaa20/modis/nnr_003_refine_e/Level3',
                'pattern': '*MYD04*land.{year}{month:02d}*.nc4',
                'label': 'DT Land'
            },
            'dt_ocean': {
                'path': '/nobackup/NNR/VIIRS/noaa20/modis/nnr_003_refine_e/Level3',
                'pattern': '*MYD04*ocean.{year}{month:02d}*.nc4',
                'label': 'DT Ocean'
            },
            'db_deep': {
                'path': '/nobackup/NNR/VIIRS/noaa20/modis/nnr_003_refine_e/Level3',
                'pattern': '*MYD04*deep.{year}{month:02d}*.nc4',
                'label': 'DB Deep'
            }
        }
    },
    'viirs': {
        'name': 'VIIRS',
        'base_dir': '/nobackup/NNR/VIIRS/noaa20/nnr_001_v001_DAtest_v2_refine_e/Level3',
        'surface_types': {
            'dt_land': {
                'path': '/nobackup/NNR/VIIRS/noaa20/nnr_001_v001_DAtest_v2_refine_e/Level3',
                'pattern': '*dt_land.{year}{month:02d}*.nc4',
                'label': 'DT Land'
            },
            'dt_ocean': {
                'path': '/nobackup/NNR/VIIRS/noaa20/nnr_001_v001_DAtest_v2_refine_e/Level3',
                'pattern': '*dt_ocean.{year}{month:02d}*.nc4',
                'label': 'DT Ocean'
            },
            'db_deep': {
                'path': '/nobackup/NNR/VIIRS/noaa20/nnr_001_v001_DAtest_v2_refine_e/Level3',
                'pattern': '*db_deep.{year}{month:02d}*.nc4',
                'label': 'DB Deep'
            }
        }
    }
}

def get_files_for_month(directory, pattern, year, month):
    """Get all files for a specific month using pattern and Y/M subdirectories"""
    # Construct the path with Y2019/M01 format
    dir_path = Path(directory) / f"Y{year}" / f"M{month:02d}"
    
    file_pattern = pattern.format(year=year, month=month)
    
    # Check if the directory exists before globbing (prevents errors on missing months/years)
    if not dir_path.exists():
        print(f"      Directory not found: {dir_path}")
        return []
        
    return sorted(dir_path.glob(file_pattern))

def load_data(files, var_name='tau'):
    datasets = []
    for file in files:
        try:
            ds = xr.open_dataset(file)
            if var_name in ds:
                ds[var_name] = ds[var_name].where(ds[var_name] < 900)
            datasets.append(ds)
        except Exception as e:
            print(f"Warning: Could not read {file}: {e}")
            continue

    if not datasets: return None
    return xr.concat(datasets, dim='time')

def compute_mean(combined_ds, var_name='tau'):
    if combined_ds is None or var_name not in combined_ds: return None
    time_mean = combined_ds[var_name].mean(dim='time', skipna=True)
    if 'lev' in time_mean.dims and time_mean.sizes['lev'] == 1:
        time_mean = time_mean.isel(lev=0)
    return time_mean

def merge_surface_types(data_dict):
    valid_data = [data for key, data in data_dict.items() if data is not None]
    if not valid_data: return None
    stacked = xr.concat(valid_data, dim='surface')
    return stacked.mean(dim='surface', skipna=True)

def get_regional_mean(da, bounds):
    """Calculate area-weighted spatial mean over a bounding box."""
    if da is None: return np.nan
    lon_min, lon_max, lat_min, lat_max = bounds
    
    # Subset
    subset = da.sel(lon=slice(lon_min, lon_max), lat=slice(lat_min, lat_max))
    if subset.size == 0: return np.nan
    
    # Cosine latitude weighting
    weights = np.cos(np.deg2rad(subset.lat))
    weights.name = "weights"
    return subset.weighted(weights).mean(dim=['lat', 'lon'], skipna=True).item()

def process_dataset(dataset_key, dataset_config, year, months, var_name):
    dataset_name = dataset_config['name']
    surface_types = dataset_config['surface_types']
    print(f"\n  Loading time series for {dataset_name}")
    data_dict = {}

    for surf_key, surf_config in surface_types.items():
        surf_label = surf_config['label']
        surf_path = surf_config['path']
        surf_pattern = surf_config['pattern']
        print(f"    Surface type: {surf_label}")

        files = []
        for month in months:
            files.extend(get_files_for_month(surf_path, surf_pattern, year, month))
        
        print(f"      Files found: {len(files)}")
        data_dict[surf_key] = load_data(files, var_name) if files else None

    return data_dict

def process_ts(syear, eyear, dataset_keys=None, do_plot=False, read_nc=False):
    if dataset_keys is None: dataset_keys = ['modis', 'viirs']
    
    # List to store our time series rows
    ts_records = []

    print(f"\n{'='*60}")
    for year in np.arange(syear, eyear+1):
        year_dir = OUTPUT_DIR / f"{year}"
        year_dir.mkdir(parents=True, exist_ok=True)
        
        for month in np.arange(1,13):
            month_str = f"{month:02d}"
            print(f"Processing {year}-{month_str}")
            print(f"Datasets: {', '.join([DATASETS[k]['name'] for k in dataset_keys])}")
            print(f"{'='*60}")

            for var_name in ['tau', 'tau_']:
                print(f"\nProcessing variable: {var_name}")
                modis_data, viirs_data = {}, {}
                modis_merged, viirs_merged = None, None

                if read_nc:
                    print(f"  Reading existing intermediary NetCDF files...")
                    for surf_key in ['dt_land', 'dt_ocean', 'db_deep']:
                        nc_file = year_dir / f"collocated_{var_name}_{surf_key}_{year}{month_str}.nc"
                        if nc_file.exists():
                            ds = xr.open_dataset(nc_file)
                            modis_data[surf_key] = ds['modis'] if 'modis' in ds else None
                            viirs_data[surf_key] = ds['viirs'] if 'viirs' in ds else None
                        else:
                            modis_data[surf_key], viirs_data[surf_key] = None, None
                    
                    merged_file = year_dir / f"collocated_{var_name}_merged_{year}{month_str}.nc"
                    if merged_file.exists():
                        ds_merged = xr.open_dataset(merged_file)
                        modis_merged = ds_merged['modis'] if 'modis' in ds_merged else None
                        viirs_merged = ds_merged['viirs'] if 'viirs' in ds_merged else None
                else:
                    modis_ts_dict = process_dataset('modis', DATASETS['modis'], year, [month], var_name) if 'modis' in dataset_keys else {}
                    viirs_ts_dict = process_dataset('viirs', DATASETS['viirs'], year, [month], var_name) if 'viirs' in dataset_keys else {}

                    print(f"\n  Collocating, calculating means, and saving NetCDF...")
                    for surf_key in ['dt_land', 'dt_ocean', 'db_deep']:
                        modis_ts = modis_ts_dict.get(surf_key)
                        viirs_ts = viirs_ts_dict.get(surf_key)

                        if modis_ts is not None and viirs_ts is not None:
                            modis_aligned, viirs_aligned = xr.align(modis_ts, viirs_ts, join='inner')
                            m_var, v_var = modis_aligned[var_name], viirs_aligned[var_name]
                            valid_mask = m_var.notnull() & v_var.notnull()

                            modis_data[surf_key] = m_var.where(valid_mask).mean(dim='time', skipna=True)
                            viirs_data[surf_key] = v_var.where(valid_mask).mean(dim='time', skipna=True)

                            if 'lev' in modis_data[surf_key].dims and modis_data[surf_key].sizes['lev'] == 1:
                                modis_data[surf_key] = modis_data[surf_key].isel(lev=0)
                                viirs_data[surf_key] = viirs_data[surf_key].isel(lev=0)
                        else:
                            modis_data[surf_key] = compute_mean(modis_ts, var_name) if modis_ts is not None else None
                            viirs_data[surf_key] = compute_mean(viirs_ts, var_name) if viirs_ts is not None else None

                        # Save individual surface type NetCDF
                        if modis_data[surf_key] is not None or viirs_data[surf_key] is not None:
                            ds_out = xr.Dataset()
                            if modis_data[surf_key] is not None: ds_out['modis'] = modis_data[surf_key]
                            if viirs_data[surf_key] is not None: ds_out['viirs'] = viirs_data[surf_key]
                            ds_out.to_netcdf(year_dir / f"collocated_{var_name}_{surf_key}_{year}{month_str}.nc")

                    modis_merged = merge_surface_types(modis_data) if 'modis' in dataset_keys else None
                    viirs_merged = merge_surface_types(viirs_data) if 'viirs' in dataset_keys else None
                    
                    if modis_merged is not None or viirs_merged is not None:
                        ds_out = xr.Dataset()
                        if modis_merged is not None: ds_out['modis'] = modis_merged
                        if viirs_merged is not None: ds_out['viirs'] = viirs_merged
                        ds_out.to_netcdf(year_dir / f"collocated_{var_name}_merged_{year}{month_str}.nc")

                # Calculate and store regional means for time series
                if modis_merged is not None and viirs_merged is not None:
                    row = {'Year': year, 'Month': month, 'Variable': var_name}
                    for reg_name, bounds in REGIONS.items():
                        m_val = get_regional_mean(modis_merged, bounds)
                        v_val = get_regional_mean(viirs_merged, bounds)
                        row[f'MODIS_{reg_name}'] = m_val
                        row[f'VIIRS_{reg_name}'] = v_val
                        row[f'Diff_{reg_name}'] = m_val - v_val if (pd.notnull(m_val) and pd.notnull(v_val)) else np.nan
                    ts_records.append(row)


    # Save CSV and plot Time Series at the end
    if ts_records:
        df = pd.DataFrame(ts_records)
        df['Date'] = pd.to_datetime(df[['Year', 'Month']].assign(DAY=1))
        df.set_index('Date', inplace=True)
        
        csv_path = OUTPUT_DIR / f"regional_monthly_means_{syear}-{eyear}.csv"
        df.to_csv(csv_path)
        print(f"\nSaved regional time series data to: {csv_path}")
        if do_plot:
            plot_timeseries(df)
    else:
        print("\nNo time series data was accumulated.")

import math

def plot_timeseries(df):
    """Create multi-panel time series plots with a region reference map in a grid"""
    print("Generating time series plots...")

    # Define colors for the bounding boxes
    box_colors = plt.cm.tab10.colors

    for var_name in df['Variable'].unique():
        df_var = df[df['Variable'] == var_name]

        # Calculate Grid Layout (2 columns)
        total_plots = len(REGIONS) + 1  # 1 map + N regions
        cols = 2
        rows = math.ceil(total_plots / cols)

        # Create figure with dynamic height based on rows
        fig = plt.figure(figsize=(16, 4 * rows))

        # 1. Add Region Reference Map (Top-Left Panel, Index 1)
        ax_map = fig.add_subplot(rows, cols, 1, projection=ccrs.PlateCarree())
        ax_map.set_global()
        ax_map.add_feature(cfeature.COASTLINE, linewidth=0.5)
        ax_map.add_feature(cfeature.BORDERS, linewidth=0.3)
        ax_map.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.5)
        ax_map.add_feature(cfeature.OCEAN, facecolor='azure', alpha=0.5)
        ax_map.set_title("Defined Target Regions", fontsize=14, fontweight='bold')

        # Draw boxes for each region
        for idx, (reg_name, bounds) in enumerate(REGIONS.items()):
            lon_min, lon_max, lat_min, lat_max = bounds

            # Skip drawing a box for the Global domain
            if reg_name.lower() == 'global':
                continue

            color = box_colors[idx % len(box_colors)]
            label_name = reg_name.replace('_', ' ')

            # Draw rectangle
            ax_map.plot([lon_min, lon_max, lon_max, lon_min, lon_min],
                        [lat_min, lat_min, lat_max, lat_max, lat_min],
                        color=color, linewidth=2.5,
                        transform=ccrs.PlateCarree(), label=label_name)

            # Add text label in the center of the box
            center_lon = (lon_min + lon_max) / 2
            center_lat = (lat_min + lat_max) / 2
            ax_map.text(center_lon, center_lat, label_name,
                        color='black', fontsize=9, fontweight='bold',
                        ha='center', va='center', transform=ccrs.PlateCarree(),
                        bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))
            
        # 2. Add Time Series Plots (Filling the rest of the grid)
        axes = []
        for i in range(len(REGIONS)):
            plot_index = i + 2 # Start at index 2
            
            # Share the x-axis with the first time series plot
            if i == 0:
                ax = fig.add_subplot(rows, cols, plot_index)
            else:
                ax = fig.add_subplot(rows, cols, plot_index, sharex=axes[0])
            axes.append(ax)

        for ax, reg_name in zip(axes, REGIONS.keys()):
            # Plot raw AOD
            l1 = ax.plot(df_var.index, df_var[f'MODIS_{reg_name}'], 'b-o', label='MODIS', markersize=4)
            l2 = ax.plot(df_var.index, df_var[f'VIIRS_{reg_name}'], 'r-s', label='VIIRS', markersize=4)

            ax.set_title(f"{reg_name.replace('_', ' ')} - {var_name}")
            ax.set_ylabel("AOD")
            ax.grid(True, linestyle=':', alpha=0.7)

            # Ensure x-axis tick labels are visible for all subplots in the grid layout
            ax.tick_params(labelbottom=True)

            # Combined Legend
            lines = l1 + l2
            labels = [l.get_label() for l in lines]
            ax.legend(lines, labels, loc='upper left')

            ax.set_xlabel("Date")

        plt.tight_layout()
        ts_plot_file = OUTPUT_DIR / f"timeseries_comparison_{var_name}.png"
        plt.savefig(ts_plot_file, dpi=300, bbox_inches='tight')
        plt.close(fig)  # Close figure to free up memory
        print(f"Saved Time Series Plot: {ts_plot_file}")
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create monthly mean AOD maps and timeseries')
    parser.add_argument('start_year', type=int, help='Start Year (e.g., 2019)')
    parser.add_argument('end_year', type=int, help='End Year (e.g. 2025)')
    parser.add_argument('--datasets', nargs='+', choices=list(DATASETS.keys()), default=['modis', 'viirs'])
    parser.add_argument('--output-dir', type=str, help='Output directory (default: ./monthly_ts)')
    parser.add_argument('--plot', action='store_true', help='Generate and save spatial map figures')
    parser.add_argument('--read-nc', action='store_true', help='Read intermediate NetCDF files instead of raw data')

    args = parser.parse_args()

    if args.output_dir:
        OUTPUT_DIR = Path(args.output_dir)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    process_ts(args.start_year, args.end_year, args.datasets, do_plot=args.plot, read_nc=args.read_nc)

    print(f"\n{'='*60}")
    print(f"Processing complete!")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"{'='*60}")
