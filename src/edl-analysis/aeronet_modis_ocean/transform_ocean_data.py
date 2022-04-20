import sys

import pandas as pd
sys.path.append('..')

from qc_c6 import QC_OCEAN
from data.box_cox_transform_data import transform_data

PREFIX = "OCEAN"

def generate_transformed_ocean_data():
    aqua  = '../data/giant_C6_10km_Aqua_20151005.nc'
    terra = '../data/giant_C6_10km_Terra_20150921.nc'

    # Ocean Model: Features
    Angles = ['SolarZenith','ScatteringAngle', 'GlintAngle'] # Satellite geometry

    Reflectances = [   'mRef470',
                    'mRef550',
                    'mRef660',
                    'mRef870',
                    'mRef1200',
                    'mRef1600',
                    'mRef2100'] # Satellite reflectance
    
    Surface = [   'CxAlbedo470',
                'CxAlbedo550',
                'CxAlbedo660',
                'CxAlbedo870',
                'CxAlbedo1200',
                'CxAlbedo1600',
                'CxAlbedo2100' ] # Derived from satellite as well
    
    Species = [ 'fdu','fcc','fsu']

    AirMassFactor = [ 'AMF']

    Features = Angles + Reflectances + Surface + Species + AirMassFactor

    modo_aod_ests = ['mTau470','mTau550','mTau660','mTau870']

    # Ocean Model: Targets (In-situ AERONET Measurements)
    Target = ['aTau470','aTau550','aTau660','aTau870']

    # Ingest Quality Controled Data
    Albedo = ['CxAlbedo'] # surface characteristics
    aFilter = Surface     # additional filters based on choice of surface

    """
    TERRA SATELLITE
    """

    modo_terra = QC_OCEAN(terra, Albedo=Albedo,verbose=True,aFilter=aFilter)
    modo_aod_target_terra = modo_terra.toDataFrame(Vars=modo_aod_ests)

    features_terra = modo_terra.toDataFrame(Vars=Features)
    features_terra[Reflectances].divide(features_terra['AMF'], axis='index')
    features_terra = features_terra[[a for a in features_terra.columns if a != 'AMF']]
    target_terra = modo_terra.toDataFrame(Vars=Target)
    modo_target_terra = modo_terra.toDataFrame(Vars=modo_aod_ests)
    
    transformed_features, transformed_features_lambdas, transformed_targets, transformed_targets_lambdas, transformed_modo_targets, transformed_modo_targets_lambdas = transform_data(features_terra, target_terra, modo_target_terra)

    modo_aod_target_terra.to_pickle(f"data/{PREFIX}_terra_modo_aod_target.pkl")

    transformed_features.to_pickle(f"data/{PREFIX}_terra_transformed_features.pkl")
    transformed_features_lambdas.to_pickle(f"data/{PREFIX}_terra_transformed_features_lambdas.pkl")  
    transformed_targets.to_pickle(f"data/{PREFIX}_terra_transformed_targets.pkl")
    transformed_targets_lambdas.to_pickle(f"data/{PREFIX}_terra_transformed_targets_lambdas.pkl")  
    transformed_modo_targets.to_pickle(f"data/{PREFIX}_terra_transformed_modo_targets.pkl")
    transformed_modo_targets_lambdas.to_pickle(f"data/{PREFIX}_terra_transformed_modo_targets_lambdas.pkl")

    """
    AQUA SATELLITE
    """

    modo_aqua  = QC_OCEAN(aqua, Albedo=Albedo,verbose=True,aFilter=aFilter)
    modo_aod_target_aqua = modo_aqua.toDataFrame(Vars=modo_aod_ests)

    features_aqua = modo_aqua.toDataFrame(Vars=Features)
    features_aqua[Reflectances].divide(features_aqua['AMF'], axis='index')
    features_aqua = features_aqua[[a for a in features_aqua.columns if a != 'AMF']]
    target_aqua = modo_aqua.toDataFrame(Vars=Target)
    modo_target_aqua = modo_aqua.toDataFrame(Vars=modo_aod_ests)

    transformed_features, transformed_features_lambdas, transformed_targets, transformed_targets_lambdas, transformed_modo_targets, transformed_modo_targets_lambdas = transform_data(features_aqua, target_aqua, modo_target_aqua)

    modo_aod_target_aqua.to_pickle(f"data/{PREFIX}_aqua_modo_aod_target.pkl")
    
    transformed_features.to_pickle(f"data/{PREFIX}_aqua_transformed_features.pkl")
    transformed_features_lambdas.to_pickle(f"data/{PREFIX}_aqua_transformed_features_lambdas.pkl")  
    transformed_targets.to_pickle(f"data/{PREFIX}_aqua_transformed_targets.pkl")
    transformed_targets_lambdas.to_pickle(f"data/{PREFIX}_aqua_transformed_targets_lambdas.pkl")  
    transformed_modo_targets.to_pickle(f"data/{PREFIX}_aqua_transformed_modo_targets.pkl")
    transformed_modo_targets_lambdas.to_pickle(f"data/{PREFIX}_aqua_transformed_modo_targets_lambdas.pkl")

if __name__ == '__main__':
    generate_transformed_ocean_data()


