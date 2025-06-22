#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: mlops.py
# Description: Machine learning utility toolkit for training, evaluation, prediction, and dataset handling.
# Author: Ms. White
# Created: 2025-04-29
# Modified: 2025-05-01 20:22:20

import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import mean_squared_error, accuracy_score


def ml_dataset_split(path: str, test_size: float = 0.2, random_state: int = 42) -> dict:
    """
    Splits a CSV dataset into training and testing sets.

    Args:
        path (str): Path to the CSV file.
        test_size (float): Fraction of data to use as test set.
        random_state (int): Random seed for reproducibility.

    Returns:
        dict: Paths to the train and test CSVs.
    """
    df = pd.read_csv(path)
    train_df, test_df = train_test_split(df, test_size=test_size, random_state=random_state)
    train_path = path.replace(".csv", "_train.csv")
    test_path = path.replace(".csv", "_test.csv")
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
    return {"train": train_path, "test": test_path}


def ml_train_model(path: str, target_column: str, task_type: str = None) -> dict:
    """
    Trains a machine learning model (regression or classification) on a CSV dataset.

    Args:
        path (str): Path to the training CSV file.
        target_column (str): Column name to predict.
        task_type (str, optional): Override for task type: 'regression' or 'classification'.

    Returns:
        dict: { "status": ..., "model_path": ..., "task_type": ..., "features": [...], "error": ... (if any) }
    """
    try:
        df = pd.read_csv(path)

        if df.empty:
            return {"status": "error", "error": "Dataset is empty."}
        if target_column not in df.columns:
            return {
                "status": "error",
                "error": f"Target column '{target_column}' not found in dataset. Columns: {df.columns.tolist()}"
            }

        X = df.drop(columns=[target_column])
        y = df[target_column]

        if X.empty:
            return {"status": "error", "error": "No feature columns remain after dropping target column."}
        if y.isnull().any() or X.isnull().any().any():
            return {"status": "error", "error": "Missing values detected in dataset. Please clean the data."}

        if task_type not in {"classification", "regression", None}:
            return {"status": "error", "error": f"Invalid task_type '{task_type}'."}

        if task_type is None:
            if y.dtype.kind in 'if' and y.nunique() > 20:
                task_type = "regression"
            else:
                task_type = "classification"

        if task_type == "classification":
            model = LogisticRegression(max_iter=1000)
        else:
            model = LinearRegression()

        model.fit(X, y)

        model_path = path.replace(".csv", f"_{task_type}_model.joblib")
        joblib.dump({"model": model, "features": list(X.columns)}, model_path)

        return {
            "status": "success",
            "model_path": model_path,
            "task_type": task_type,
            "features": list(X.columns)
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}



def ml_evaluate_model(model_path: str, test_path: str, target_column: str) -> dict:
    """
    Evaluates a trained model using test data.

    Args:
        model_path (str): Path to the trained model bundle.
        test_path (str): Path to the test dataset.
        target_column (str): Column name used for evaluation.

    Returns:
        dict: Evaluation metric (MSE or accuracy).
    """
    bundle = _ml_load_model_bundle(model_path)
    model = bundle["model"]
    features = bundle["features"]

    df = pd.read_csv(test_path)
    X_test = df[features]
    y_test = df[target_column]
    y_pred = model.predict(X_test)

    if y_test.dtype.kind in 'if':
        return {"mse": mean_squared_error(y_test, y_pred)}
    else:
        return {"accuracy": accuracy_score(y_test, y_pred)}


def ml_predict(model_path: str, input_data: pd.DataFrame) -> list:
    """
    Uses a saved model to predict values for new input data.

    Args:
        model_path (str): Path to the joblib model bundle.
        input_data (pd.DataFrame): DataFrame of inputs to predict.

    Returns:
        list: List of predicted values.
    """
    bundle = _ml_load_model_bundle(model_path)
    model = bundle["model"]
    expected_features = bundle["features"]
    _ml_validate_input_schema(input_data, expected_features)
    return model.predict(input_data).tolist()


def _ml_validate_input_schema(input_df: pd.DataFrame, expected_columns: list[str]) -> None:
    """
    Validates that input data matches the model's expected columns.

    Args:
        input_df (pd.DataFrame): Input for prediction.
        expected_columns (list[str]): Required column names.

    Raises:
        ValueError: If input schema doesn't match expected.
    """
    if list(input_df.columns) != expected_columns:
        raise ValueError(
            f"Input columns do not match model expectations.\nExpected: {expected_columns}\nReceived: {list(input_df.columns)}"
        )


def _ml_load_model_bundle(path: str) -> dict:
    """
    Loads a model bundle with model and feature metadata.

    Args:
        path (str): Path to the joblib file.

    Returns:
        dict: Dictionary with 'model' and 'features'.
    """
    bundle = joblib.load(path)
    if not isinstance(bundle, dict) or "model" not in bundle or "features" not in bundle:
        raise ValueError("Invalid model bundle structure.")
    return bundle

