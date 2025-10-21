DEFAULT_COL_DICT = {
    "name": None,
    "description": None,
    "constraints": None,
    "meta": None,
    "meta_tags": None,
    "data_type": None,
    "data_tests": None,
    "tags": None,
}


DEFAULT_MODEL_CONFIG = {
    "version": 2,
    "models": [
        {
            "name": None,
            "description": None,
            "enabled": True,
            "tags": None,
            "meta": None,
            "data_tests": None,
            "config": {
                "database": None,
                "schema": None,
                "tags": None,
                "meta": None,
                "materialized": "table",
                "contract": {
                    "enforced": False,
                },
            },
            "constraints": None,
            "pre_hook": None,
            "post_hook": None,
            "columns": [],
        }
    ],
}
