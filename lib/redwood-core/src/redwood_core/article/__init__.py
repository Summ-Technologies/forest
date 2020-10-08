from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Tuple

from bs4 import BeautifulSoup, PageElement, ResultSet

from .source import SourceType


class TransformerFactory(object):
    def __init__(self, config: dict):
        self.config = config

    def get_transformer(self, source_type: SourceType) -> AbstractTransformer:
        default_transformer = GenericTransformer
        mapping = {
            SourceType.GENERIC: GenericTransformer,
            SourceType.SUBSTACK: SubstackTransformer,
        }
        return mapping.get(source_type, default_transformer)(self.config)


class AbstractTransformer(ABC):
    def __init__(self, config: dict):
        self.config = config

    def get_html_and_outline(self, html_content: str) -> Tuple[str, str]:
        """
        Given email html content returns transformed html and matching outline to save
        returns: [transformed_html, outline]
        """
        transformed_html = self.transform_html(html_content)
        outline = self.generate_outline(transformed_html)
        return transformed_html, outline

    @abstractmethod
    def transform_html(self, html_content: str):
        """
        Returns html with the proper div's tagged with whittle_outline
        """
        pass

    def generate_outline(self, transformed_html: str):
        outline = ""
        soup = BeautifulSoup(transformed_html, "html.parser")
        for header in soup.select(
            f".{self._class_name(1)}, .{self._class_name(2)}, .{self._class_name(3)}"
        ):
            _whittle_anchor_id, *rest = (
                list(
                    filter(
                        lambda _id: _id.startswith(f"{self._anchor_id('')}"),
                        header.get("id", "").split(),
                    )
                )
                + [""]
            )
            if self._class_name(1) in header.get("class", []):
                outline += self._create_outline_h1(
                    header.get_text(), _whittle_anchor_id
                )
            elif self._class_name(2) in header.get("class", []):
                outline += self._create_outline_h2(
                    header.get_text(), _whittle_anchor_id
                )
            elif self._class_name(3) in header.get("class", []):
                outline += self._create_outline_h3(
                    header.get_text(), _whittle_anchor_id
                )
        return outline

    def get_text(self, html_content: str) -> str:
        soup = BeautifulSoup(html_content, "html.parser")
        return soup.get_text(" ", strip=True)

    def _create_outline_h1(self, text: str, anchor_id: str):
        return f"##### [{text.strip()}](#{anchor_id})  \n\n"

    def _create_outline_h2(self, text: str, anchor_id: str):
        return f"[**{text.strip()}**](#{anchor_id})  \n\n"

    def _create_outline_h3(self, text: str, anchor_id: str):
        return f"- [**{text.strip()}**](#{anchor_id})  \n\n"

    def _anchor_id(self, name: str):
        html_id_prefix = "whittle_anchor_"
        return f"{html_id_prefix}{name}"

    def _class_name(self, _type: int):
        html_class_prefix = "whittle_outline_"
        return f"{html_class_prefix}{str(_type)}"


class GenericTransformer(AbstractTransformer):
    def transform_html(self, html_content: str):
        """Returns html string with custom whittle tags/ids/etc.

        Args:
            html_content (str): original html from gmail message
        """
        soup = BeautifulSoup(html_content, "html.parser")
        link_i = 0
        for header in soup.find_all(["h1", "h2", "h3"]):
            existing_class: list = header.get("class", [])
            existing_id: list = header.get("id", "").split()
            if header.name == "h1":
                header["class"] = existing_class + [f"{self._class_name(1)}"]
                header["id"] = existing_id + [f"{self._anchor_id(str(link_i))}"]
                link_i += 1
            elif header.name == "h2":
                header["class"] = existing_class + [f"{self._class_name(2)}"]
                header["id"] = existing_id + [f"{self._anchor_id(str(link_i))}"]
                link_i += 1
            elif header.name == "h3":
                header["class"] = existing_class + [f"{self._class_name(3)}"]
                header["id"] = existing_id + [f"{self._anchor_id(str(link_i))}"]
                link_i += 1
        return str(soup)


class SubstackTransformer(AbstractTransformer):
    def transform_html(self, html_content: str):
        soup = BeautifulSoup(html_content, "html.parser")
        link_i = 0
        for header in soup.find_all(["h1", "h2", "h3"]):
            existing_class: list = header.get("class", [])
            existing_id: list = header.get("id", "").split()
            if header.name == "h1":
                header["class"] = existing_class + [f"{self._class_name(1)}"]
                header["id"] = existing_id + [f"{self._anchor_id(str(link_i))}"]
                link_i += 1
            elif header.name == "h2":
                header["class"] = existing_class + [f"{self._class_name(2)}"]
                header["id"] = existing_id + [f"{self._anchor_id(str(link_i))}"]
                link_i += 1
            elif header.name == "h3":
                header["class"] = existing_class + [f"{self._class_name(3)}"]
                header["id"] = existing_id + [f"{self._anchor_id(str(link_i))}"]
                link_i += 1
        return str(soup)
