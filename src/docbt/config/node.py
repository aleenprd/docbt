import pandas as pd


def generate_column_info(df: pd.DataFrame) -> pd.DataFrame:
    """Generate a DataFrame with column information."""
    col_info = []
    for col in df.columns:
        col_info.append(
            {
                "Column": col,
                "Data Type": str(df[col].dtype),
                "Non-Null Count": df[col].count(),
                "Null Count": df[col].isnull().sum(),
                "Unique Values": (
                    df[col].nunique()
                    if df[col].dtype != "object" or df[col].nunique() < 100
                    else "100+"
                ),
            }
        )

    return pd.DataFrame(col_info)


def generate_number_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Display statistical summary for numeric columns."""
    numeric_cols = df.select_dtypes(include=["number"]).columns
    if len(numeric_cols) > 0:
        return df[numeric_cols].describe()
    else:
        return pd.DataFrame()


def generate_text_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Display statistics for text/object columns."""
    object_cols = df.select_dtypes(include=["object"]).columns
    if len(object_cols) > 0:
        obj_stats = []
        for col in object_cols:
            obj_stats.append(
                {
                    "Column": col,
                    "Unique Values": df[col].nunique(),
                    "Most Frequent": (df[col].mode().iloc[0] if len(df[col].mode()) > 0 else "N/A"),
                    "Frequency": (df[col].value_counts().iloc[0] if len(df[col]) > 0 else 0),
                }
            )
        obj_stats_df = pd.DataFrame(obj_stats)
        return obj_stats_df
    else:
        return pd.DataFrame()
