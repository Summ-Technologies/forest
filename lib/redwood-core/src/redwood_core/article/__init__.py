from enum import Enum

from bs4 import BeautifulSoup, PageElement, ResultSet


def whittle_anchor_id(name: str):
    html_id_prefix = "whittle_anchor_"
    return f"{html_id_prefix}{name}"


def whittle_class_name(_type: int):
    html_class_prefix = "whittle_outline_"
    return f"{html_class_prefix}{str(_type)}"


class SourceType(Enum):
    GENERIC = "GENERIC"
    SUBSTACK = "SUBSTACK"


class ArticleUtils:
    @staticmethod
    def transform_html(html_content: str, source: SourceType):
        """Returns html string with custom whittle tags/ids/etc.

        Args:
            html_content (str): original html from gmail message
        """
        if source == SourceType.SUBSTACK:
            return SubtackUtils.transform_html(html_content)
        else:
            raise Exception(f"No handler for source: {source}")

    @staticmethod
    def generate_outline(html_content: str):
        outline = ""
        soup = BeautifulSoup(html_content, "html.parser")
        for header in soup.select(
            f".{whittle_class_name(1)}, .{whittle_class_name(2)}, .{whittle_class_name(3)}"
        ):
            _whittle_anchor_id, *rest = (
                list(
                    filter(
                        lambda _id: _id.startswith(f"{whittle_anchor_id('')}"),
                        header.get("id", "").split(),
                    )
                )
                + ["whittle"]
            )
            if whittle_class_name(1) in header.get("class", []):
                outline += f"##### [{header.get_text()}](#{_whittle_anchor_id})"
                outline += "  \n\n"
            elif header.name == "h2":
                outline += f"[**{header.get_text()}**](#{_whittle_anchor_id})"
                outline += "  \n\n"
            elif header.name == "h3":
                outline += f"- [**{header.get_text()}**](#{_whittle_anchor_id})"
                outline += "  \n\n"
        return outline


class SubtackUtils:
    @staticmethod
    def transform_html(html_content: str):
        soup = BeautifulSoup(html_content, "html.parser")
        link_i = 0
        for header in soup.find_all(["h1", "h2", "h3"]):
            existing_class: list = header.get("class", [])
            existing_id: list = header.get("id", "").split()
            if header.name == "h1":
                header["class"] = existing_class + [f"{whittle_class_name(1)}"]
                header["id"] = existing_id + [f"{whittle_anchor_id(str(link_i))}"]
                link_i += 1
            elif header.name == "h2":
                header["class"] = existing_class + [f"{whittle_class_name(2)}"]
                header["id"] = existing_id + [f"{whittle_anchor_id(str(link_i))}"]
                link_i += 1
            elif header.name == "h3":
                header["class"] = existing_class + [f"{whittle_class_name(3)}"]
                header["id"] = existing_id + [f"{whittle_anchor_id(str(link_i))}"]
                link_i += 1
        return str(soup)
