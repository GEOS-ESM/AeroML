import numpy as np
import pandas as pd
import pickle
import sys
sys.path.append('..')

from aod_models import run_all_models

def run_land(start_dir=""):
    edl_params = np.linspace(0, 1, 21)
    for edl_param in edl_params:
        print(f"RUNNING LAND MODEL for edl_param = {edl_param}...")
        transformed_features = pd.read_pickle(f"{start_dir}data/LAND_terra_transformed_features.pkl")
        transformed_target = pd.read_pickle(f"{start_dir}data/LAND_terra_transformed_targets.pkl")
        output_dir = f'{start_dir}model_outputs'
        run_all_models(transformed_features, transformed_target, output_dir, 'terra', edl_param=edl_param)

        transformed_features = pd.read_pickle(f"{start_dir}data/LAND_aqua_transformed_features.pkl")
        transformed_target = pd.read_pickle(f"{start_dir}data/LAND_aqua_transformed_targets.pkl")
        output_dir = f'{start_dir}model_outputs'
        run_all_models(transformed_features, transformed_target, output_dir, 'aqua', edl_param=edl_param)

if __name__ == '__main__':
    run_land()