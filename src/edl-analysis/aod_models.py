import os
from matplotlib import pyplot as plt
from matplotlib import cm, ticker
import numpy as np
import pandas as pd
import evidential_deep_learning as edl
import pickle
import tensorflow as tf
import scipy.stats   as stats
import scipy.special as special

"""
Plotting Functions
"""
X_BOUNDS = [0, 3]
Y_BOUNDS = [0, 3]

def plot_kde2d( x_bins, y_bins, P, x_bounds=X_BOUNDS, y_bounds=Y_BOUNDS, centroid=False, formatter=None,dpi=None,
                regression=None,Title=None,xLabel=None,yLabel=None):


    #   Plot results with 2 different colormaps
    #   ---------------------------------------
    fig = plt.figure(dpi=dpi)
    ax = fig.add_axes([0.1,0.1,0.75,0.75])
    if formatter != None:
        ax.xaxis.set_major_formatter(formatter)
        ax.yaxis.set_major_formatter(formatter)
    plt.imshow(P, cmap=cm.gist_earth_r, origin='lower', 
           extent=(x_bounds[0],x_bounds[-1],y_bounds[0],y_bounds[-1]) )
    plt.grid()
    plt.plot([x_bins[0],x_bins[-1]],[y_bins[0],y_bins[-1]],'k')
    if Title != None:
        plt.title(Title)
    if xLabel != None:
        plt.xlabel(xLabel)
    if yLabel != None:
        plt.ylabel(yLabel)

    # Regression
    # ----------
    if regression!=None:
        plot_linregress(regression[0],regression[1],x_bins)

    # Centroid
    # --------
    if centroid:
        X, Y = plt.meshgrid(x_bins,y_bins) # each has shape (Ny,Nx)
        y_c = sum(P*Y,axis=0)/sum(P,axis=0)
        plt.plot(x_bins,y_c,'r',label='Centroid')

    # Tighter colorbar
    # ----------------
    plt.draw()
    bbox = ax.get_position()
    l,b,w,h = bbox.bounds # mpl >= 0.98
    cax = plt.axes([l+w+0.02, b, 0.04, h]) # setup colorbar axes.
    plt.colorbar(cax=cax) # draw colorbar

#---
def plot_linregress(x_values,y_values,x_bins,label=None):
    slope, intercept, r, prob, see = stats.linregress(x_values,y_values)
    print(slope, intercept, r, prob, see)
    yy = slope * x_bins + intercept
    plt.plot(x_bins,slope * x_bins + intercept,'k',label='Regression')
    if label is None:
        label = "Regression Actual vs Model values"
    plt.plot(x_values,y_values,'ro',label=label,alpha=0.5, markersize=1)
    plt.legend(loc='upper left')
    return r

def plot_linregress_diff(x_values,y_values,x_bins,label=None):
    slope, intercept, r, prob, see = stats.linregress(x_values,y_values)
    print(slope, intercept, r, prob, see)
    yy = slope * x_bins + intercept
    plt.plot(x_bins, np.zeros(len(x_bins)),'k',label='AOD Ground Truth')
    print(y_values)
    if label is None:
        label = "Model - Ground Truth"
    plt.title('Model - Ground Truth Estimations')
    plt.plot(x_values,y_values - x_values,'ro',label=label,alpha=0.5, markersize=1)
    plt.legend(loc='upper left')
    return r

"""
Deep Learning Model Functions
"""
def nBoxCox(x):
    """
    Returns normalized (z-scores) BoxCox transform.
    """
    (x_,p_)=stats.boxcox(x)
    p = (p_, x_.mean(), x_.std() )
    x_ = (x_-p[1]) / p[2]
    
    return (x_,p)
    
def inv_nBoxCox(x,p):
    """
    Inverse normalized (z-scores) BoxCox transform.
    """
    x_ = p[1] + p[2] * x 
    x_ = special.inv_boxcox(x_,p[0])
    return x_

