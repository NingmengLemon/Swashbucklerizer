from enum import Enum

__all__ = ["MediaType", "Mood", "Weather"]


class MediaType(Enum):
    """
    侠客日记的代码:
    ```csharp
    namespace SwashbucklerDiary.Shared
    {
        public enum MediaResource
        {
            Unknown,
            Image,
            Audio,
            Video,
        }
    }
    ```
    """

    UNKNOWN = 0
    IMAGE = 1
    AUDIO = 2
    VIDEO = 3


class Mood(Enum):
    ANGRY = "angry"
    CONFUSED = "confused"
    COOL = "cool"
    CRY = "cry"
    DEAD = "dead"
    DEVIL = "devil"
    EXCITED = "excited"
    FROWN = "frown"
    HAPPY = "happy"
    KISS = "kiss"
    LOL = "lol"
    NEUTRAL = "neutral"
    POOP = "poop"
    SAD = "sad"
    SICK = "sick"
    TONGUE = "tongue"
    WINK = "wink"


class Weather(Enum):
    CLOUDY = "cloudy"
    DUST = "dust"
    FOG = "fog"
    HAIL = "hail"
    HAZY = "hazy"
    HURRICANE = "hurricane"
    LIGHTNING = "lightning"
    LIGHTNING_RAINY = "lightning-rainy"
    POURING = "pouring"
    RAINY = "rainy"
    SLEET = "sleet"
    SNOW = "snow"
    SUNNY = "sunny"
    SUNNY_OFF = "sunny-off"
    ULTRAVIOLET = "ultraviolet"
    TORNADO = "tornado"
    WINDY = "windy"
