import os
from collections import defaultdict

import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import (
    davies_bouldin_score,
    silhouette_score,
    calinski_harabasz_score,
)
from scipy.spatial.distance import pdist, squareform

from osl_dynamics.utils import plotting
from osl_dynamics.utils.misc import load

base_dir = "results"
plot_dir = "figures"
os.makedirs(plot_dir, exist_ok=True)

clustering_scores = {
    "hmm": defaultdict(list),
    "hive": defaultdict(list),
}
subject_labels = np.repeat(np.arange(19), 6)
fe = {
    "hmm": [],
    "hive": [],
}

for model in ["hmm", "hive"]:
    model_dir = f"{base_dir}/{model}"
    n_runs = len(os.listdir(model_dir))
    for run in range(1, n_runs + 1):
        fe[model].append(load(f"{model_dir}/run{run}/model/history.pkl")["free_energy"])
        if model == "hive":
            covs = load(f"{model_dir}/run{run}/inf_params/covs.npy")
        else:
            covs = load(f"{model_dir}/run{run}/dual_estimates/covs.npy")

        covs_flatten = np.array([cov.flatten() for cov in covs])
        clustering_scores[model]["silhouette"].append(
            silhouette_score(covs_flatten, subject_labels)
        )
        clustering_scores[model]["davies_bouldin"].append(
            davies_bouldin_score(covs_flatten, subject_labels)
        )
        clustering_scores[model]["calinski_harabasz"].append(
            calinski_harabasz_score(covs_flatten, subject_labels)
        )

# plot results
plotting.plot_violin(
    np.array(
        [
            clustering_scores["hive"]["silhouette"],
            clustering_scores["hmm"]["silhouette"],
        ]
    ),
    ["HIVE", "HMM-DE"],
    title="Silhouette score",
    y_label="Score",
    sns_kwargs={"cut": 0, "scale": "width"},
    filename=f"{plot_dir}/silhouette_scores.png",
)

plotting.plot_violin(
    1
    - np.array(
        [
            clustering_scores["hive"]["davies_bouldin"],
            clustering_scores["hmm"]["davies_bouldin"],
        ]
    ),
    ["HIVE", "HMM-DE"],
    title="Negative Davies-Bouldin score",
    y_label="Score",
    sns_kwargs={"cut": 0, "scale": "width"},
    filename=f"{plot_dir}/davies_bouldin_scores.png",
)

plotting.plot_violin(
    np.array(
        [
            clustering_scores["hive"]["calinski_harabasz"],
            clustering_scores["hmm"]["calinski_harabasz"],
        ]
    ),
    ["HIVE", "HMM-DE"],
    title="Calinski-Harabasz score",
    y_label="Score",
    sns_kwargs={"cut": 0, "scale": "width"},
    filename=f"{plot_dir}/calinski_harabasz_scores.png",
)

# Get the best runs
best_hmm_run = np.argmin(fe["hmm"])
best_hive_run = np.argmin(fe["hive"])

best_hmm_covs = load(f"{base_dir}/hmm/run{best_hmm_run + 1}/dual_estimates/covs.npy")
best_hive_covs = load(f"{base_dir}/hive/run{best_hive_run + 1}/inf_params/covs.npy")

best_hmm_covs_flatten = np.array([cov.flatten() for cov in best_hmm_covs])
best_hive_covs_flatten = np.array([cov.flatten() for cov in best_hive_covs])

# Get the pairwise distances
hmm_pdist = squareform(pdist(best_hmm_covs_flatten, metric="euclidean"))
hive_pdist = squareform(pdist(best_hive_covs_flatten, metric="euclidean"))

fig, ax = plotting.plot_matrices(
    [
        hive_pdist,
        hmm_pdist,
    ],
    titles=["HIVE", "HMM-DE"],
    cmap="coolwarm",
)
ax[0][0].set_xticks(
    ticks=np.arange(0, 114, 6) + 3,
    labels=[f"{i + 1}" for i in range(19)],
    fontsize=6,
)
ax[0][0].set_yticks(
    ticks=np.arange(0, 114, 6) + 3,
    labels=[f"{i + 1}" for i in range(19)],
    fontsize=6,
)
plt.setp(ax[0][0].get_xticklabels(), rotation=45)
ax[0][1].set_xticks(
    ticks=np.arange(0, 114, 6) + 3,
    labels=[f"{i + 1}" for i in range(19)],
    fontsize=6,
)
ax[0][1].set_yticks(
    ticks=np.arange(0, 114, 6) + 3,
    labels=[f"{i + 1}" for i in range(19)],
    fontsize=6,
)
plt.setp(ax[0][1].get_xticklabels(), rotation=45)
fig.savefig(f"{plot_dir}/covs_pw.png", dpi=300)
plt.close(fig)
