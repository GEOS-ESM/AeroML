import pandas as pd
import pickle
import sys
sys.path.append('..')
from aod_models import nBoxCox



def transform_data(features, target, modis_target,
                   epsilon_target = 1e-2,
                   modis_epsilon_target = 1e-2,
                   sim=False):
    
    features_box_cox_transformed = features.copy()
    if sim:
            features_lambda_box_coxes = pd.DataFrame(columns=['lam_box_cox'], index=[c for c in features.columns if c[:3] == "Ref"])
    else:
        features_lambda_box_coxes = pd.DataFrame(columns=['lam_box_cox'], index=[c for c in features.columns if c[:4] == "mRef"])
    for a in features_lambda_box_coxes.index:
        features_box_cox_transformed[a], lambda_box_cox = nBoxCox(features[a])
        features_lambda_box_coxes['lam_box_cox'][a] = lambda_box_cox

    target_box_cox_transformed = target.copy()
    target_lambda_box_coxes = pd.DataFrame(columns=['lam_box_cox'], index=target_box_cox_transformed.columns)
    for a in target_box_cox_transformed.columns:
        target_data = target_box_cox_transformed[a]
        if target_data.min() <= 0:
            target_data += epsilon_target
        target_box_cox_transformed[a], lambda_box_cox = nBoxCox(target_data)
        target_lambda_box_coxes['lam_box_cox'][a] = lambda_box_cox
    
    modis_target_box_cox_transformed = modis_target.copy()
    modis_target_lambda_box_coxes = pd.DataFrame(columns=['lam_box_cox'], index=modis_target_box_cox_transformed.columns)
    for a in modis_target_box_cox_transformed.columns:
        target_data = modis_target_box_cox_transformed[a]
        if target_data.min() <= 0:
            target_data += modis_epsilon_target
        modis_target_box_cox_transformed[a], lambda_box_cox = nBoxCox(target_data)
        modis_target_lambda_box_coxes['lam_box_cox'][a] = lambda_box_cox

    return features_box_cox_transformed, features_lambda_box_coxes, target_box_cox_transformed, target_lambda_box_coxes, modis_target_box_cox_transformed, modis_target_lambda_box_coxes
