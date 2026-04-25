from enum import Enum

from pydantic import BaseModel


class Season(str, Enum):
    SPRING = "spring"
    SUMMER = "summer"
    FALL = "fall"
    WINTER = "winter"
    ALL_SEASON = "all_season"
    UNDEFINED = "undefined"


class Occasion(str, Enum):
    CASUAL = "casual"
    WORK = "work"
    FORMAL = "formal"
    PARTY = "party"
    SPORT = "sport"
    OUTDOOR = "outdoor"
    UNDEFINED = "undefined"


class ScoringWeights(BaseModel):
    w_visual: float
    w_tag: float
    w_recency: float

    def __post_init__(self):
        for name, value in (
                ("w_visual", self.w_visual),
                ("w_tag", self.w_tag),
                ("w_recency", self.w_recency),
        ):
            if value < 0:
                raise ValueError(f'{name} cannot be negative')


class Color(BaseModel):
    hex: str

    def __post_init__(self):
        if not self.hex.startswith("#") or len(self.hex) != 7:
            raise ValueError(f'Invalid hex color: {self.hex}')

    @property
    def as_rgb(self) -> tuple[int, int, int]:
        return (
            int(self.hex[1:3], 16),
            int(self.hex[3:5], 16),
            int(self.hex[5:7], 16),

        )


class Category(str, Enum):
    TOP = "top"
    BOTTOM = "bottom"
    SHOES = "shoes"
    OUTERWEAR = "outerwear"
    ACCESSORY = "accessory"


class Style(str, Enum):
    CASUAL = "casual"
    FORMAL = "formal"
    SPORT = "sport"
    STREETWEAR = "streetwear"
    UNDEFINED = "undefined"
