from dagster import (
    external_assets_from_specs,
    AssetSpec,
    MetadataValue,
    ExperimentalWarning,
)
import json
from .settings import ASSETS_CONFIG_DIR, ASSETS_CONFIG_FILENAME
from unidecode import unidecode_expect_ascii
import re
import warnings

warnings.filterwarnings("ignore", category=ExperimentalWarning)

with open(ASSETS_CONFIG_DIR.joinpath(ASSETS_CONFIG_FILENAME)) as fp:
    usp_assets_config: dict = json.load(fp)


def _make_dagster_name(name: str, max_length: int = 63) -> str:
    """Generates a valid Dagster name from a bare name.

    Conditions for a valid Dagster name:
        Allowed characters: alpha-numeric, '_', '-', '.'.
        Must have <= 63 characters.
    """
    if len(name) > max_length:
        name = name[:max_length]
    ascii_name = unidecode_expect_ascii(name.strip(), errors="replace", replace_str="_")
    return re.sub(r"[^a-zA-z0-9_.-]", "_", ascii_name)


cs_usp_assets = external_assets_from_specs(
    [
        AssetSpec(
            key=_make_dagster_name(config["name"]),
            deps=set(
                map(
                    lambda code: _make_dagster_name(
                        usp_assets_config.get(code, {}).get("name", "") or code
                    ),
                    config["deps"],
                )
            ),
            description=config["description"],
            metadata={
                "code": MetadataValue.text(code),
                "url": MetadataValue.url(config["url"]),
                "program": MetadataValue.md(config["program"]),
                "bibliography": MetadataValue.md(config["bibliography"]),
            },
        )
        for code, config in usp_assets_config.items()
    ]
)