def get_permuted_partitions_pd(df, train_split=0.8, val_split=0.1, test_split=0.1):
    perm_len = df.shape[0]
    np.random.seed(0)
    perm = np.random.permutation(perm_len)
    
    assert (train_split + test_split + val_split) == 1
    
    # Only allows for equal validation and test splits
    assert val_split == test_split 

    # Specify seed to always have the same split distribution between runs
    df_sample = df.sample(frac=1, random_state=12)
    indices_or_sections = [int(train_split * len(df)), int((1 - test_split) * len(df))]
    
    train_indices, val_indices, test_indices = np.split(perm, indices_or_sections)
    
    return train_indices, val_indices, test_indices

def generate_relu_mlp_model(number_of_units_per_layer, output_dim):
    num_layers = len(number_of_units_per_layer)
    dense_layers = [tf.keras.layers.Dense(number_of_units_per_layer[i], activation="relu") for i in range(num_layers)]
    model = tf.keras.Sequential(dense_layers + [tf.keras.layers.Dense(output_dim)])
    return model

def generate_relu_edl_model(number_of_units_per_layer, output_dim):
    num_layers = len(number_of_units_per_layer)
    dense_layers = [tf.keras.layers.Dense(number_of_units_per_layer[i], activation="relu") for i in range(num_layers)]
    model = tf.keras.Sequential(dense_layers + [edl.layers.DenseNormalGamma(output_dim)])
    return model

def run_mlp_model(x_train, y_train, x_test, y_test, output_dim, columns, batch_size=100, epochs=2000):
    model = generate_relu_mlp_model([16, 12, 8], output_dim)
    model.compile(
            optimizer=tf.keras.optimizers.Adam(5e-4),
            loss=tf.keras.losses.MeanSquaredError())
    model.fit(x_train, y_train, batch_size=batch_size, epochs=epochs)
    print("Evaluating MLP Model...")
    model.evaluate(x_test, y_test)
    out = model.predict(x_test)
    out_df = pd.DataFrame(out, columns = columns)
    return out_df

def run_edl_model(x_train, y_train, x_test, y_test, output_dim, columns, edl_param, batch_size=100, epochs=2000):
    model = generate_relu_edl_model([16, 12, 8], output_dim)
    
    def EvidentialRegressionLoss(true, pred):
        return edl.losses.EvidentialRegression(true, pred, coeff=edl_param)

    model.compile(
        optimizer=tf.keras.optimizers.Adam(5e-4),
        loss=EvidentialRegressionLoss)
    model.fit(x_train, y_train, batch_size=batch_size, epochs=epochs)
    print("Evaluating EDL Model...")
    model.evaluate(x_test, y_test)
    out = model.predict(x_test)
    return out

def run_all_models(transformed_features, transformed_target, output_dir, satellite, edl_param=0.1):
    train_indices, val_indices, test_indices = get_permuted_partitions_pd(transformed_features)
    x_train = transformed_features.iloc[train_indices]
    y_train = transformed_target.iloc[train_indices]
    x_test = transformed_features.iloc[test_indices]
    y_test = transformed_target.iloc[test_indices]
    output_dim = transformed_target.shape[1]
    columns = transformed_target.columns

    with open(os.path.join(output_dir, f'{satellite}_test_indices.pkl'), 'wb') as f:
        pickle.dump(test_indices, f)

    with open(os.path.join(output_dir, f'{satellite}_y_test.pkl'), 'wb') as f:
        pickle.dump(y_test, f)

    import ipdb; ipdb.set_trace()
    # print("Training MLP Model...")
    # mlp_out = run_mlp_model(x_train, y_train, x_test, y_test, output_dim, columns)
    # with open(os.path.join(output_dir, f'{satellite}_mlp_out.pkl'), 'wb') as f:
    #     pickle.dump(mlp_out, f)

    # print("Training EDL Model...")
    # edl_out = run_edl_model(x_train, y_train, x_test, y_test, output_dim, columns, edl_param)
    # with open(os.path.join(output_dir, f'{satellite}_edl_out_edl_param={edl_param}.npy'), 'wb') as f:
    #     np.save(f, edl_out)
        