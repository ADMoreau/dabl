import pytest
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.datasets import load_iris

from dabl.utils import data_df_from_bunch
from dabl.plot.utils import (find_pretty_grid,
                             plot_coefficients,
                             pairplot, joint_plot)


def test_find_pretty_grid():
    # test that the grid is big enough:
    rng = np.random.RandomState(0)
    for i in range(100):
        n_plots = rng.randint(1, 34)
        max_cols = rng.randint(1, 12)
        rows, cols = find_pretty_grid(n_plots=n_plots, max_cols=max_cols)
        assert rows * cols >= n_plots
        assert cols <= max_cols


@pytest.mark.parametrize("n_features, n_top_features",
                         [(5, 10), (10, 5), (10, 40), (40, 10)])
def test_plot_coefficients(n_features, n_top_features):
    coef = np.arange(n_features) + .4
    names = ["feature_{}".format(i) for i in range(n_features)]
    plot_coefficients(coef, names, n_top_features=n_top_features)
    ax = plt.gca()
    assert len(ax.get_xticks()) == min(n_top_features, n_features)
    coef[:-5] = 0
    plot_coefficients(coef, names, n_top_features=n_top_features)
    ax = plt.gca()
    assert len(ax.get_xticks()) == 5


def test_pairplot_iris():
    data = data_df_from_bunch(load_iris())
    axes = pairplot(data, target_col='target')
    # the diagonal axes are duplicated
    # so we can have sharex / sharey
    assert axes.shape == (4, 4)
    assert len(plt.gcf().get_axes()) == 4 * 4 + 4


def test_joint_plot():
    tips = sns.load_dataset("tips")
    joint_plot(tips, 'total_bill', 'tip', clip_outliers=True)
