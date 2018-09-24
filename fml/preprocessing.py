from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import OneHotEncoder, StandardScaler, FunctionTransformer
from sklearn.pipeline import make_pipeline
from sklearn.compose import make_column_transformer
from sklearn.utils.validation import check_array, check_is_fitted
import pandas as pd
import numpy as np

def detect_types_dataframe(X, verbose=0):
    """
    recognized types:
    continuous
    categorical
    free string TODO
    dirty string / dirty category TODO
    date
    """
    # Todo: detect index / unique integers
    # todo: detect near constant features
    # TODO subsample large datsets? one level up?
    # TODO detect encoding missing values as strings /weird values
    n_samples, n_features = X.shape
    n_values = X.apply(lambda x: x.nunique())
    dtypes = X.dtypes
    kinds = dtypes.apply(lambda x: x.kind)
    floats = kinds == "f"
    integers = kinds == "i"
    objects = kinds == "O"
    dates = kinds == "M"
    other = - (floats | integers | objects | dates)
    # check if we can cast strings to float


    # using categories as integers is not that bad usually
    cont_integers = integers.copy()
    # using integers as categories only if low cardinality
    # FIXME hardcoded
    few_entries = n_values < max(42, n_samples / 10)
    cat_integers = few_entries & integers  
    cat_string = few_entries & objects

    res = pd.DataFrame(
        {'continuous': floats | cont_integers,
         'categorical': cat_integers | cat_string, 'date': dates})
    res = res.fillna(False)
    if verbose == 1:
        print("Detected feature types:")
        desc = "{} float, {} int, {} object, {} date, {} other".format(
            floats.sum(), integers.sum(), objects.sum(), dates.sum(), other.sum())
        print(desc)
        print("Interpreted as:")
        dropped = (res.sum(axis=1) == 0).sum()
        interp = "{} continuous, {} categorical, {} date, {} dropped".format(
            res.continuous.sum(), res.categorical.sum(), res.date.sum(), dropped    
        )
        print(interp)
    return res

def detect_types_ndarray(X):
    raise NotImplementedError


class SimplePreprocessor(BaseEstimator, TransformerMixin):
    """ An simple preprocessor

    Detects variable types, encodes everything as floats
    for use with sklearn.

    Applies one-hot encoding, missing value imputation and scaling.

    Attributes
    ----------
    
    """
    def __init__(self, verbose=0):
        self.verbose = verbose

    def fit(self, X, y=None):
        """A reference implementation of a fitting function for a transformer.

        Parameters
        ----------
        X : array-like or sparse matrix of shape = [n_samples, n_features]
            The training input samples.
        y : None
            There is no need of a target in a transformer, yet the pipeline API
            requires this parameter.

        Returns
        -------
        self : object
            Returns self.
        """
        if isinstance(X, pd.DataFrame):
            self.columns_ = X.columns
            self.dtypes_ = X.dtypes
            types = detect_types_dataframe(X, verbose=self.verbose)
        else:
            X = check_array(X)
            types = detect_types_ndarray(X)

        # go over variable blocks
        # check for missing values
        # scale etc
        pipe_categorical = OneHotEncoder()

        steps_continuous = [FunctionTransformer(lambda x: x.astype(np.float), validate=False),
                            StandardScaler()]
        if X.loc[:, types['continuous']].isnull().values.any():
            steps_continuous.insert(0, SimpleImputer(strategy='median'))
        pipe_continuous = make_pipeline(*steps_continuous)
        # construct column transformer
        column_types = []
        if types['continuous'].any():
            column_types.append((types['continuous'], pipe_continuous))
        if types['categorical'].any():
             column_types.append((types['categorical'], pipe_categorical))
        if not len(column_types):
            raise ValueError("No feature columns found")
        self.ct_ = make_column_transformer(*column_types)
        self.ct_.sparse_threshold = .1  # FIXME HACK

        self.ct_.fit(X)

        self.input_shape_ = X.shape
        self.types_ = types
        # Return the transformer
        return self

    def get_feature_names(self):
        return self.ct_.get_feature_names(self.columns_)

    def transform(self, X):
        """ A reference implementation of a transform function.

        Parameters
        ----------
        X : array-like of shape = [n_samples, n_features]
            The input samples.

        Returns
        -------
        X_transformed : array of int of shape = [n_samples, n_features]
            The array containing the element-wise square roots of the values
            in `X`
        """
        # Check is fit had been called
        check_is_fitted(self, ['ct_'])
        return self.ct_.transform(X)