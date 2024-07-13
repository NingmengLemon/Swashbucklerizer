import os
import json
import time
from typing import Optional
import uuid
import shutil
import hashlib

from utils import (
    md5_from_io,
    timestamp_to_iso8601_no_timezone,
    open_unique,
    walk_compress,
    timestamp_to_iso8601,
)
from swbkenum import MediaType, Mood


class Media:
    def __init__(
        self,
        content: bytes | str,
        type_: MediaType = MediaType.UNKNOWN,
        ext: Optional[str] = None,
    ) -> None:
        self.type: MediaType = type_
        self.content: bytes | str = content
        self.extension: str = "unknown"
        if ext:
            self.extension = ext
        elif isinstance(content, str) and not ext:
            _, ext = os.path.splitext(content)
            if len(ext) > 1:
                self.extension = ext[1:]

    @staticmethod
    def md5_from_file(path):
        assert os.path.isfile(path), "Not a file: " + path
        with open(path, "rb") as file:
            md5 = md5_from_io(file)
        return md5

    @property
    def filename(self):
        if isinstance(self.content, str):
            return self.md5_from_file(self.content) + "." + self.extension
        elif isinstance(self.content, bytes):
            return hashlib.md5(self.content).hexdigest() + "." + self.extension
        else:
            raise TypeError("invalid content type: " + str(type(self.content)))


class Diary:
    def __init__(
        self,
        time_: Optional[float] = None,
        uuid_: Optional[str] = None,
        content: Optional[str] = None,
    ) -> None:
        self.time = time_ if time_ else time.time()
        self.uuid = uuid_ if uuid_ else str(uuid.uuid4())
        self.content: str = content if content else ""
        self.medias: list[Media] = []
        self.mood: Mood | None = None

    def add_media(self, media: Media):
        self.medias += [media]

    def __len__(self):
        return len(self.content)

    @property
    def media_count(self):
        return len(self.medias)


class SwbkArchive:
    def __init__(self, time_: Optional[float] = None) -> None:
        self.time = time_ if time_ else time.time()
        self.diaries: list[Diary] = []

    def add_diary(self, diary: Diary):
        self.diaries += [diary]

    def export_as_folder(self, path: str):
        if not os.path.exists(path):
            os.mkdir(path)
        assert not os.listdir(path), "Folder to export is not empty"

        with open(os.path.join(path, "version.json"), "w+", encoding="utf-8") as vfile:
            json.dump(self.version, vfile, ensure_ascii=False, indent=2)
        os.mkdir(os.path.join(path, "appdata"))
        os.mkdir(os.path.join(path, "appdata", "Audio"))
        os.mkdir(os.path.join(path, "appdata", "Video"))
        os.mkdir(os.path.join(path, "appdata", "Image"))
        for diary in self.diaries:
            resources = []
            for media in diary.medias:
                fname = media.filename
                type_ = {
                    MediaType.UNKNOWN: "Unknown",
                    MediaType.AUDIO: "Audio",
                    MediaType.IMAGE: "Image",
                    MediaType.VIDEO: "Video",
                }.get(media.type, "Unknown")
                fpath = os.path.join(path, "appdata", type_, fname)
                if not type_:
                    continue
                if isinstance(media.content, bytes):
                    with open(fpath, "wb") as f:
                        f.write(media.content)
                elif isinstance(media.content, str):
                    if not os.path.exists(media.content):
                        continue
                    if os.path.exists(fpath):
                        continue
                    shutil.copy(media.content, fpath)
                resources.append(
                    {
                        "ResourceUri": f"appdata/{type_}/{fname}",
                        "ResourceType": media.type.value,
                    }
                )
            diary_data = {
                "Title": None,
                "Content": diary.content,
                "Mood": diary.mood.value if diary.mood else None,
                "Weather": None,
                "Location": None,
                "Top": False,
                "Private": False,
                "Tags": [],
                "Resources": resources,
                "Id": diary.uuid,
                "CreateTime": timestamp_to_iso8601_no_timezone(diary.time),
                "UpdateTime": timestamp_to_iso8601_no_timezone(diary.time),
            }
            with open_unique(
                os.path.join(
                    path,
                    time.strftime("%Y-%m-%d", time.localtime(diary.time)) + ".json",
                ),
                mode="w+",
                encoding="utf-8",
            ) as f:
                json.dump(diary_data, f, ensure_ascii=False, indent=2)

    def export_as_zipfile(self, file: str, rm_tmp_dir=False):
        tmpdir = "./tmp/"
        assert not os.path.exists(file), "File already exists"
        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)
        os.mkdir(tmpdir)
        self.export_as_folder(tmpdir)
        walk_compress(tmpdir, file)
        if rm_tmp_dir:
            shutil.rmtree(tmpdir)

    @property
    def version(self):
        return {
            "Version": "0.91.6",
            "FileSuffix": ".json",
            "Platform": "Android",
            # "DateTime": "2024-06-23T10:35:55.741136+08:00",
            "DateTime": timestamp_to_iso8601(self.time),
        }


def test():
    archive = SwbkArchive()
    for i in range(10):
        d = Diary(content=str(i))
        d.add_media(Media("./tests/test.jpg", MediaType.IMAGE))
        d.add_media(Media("./tests/test.mp4", MediaType.VIDEO))
        d.add_media(Media("./tests/test.m4a", MediaType.AUDIO))
        archive.add_diary(d)
        # 注意，添加媒体之后要在日记内容中添加引用才能在日记中显示出来
        # 路径为 appdata/(类型)/(文件md5).(文件后缀)
    archive.export_as_zipfile(f"./test_{round(time.time())}.zip")


if __name__ == "__main__":
    test()
