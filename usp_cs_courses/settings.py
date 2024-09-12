from pathlib import Path

BASE_URL = "https://uspdigital.usp.br/jupiterweb/"

CS_COURSE_RELATIVE_URL = "listarGradeCurricular?codcg=55&codcur=55041&codhab=0&tipo=N"

ASSETS_CONFIG_DIR = Path(__file__).parents[1].joinpath("config")

ASSETS_CONFIG_FILENAME = "usp_assets_config.json"
