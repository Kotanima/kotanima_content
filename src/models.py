"""
Commonly used data structures
"""

from attr import attrs, attrib
from typing import Optional


@attrs
class RedditPost:
    title: str = attrib(default=None)
    sub_name: str = attrib(default=None)
    post_id: int = attrib(default=None)
    author: str = attrib(default=None)
    created_utc: int = attrib(default=None)
    url: str = attrib(default=None)
    phash: str = attrib(default=None)

    @classmethod
    def from_dict(cls, obj):
        return cls(**obj)

    @classmethod
    def from_downloader_db(cls, obj):
        return cls(
            title=obj.title,
            post_id=obj.post_id,
            author=obj.author,
            created_utc=obj.created_utc,
            url=obj.url,
            phash=obj.phash,
            sub_name=obj.sub_name,
        )

    def get_image_name(self) -> Optional[str]:
        if self.sub_name and self.post_id:
            return f"{self.sub_name}_{self.post_id}.jpg"
        return None


@attrs
class IdentifiedRedditPost(RedditPost):
    mal_id: int = attrib(default=None)
    is_downloaded: bool = attrib(default=None)
    source_link: str = attrib(default=None)
    visible_tags: list[str] = attrib(default=None)
    invisible_tags: list[str] = attrib(default=None)

    anime_name: str = attrib(default=None, init=False)
    character_name: str = attrib(default=None, init=False)

    def __attrs_post_init__(self):
        try:
            self.anime_name = self.visible_tags[0]
        except (IndexError, TypeError):
            pass

        try:
            self.character_name = self.visible_tags[1]
        except (IndexError, TypeError):
            pass

    @classmethod
    def from_metadata_db(cls, obj):
        return cls(
            title=obj.title,
            mal_id=obj.mal_id,
            post_id=obj.post_id,
            author=obj.author,
            phash=obj.phash,
            source_link=obj.source_link,
            visible_tags=obj.visible_tags,
            invisible_tags=obj.invisible_tags,
            sub_name=obj.sub_name,
        )
