import requests
from bs4 import BeautifulSoup
from usp_cs_courses.settings import (
    BASE_URL,
    CS_COURSE_RELATIVE_URL,
    ASSETS_CONFIG_DIR,
    ASSETS_CONFIG_FILENAME,
)
from pathlib import Path
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logging.Formatter.formatTime = (
    lambda self, record, datefmt=None: datetime.fromtimestamp(
        record.created, timezone.utc
    )
    .astimezone()
    .isoformat(sep="T", timespec="milliseconds")
)


class DisciplineMetadataConfig:
    """Some useful discipline metadata are in certain tags that immediately follows a
    'b' tag with a specific word.
    """

    def __init__(self, b_tag_word: str, next_tag_type: str):
        self.b_tag_word = b_tag_word
        self.next_tag_type = next_tag_type

    def get_content(
        self,
        discipline_soup: BeautifulSoup,
        class_filter: str = "",
    ) -> str:
        """Gets the metadata content from a given discipline soup.

        The class_filter param allows to specify a class filter if needed.
        """
        content_tag = discipline_soup.find(
            lambda tag: tag.string.strip() == self.b_tag_word if tag.string else False
        )
        class_filter_dict = {"class_": class_filter} if class_filter else {}
        return content_tag.find_next(self.next_tag_type, **class_filter_dict).get_text(
            strip=True, separator="\n"
        )


def _get_soup(url: str) -> BeautifulSoup:
    r = requests.get(url)
    encoding = (
        r.encoding if "charset" in r.headers.get("content-type", "").lower() else None
    )
    parser = "html.parser"  # or lxml or html5lib
    return BeautifulSoup(r.content, parser, from_encoding=encoding)


def _get_discipline_name(discipline_soup: BeautifulSoup) -> str:
    """Discipline names in English are found in "span" tags folowing a 'b' tag of the form:

    "Disciplina: [discipline code] - [discipline name]"
    """
    discipline_tag = discipline_soup.find(
        lambda tag: (
            tag.name == "b" and tag.string.startswith("Disciplina")
            if tag.string
            else False
        )
    )
    return discipline_tag.find_next("span").get_text(strip=True)


def main(
    base_url: str = BASE_URL,
    course_relative_url: str = CS_COURSE_RELATIVE_URL,
    config_path: Path = ASSETS_CONFIG_DIR.joinpath(ASSETS_CONFIG_FILENAME),
) -> None:
    """Gets the latest content from the course url, parses it, and
    stores the resulting assets config to local storage.

    :param base_url: The base url for accessing USP courses.
    :param course_relative_url: The relative url for the CS course.
    :param config_path: The path to persist the resulting assets config file.
    """
    assets_config = {}
    course_url = base_url + course_relative_url
    logger.info(f"Getting course info from {course_url} ...")
    courses_soup = _get_soup(course_url)
    discipline_tags = courses_soup.find_all("a", class_="link_gray")
    disciplines_found = len(discipline_tags)
    logger.info(f"Found {disciplines_found} disciplines.")
    for count, tag in enumerate(discipline_tags, start=1):
        discipline_url = base_url + tag["href"]
        discipline_code = tag.string[-7:]
        logger.info(
            f"Retrieving info on discipline {discipline_code} from {discipline_url}..."
        )
        discipline_soup = _get_soup(discipline_url)
        discipline_name = _get_discipline_name(discipline_soup)
        bibliography_config = DisciplineMetadataConfig("Bibliografia", "pre")
        description_config = DisciplineMetadataConfig("Objetivos", "i")
        program_config = DisciplineMetadataConfig("Programa", "i")
        assets_config.update(
            {
                discipline_code: {
                    "name": discipline_name,
                    "url": discipline_url,
                    "deps": [],
                    "bibliography": bibliography_config.get_content(discipline_soup),
                    "description": description_config.get_content(discipline_soup),
                    "program": program_config.get_content(discipline_soup),
                }
            }
        )
        logger.info(
            f"Successfully processed {count}/{disciplines_found} discipline infos."
        )
    logger.info("Parsing discipline dependencies info...")
    dependency_tags = courses_soup.find_all("span", class_="txt_arial_8pt_red")
    for tag in dependency_tags:
        child_tag = tag.find_previous("a", class_="link_gray")
        child_code = child_tag.string[-7:]
        deps_code = tag.string.strip()[:7]
        assets_config[child_code]["deps"].append(deps_code)
    logger.info(f"Persisting assets configuration into {config_path.as_posix()}...")
    with open(config_path, "w+") as fp:
        json.dump(assets_config, fp, ensure_ascii=False, indent=4)
