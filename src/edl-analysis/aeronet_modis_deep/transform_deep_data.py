import sys

import pandas as pd
sys.path.append('..')

from qc_c6 import QC_DEEP
from data.box_cox_transform_data import transform_data

PREFIX = "DEEP"

def generate_transformed_deep_data():
    # Aqua Satellite (prefix: myd)
    aqua  = '../data/giant_C6_10km_Aqua_20151005.nc'
    terra = '../data/giant_C6_10km_Terra_20150921.nc'

    # Ocean Model: Features
    Angles = ['SolarZenith','ScatteringAngle', 'GlintAngle'] # Satellite geometry

    Reflectances = [   'mRef412',
                            'mRef470',
                            'mRef660',
                            ] # Satellite reflectance: Deep Blue channels
        
    Surface = [ 'mSre412',
                'mSre470',
                'mSre660'] # Derived from satellite as well
    
    Species = [ 'fdu','fcc','fsu']

    Features = Angles + Reflectances + Surface + Species

    modd_aod_ests = ['mTau470','mTau550','mTau660']

    # Ocean Model: Targets (In-situ AERONET Measurements)
    Target = ['aTau470','aTau550','aTau660']

    # Ingest Quality Controled Data
    Albedo = None
    aFilter = None
    outliers = 5.

    """
    TERRA SATELLITE
    """

    modd_terra = QC_DEEP(terra,Albedo=Albedo,verbose=True,aFilter=aFilter, outliers=5)
    modd_aod_target_terra = modd_terra.toDataFrame(Vars=modd_aod_ests)

    features_terra = modd_terra.toDataFrame(Vars=Features)
    target_terra = modd_terra.toDataFrame(Vars=Target)
    modd_target_terra = modd_terra.toDataFrame(Vars=modd_aod_ests)
    
    transformed_features, transformed_features_lambdas, transformed_targets, transformed_targets_lambdas, transformed_modd_targets, transformed_modd_targets_lambdas = transform_data(features_terra, target_terra, modd_target_terra, 1e-2, 1e-2)

    modd_aod_target_terra.to_pickle(f"data/{PREFIX}_terra_modd_aod_target.pkl")

    transformed_features.to_pickle(f"data/{PREFIX}_terra_transformed_features.pkl")
    transformed_features_lambdas.to_pickle(f"data/{PREFIX}_terra_transformed_features_lambdas.pkl")  
    transformed_targets.to_pickle(f"data/{PREFIX}_terra_transformed_targets.pkl")
    transformed_targets_lambdas.to_pickle(f"data/{PREFIX}_terra_transformed_targets_lambdas.pkl")  
    transformed_modd_targets.to_pickle(f"data/{PREFIX}_terra_transformed_modd_targets.pkl")
    transformed_modd_targets_lambdas.to_pickle(f"data/{PREFIX}_terra_transformed_modd_targets_lambdas.pkl") 

    """
    AQUA SATELLITE
    """

    modd_aqua  = QC_DEEP(aqua,  Albedo=Albedo, verbose=True, aFilter=aFilter, outliers=5)
    modd_aod_target_aqua = modd_aqua.toDataFrame(Vars=modd_aod_ests)

    features_aqua = modd_aqua.toDataFrame(Vars=Features)
    target_aqua = modd_aqua.toDataFrame(Vars=Target)
    modd_target_aqua = modd_aqua.toDataFrame(Vars=modd_aod_ests)

    transformed_features, transformed_features_lambdas, transformed_targets, transformed_targets_lambdas, transformed_modd_targets, transformed_modd_targets_lambdas = transform_data(features_aqua, target_aqua, modd_target_aqua, 1e-2, 1e-2)

    modd_aod_target_aqua.to_pickle(f"data/{PREFIX}_aqua_modd_aod_target.pkl")
    
    transformed_features.to_pickle(f"data/{PREFIX}_aqua_transformed_features.pkl")
    transformed_features_lambdas.to_pickle(f"data/{PREFIX}_aqua_transformed_features_lambdas.pkl")  
    transformed_targets.to_pickle(f"data/{PREFIX}_aqua_transformed_targets.pkl")
    transformed_targets_lambdas.to_pickle(f"data/{PREFIX}_aqua_transformed_targets_lambdas.pkl")  
    transformed_modd_targets.to_pickle(f"data/{PREFIX}_aqua_transformed_modd_targets.pkl")
    transformed_modd_targets_lambdas.to_pickle(f"data/{PREFIX}_aqua_transformed_modd_targets_lambdas.pkl")  

if __name__ == '__main__':
    generate_transformed_deep_data()


