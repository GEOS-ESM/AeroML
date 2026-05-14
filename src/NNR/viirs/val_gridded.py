#!/usr/bin/env python3
"""
Create seasonal mean maps of MODIS and VIIRS NNR AOD data
Produces combined figures with MODIS, VIIRS, and difference plots
Uses natural log scale for AOD
Grid cells with no data are grayed out
"""
import argparse
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
                'pattern': '*MYD04*land.{year}{month:02d}*.nc4',
                'label': 'DT Land'
            },
            'dt_ocean': {
                'path': '/nobackup/NNR/VIIRS/noaa20/modis/nnr_003',
                'pattern': '*MYD04*ocean.{year}{month:02d}*.nc4',
                'label': 'DT Ocean'
            },
            'db_deep': {
                'path': '/nobackup/NNR/VIIRS/noaa20/modis/nnr_003',
                'pattern': '*MYD04*deep.{year}{month:02d}*.nc4',
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
    """Process one dataset (MODIS or VIIRS) - Returns full time series, not means"""
    dataset_name = dataset_config['name']
    surface_types = dataset_config['surface_types']

    print(f"\n  Loading time series for {dataset_name}")

    data_dict = {}

    # Process each surface type
    for surf_key, surf_config in surface_types.items():
        surf_label = surf_config['label']
        surf_path = surf_config['path']
        surf_pattern = surf_config['pattern']

        print(f"    Surface type: {surf_label}")

        # Get files (using extend to create a flat list, not a list of lists)
        files = []
        for month in months:
            files.extend(get_files_for_month(surf_path, surf_pattern, year, month))
            
        print(f"      Files found: {len(files)}")

        if files:
            combined = load_data(files, var_name)
            # We no longer compute the mean here! We need the full time series for masking.
            data_dict[surf_key] = combined
        else:
            data_dict[surf_key] = None

    return data_dict

def process_season(year, season_name, months, dataset_keys=None, do_plot=False, read_nc=False):
    """Process one season of data with strict MODIS/VIIRS collocation"""
    if dataset_keys is None:
        dataset_keys = ['modis', 'viirs']

    print(f"\n{'='*60}")
    print(f"Processing {year}-{season_name} (Months: {months})")
    print(f"Datasets: {', '.join([DATASETS[k]['name'] for k in dataset_keys])}")
    print(f"{'='*60}")

    season_dir = OUTPUT_DIR / f"{year}{season_name}"
    season_dir.mkdir(parents=True, exist_ok=True)

    for var_name in ['tau', 'tau_']:
        print(f"\nProcessing variable: {var_name}")
        
        modis_data = {}
        viirs_data = {}
        modis_merged = None
        viirs_merged = None

        if read_nc:
            # --- PATH 1: READ INTERMEDIARY NETCDF FILES ---
            print(f"  Reading existing intermediary NetCDF files...")
            
            for surf_key in ['dt_land', 'dt_ocean', 'db_deep']:
                nc_file = season_dir / f"collocated_{var_name}_{surf_key}_{year}{season_name}.nc"
                if nc_file.exists():
                    ds = xr.open_dataset(nc_file)
                    modis_data[surf_key] = ds['modis'] if 'modis' in ds else None
                    viirs_data[surf_key] = ds['viirs'] if 'viirs' in ds else None
                    print(f"    Loaded: {nc_file.name}")
                else:
                    modis_data[surf_key] = None
                    viirs_data[surf_key] = None
                    
            merged_file = season_dir / f"collocated_{var_name}_merged_{year}{season_name}.nc"
            if merged_file.exists():
                ds_merged = xr.open_dataset(merged_file)
                modis_merged = ds_merged['modis'] if 'modis' in ds_merged else None
                viirs_merged = ds_merged['viirs'] if 'viirs' in ds_merged else None
                print(f"    Loaded: {merged_file.name}")
                
        else:
            # --- PATH 2: PROCESS RAW DATA ---
            modis_ts_dict = process_dataset('modis', DATASETS['modis'], year, months, var_name) if 'modis' in dataset_keys else {}
            viirs_ts_dict = process_dataset('viirs', DATASETS['viirs'], year, months, var_name) if 'viirs' in dataset_keys else {}

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
                    ds_out.to_netcdf(season_dir / f"collocated_{var_name}_{surf_key}_{year}{season_name}.nc")

            modis_merged = merge_surface_types(modis_data) if 'modis' in dataset_keys else None
            viirs_merged = merge_surface_types(viirs_data) if 'viirs' in dataset_keys else None
            
            # Save merged NetCDF
            if modis_merged is not None or viirs_merged is not None:
                ds_out = xr.Dataset()
                if modis_merged is not None: ds_out['modis'] = modis_merged
                if viirs_merged is not None: ds_out['viirs'] = viirs_merged
                ds_out.to_netcdf(season_dir / f"collocated_{var_name}_merged_{year}{season_name}.nc")

        # --- PLOTTING (Happens regardless of how data was loaded) ---
        if do_plot:
            print(f"\n  Generating plots...")
            for surf_key in ['dt_land', 'dt_ocean', 'db_deep']:
                if modis_data.get(surf_key) is not None or viirs_data.get(surf_key) is not None:
                    surf_label = DATASETS['modis']['surface_types'][surf_key]['label']
                    plot_file = season_dir / f"combined_{var_name}_{surf_key}_{year}{season_name}.png"
                    title = f"{surf_label} - {var_name} - {year}-{season_name} (Collocated)"
                    plot_comparison_maps(modis_data.get(surf_key), viirs_data.get(surf_key), season_name, output_filename=plot_file)
                    print(f"    Saved Plot: {plot_file.name}")
                    
            if modis_merged is not None or viirs_merged is not None:
                plot_file = season_dir / f"combined_{var_name}_merged_{year}{season_name}.png"
                title = f"Merged All Surface Types - {var_name} - {year}-{season_name} (Collocated)"
                plot_comparison_maps(modis_merged, viirs_merged, season_name, output_filename=plot_file)
                print(f"    Saved Plot: {plot_file.name}")


def plot_comparison_maps(control_data, noaa20_data, season, output_filename=None):
    """
    Create a figure with 3 maps: control, NOAA20, and difference
    """
    # Create figure with 3 subplots
    fig = plt.figure(figsize=(18, 6))

    projection = ccrs.PlateCarree()

    # Calculate the difference data
    diff_data = control_data - noaa20_data

    # Titles for the plots
    titles = [
        f"{season} mean AOD - MODIS",
        f"{season} mean AOD - NOAA20",
        f"Difference (MODIS - NOAA20)"
    ]

    # Data for each plot
    plot_data = [control_data, noaa20_data, diff_data]

    # Create subplots
    for i in range(3):
        ax = fig.add_subplot(1, 3, i+1, projection=projection)

        # Add map features
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
        ax.add_feature(cfeature.BORDERS, linewidth=0.3)
        ax.add_feature(cfeature.OCEAN, color='gray', alpha=0.5)
        ax.add_feature(cfeature.LAND, color='gray', alpha=0.5)

        # Set global extent
        ax.set_global()

        # Add gridlines
        gl = ax.gridlines(draw_labels=True, linewidth=0.5, alpha=0.5)
        gl.top_labels = False
        gl.right_labels = False

        # Get data for this plot
        data = plot_data[i]
        lon = data.lon.values
        lat = data.lat.values

        if lon.max() > 180:
            lon = np.where(lon > 180, lon - 360, lon)
            # Sort by longitude
            sort_idx = np.argsort(lon)
            lon = lon[sort_idx]
            data_values = data.values[:, sort_idx]
        else:
            data_values = data.values

        # Create colormap and norm based on which plot
        if i == 2:  # Difference plot - linear with imshow
            cmap = plt.cm.RdBu_r

            norm = mcolors.TwoSlopeNorm(vmin=-0.25, vcenter=0.0, vmax=0.25)

            extent = [lon.min(), lon.max(), lat.min(), lat.max()]
            im = ax.imshow(data_values,
                          cmap=cmap,
                          norm=norm,
                          extent=extent,
                          origin='lower',
                          transform=ccrs.PlateCarree(),
                          interpolation='bilinear')
        else:  # AOD plots - use imshow with log normalization
            # Handle zeros by setting minimum value
            data_values = np.maximum(data_values, 0.01)  # Replace zeros with 0.01

            # Use continuous colormap with log normalization
            cmap = plt.cm.viridis
            #cmap = plt.cm.inferno
            #cmap = plt.cm.plasma
            norm = mcolors.LogNorm(vmin=0.01, vmax=0.75)  # Log scale from 0.01 to 1.0

            # Use imshow
            extent = [lon.min(), lon.max(), lat.min(), lat.max()]
            im = ax.imshow(data_values,
                          cmap=cmap,
                          norm=norm,
                          extent=extent,
                          origin='lower',
                          transform=ccrs.PlateCarree(),
                          interpolation='bilinear')

        # Add colorbar with extend parameter (separate from extent)
        if i == 2:  # Difference plot
           cbar = plt.colorbar(im, ax=ax, orientation='horizontal',
                       pad=0.05, shrink=0.8, aspect=25,
                       extend='both')  # Triangles on both ends
        else:  # AOD plots
           cbar = plt.colorbar(im, ax=ax, orientation='horizontal',
                       pad=0.05, shrink=0.8, aspect=25,
                       extend='max')   # Triangle on high end only

        if i != 2:  # AOD plots - set custom log-spaced ticks
            # Custom tick positions (log-like spacing but not regular)
            custom_ticks = [0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 0.75]

            # Format tick labels as regular decimals (like MERRA-2)
            tick_labels = []
            for tick in custom_ticks:
                if tick < 0.1:
                    tick_labels.append(f'{tick:.2f}')
                else:
                    tick_labels.append(f'{tick:.1f}')

            # Remove all default ticks and only add the ones we want
            cbar.ax.tick_params(size=0)
            cbar.set_ticks([])
            cbar.set_ticks(custom_ticks) # Add only custom ticks
            cbar.set_ticklabels(tick_labels)
            cbar.ax.tick_params(size=4)

            cbar.set_label('AOD at 550nm', fontsize=10)
        else:  # Difference plot
            cbar.ax.minorticks_off()
            cbar.set_label('AOD 550nm Difference', fontsize=10)

        # Set title
        ax.set_title(titles[i], fontsize=12, fontweight='bold')

    plt.tight_layout()

    # Save if filename provided
    if output_filename:
        plt.savefig(output_filename, dpi=150, bbox_inches='tight')
        print(f"Plot saved as: {output_filename}")

#    plt.show()


if __name__ == '__main__':
    """Main function"""

    parser = argparse.ArgumentParser(description='Create seasonal mean AOD maps')
    parser.add_argument('year', type=int, help='Year (e.g., 2019)')
    parser.add_argument('season', type=str, help='Season (DJF,MAM,JJA,SON)')
    parser.add_argument('--datasets', nargs='+', choices=list(DATASETS.keys()),
                       default=['modis', 'viirs'],
                       help='Datasets to process (default: modis viirs)')
    parser.add_argument('--output-dir', type=str,
                       help='Output directory (default: ./seasonal_maps)')
    parser.add_argument('--plot', action='store_true',
                       help='Generate and save combined PDF figures')
    parser.add_argument('--read-nc', action='store_true',
                       help='Read intermediate NetCDF files instead of processing raw data')


    args = parser.parse_args()

    seasons = {'DJF': [12,1,2],
               'MAM': [3,4,5],
               'JJA': [6,7,8],
               'SON': [9,10,11]}


    # Validate month
    if args.season not in seasons:
        raise ValueError(f"Season must be in {list(seasons.keys())}")

    # Set output directory if provided
    if args.output_dir:
        OUTPUT_DIR = Path(args.output_dir)

    # Process the month
    process_season(args.year, args.season, seasons[args.season], args.datasets,
                   do_plot=args.plot, read_nc=args.read_nc)

    print(f"\n{'='*60}")
    print(f"Processing complete!")
    print(f"Output directory: {OUTPUT_DIR / f'{args.year}{args.season}'}")
    print(f"{'='*60}")

