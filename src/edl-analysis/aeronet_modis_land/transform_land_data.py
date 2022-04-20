import sys

import pandas as pd
sys.path.append('..')

from qc_c6 import QC_LAND
from data.box_cox_transform_data import transform_data

PREFIX = "LAND"

def generate_transformed_land_data():
    # Aqua Satellite (prefix: myd)
    aqua = '../data/giant_C6_10km_Aqua_20151005.nc'
    terra = '../data/giant_C6_10km_Terra_20150921.nc'

    # Ocean Model: Features
    Angles = ['SolarZenith','ScatteringAngle', 'GlintAngle'] # Satellite geometry

    Reflectances = [   'mRef412',
                    'mRef440',  
                    'mRef470',
                    'mRef550',
                    'mRef660',
                    'mRef870',
                    'mRef1200',
                    'mRef1600',
                    'mRef2100'] # Dark Target Satellite reflectance
    
    Surface = [ 'BRDF470',
                'BRDF550',
                'BRDF650',
                'BRDF850',
                'BRDF1200',
                'BRDF1600',
                'BRDF2100' ] # Derived from satellite as well
    
    Surface2 = [ 'mSre470',
                'mSre660',
                'mSre2100'] 

    AirMassFactor = [ 'AMF']
        
    Species = [ 'fdu','fcc','fsu']

    Features = Angles + Reflectances + Surface + Species + AirMassFactor


    # Ocean Model: Targets (In-situ AERONET Measurements)
    Target = ['aTau470','aTau550','aTau660']

    modl_aod_ests = ['mTau470','mTau550','mTau660']

    # Ingest Quality Controlled Data
    Albedo = ['MCD43C1',] # BRDF surface characteristics
    aFilter = Surface # additional filters based on choice of surface

    """
    TERRA SATELLITE
    """

    modl_terra = QC_LAND(terra, Albedo=Albedo, verbose=True, aFilter=aFilter, outliers=5)
    modl_aod_target_terra = modl_terra.toDataFrame(Vars=modl_aod_ests)

    features_terra = modl_terra.toDataFrame(Vars=Features)
    features_terra[Reflectances].divide(features_terra['AMF'], axis='index')
    features_terra = features_terra[[a for a in features_terra.columns if a != 'AMF']]
    target_terra = modl_terra.toDataFrame(Vars=Target)
    modl_target_terra = modl_terra.toDataFrame(Vars=modl_aod_ests)
    
    transformed_features, transformed_features_lambdas, transformed_targets, transformed_targets_lambdas, transformed_modl_targets, transformed_modl_targets_lambdas = transform_data(features_terra, target_terra, modl_target_terra, 1e-2, 1e-2)

    modl_aod_target_terra.to_pickle(f"data/{PREFIX}_terra_modl_aod_target.pkl")

    transformed_features.to_pickle(f"data/{PREFIX}_terra_transformed_features.pkl")
    transformed_features_lambdas.to_pickle(f"data/{PREFIX}_terra_transformed_features_lambdas.pkl")  
    transformed_targets.to_pickle(f"data/{PREFIX}_terra_transformed_targets.pkl")
    transformed_targets_lambdas.to_pickle(f"data/{PREFIX}_terra_transformed_targets_lambdas.pkl")  
    transformed_modl_targets.to_pickle(f"data/{PREFIX}_terra_transformed_modl_targets.pkl")
    transformed_modl_targets_lambdas.to_pickle(f"data/{PREFIX}_terra_transformed_modl_targets_lambdas.pkl")

    """
    AQUA SATELLITE
    """

    modl_aqua  = QC_LAND(aqua,  Albedo=Albedo, verbose=True, aFilter=aFilter, outliers=5)
    modl_aod_target_aqua = modl_aqua.toDataFrame(Vars=modl_aod_ests)

    features_aqua = modl_aqua.toDataFrame(Vars=Features)
    features_aqua[Reflectances].divide(features_aqua['AMF'], axis='index')
    features_aqua = features_aqua[[a for a in features_aqua.columns if a != 'AMF']]
    target_aqua = modl_aqua.toDataFrame(Vars=Target)
    modl_target_aqua = modl_aqua.toDataFrame(Vars=modl_aod_ests)

    transformed_features, transformed_features_lambdas, transformed_targets, transformed_targets_lambdas, transformed_modl_targets, transformed_modl_targets_lambdas = transform_data(features_aqua, target_aqua, modl_target_aqua, 1e-2, 1e-2)

    modl_aod_target_aqua.to_pickle(f"data/{PREFIX}_aqua_modl_aod_target.pkl")
    
    transformed_features.to_pickle(f"data/{PREFIX}_aqua_transformed_features.pkl")
    transformed_features_lambdas.to_pickle(f"data/{PREFIX}_aqua_transformed_features_lambdas.pkl")  
    transformed_targets.to_pickle(f"data/{PREFIX}_aqua_transformed_targets.pkl")
    transformed_targets_lambdas.to_pickle(f"data/{PREFIX}_aqua_transformed_targets_lambdas.pkl")  
    transformed_modl_targets.to_pickle(f"data/{PREFIX}_aqua_transformed_modl_targets.pkl")
    transformed_modl_targets_lambdas.to_pickle(f"data/{PREFIX}_aqua_transformed_modl_targets_lambdas.pkl")

if __name__ == '__main__':
    generate_transformed_land_data()
1

