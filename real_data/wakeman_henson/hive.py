from sys import argv

if len(argv) != 2:
    print(f"Please pass the run id, e.g. python {argv[0]}.py 1")
    exit()
id = argv[1]

import os
from glob import glob

import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import pdist, squareform

from osl_dynamics import run_pipeline
from osl_dynamics.data import Data
from osl_dynamics.inference import tf_ops
from osl_dynamics.utils import plotting
from osl_dynamics.utils.misc import load

# GPU settings
tf_ops.gpu_growth()


# Helper functions
def load_data(data_dir, store_dir, use_tfrecord=True, buffer_size=2000, n_jobs=16):
    """Load the data."""

    data_paths = sorted(glob(f"{data_dir}/sub*_run*/sflip_parc-raw.fif"))
    training_data = Data(
        data_paths,
        sampling_frequency=250,
        picks="misc",
        reject_by_annotation="omit",
        use_tfrecord=use_tfrecord,
        buffer_size=buffer_size,
        n_jobs=n_jobs,
        store_dir=store_dir,
    )

    methods = {
        "tde_pca": {"n_embeddings": 15, "n_pca_components": 80},
        "standardize": {},
    }
    training_data.prepare(methods)
    return training_data


def plot_loss(data, output_dir):
    """Plot the training loss with epoch."""

    # Directories
    model_dir = f"{output_dir}/model"
    plot_dir = output_dir

    history = load(f"{model_dir}/history.pkl")
    plotting.plot_line(
        [range(1, len(history["loss"]) + 1)],
        [history["loss"]],
        x_label="Epoch",
        y_label="Loss",
        title="Training loss",
        filename=f"{plot_dir}/loss.png",
    )


def plot_embeddings(data, output_dir):
    """Plot the embeddings related plots."""

    # Directories
    inf_params_dir = f"{output_dir}/inf_params"
    plot_dir = f"{output_dir}/embeddings"
    os.makedirs(plot_dir, exist_ok=True)

    embeddings = load(f"{inf_params_dir}/embeddings.npy")
    embeddings -= np.mean(embeddings, axis=0, keepdims=True)
    embeddings /= np.std(embeddings, axis=0, keepdims=True)

    # Pairwise correlation between subject embeddings
    se_cosine = squareform(pdist(embeddings, metric="cosine"))
    fig, ax = plotting.plot_matrices(
        se_cosine,
        cmap="coolwarm",
    )
    ax[0][0].set_xticks(
        ticks=np.arange(0, 114, 6) + 3, labels=[f"{i + 1}" for i in range(19)]
    )
    ax[0][0].set_yticks(
        ticks=np.arange(0, 114, 6) + 3, labels=[f"{i + 1}" for i in range(19)]
    )
    fig.savefig(f"{plot_dir}/se_cos.png")
    plt.close(fig)


# Set directories
output_dir = f"results/hive/run{id}"
tmp_dir = f"tmp/hive/run{id}"
data_dir = "/well/woolrich/projects/wakeman_henson/spring23/src"

config = """
    train_hive:
        config_kwargs:
            n_states: 6
            learn_means: False
            learn_covariances: True
            embeddings_dim: 10
    multitaper_spectra:
        kwargs:
            frequency_range: [1, 45]
            n_jobs: 16
        nnmf_components: 2
    plot_loss: {}
    plot_embeddings: {}
    plot_alpha:
        kwargs: {n_samples: 2000}
    plot_group_nnmf_tde_hmm_networks:
        nnmf_file: spectra/nnmf_2.npy
        mask_file: MNI152_T1_8mm_brain.nii.gz
        parcellation_file: fmri_d100_parcellation_with_PCC_reduced_2mm_ss5mm_ds8mm.nii.gz
        power_save_kwargs:
            plot_kwargs: {views: [lateral]}
    plot_hmm_network_summary_stats:
        sns_kwargs:
            cut: 0
"""
training_data = load_data(data_dir, tmp_dir, n_jobs=16)
run_pipeline(
    config,
    output_dir=output_dir,
    data=training_data,
    extra_funcs=[plot_loss, plot_embeddings],
)
