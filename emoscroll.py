from utils import *
from swbkarchive import Media, Diary, SwbkArchive
from swbkenum import Mood, MediaType
from esmenum import Emotion

import os
import time
import shutil

emo2mood = {
    Emotion.JOY: Mood.HAPPY,
    Emotion.THOUGHT: Mood.CONFUSED,
    Emotion.SADNESS: Mood.CRY,
    Emotion.WORRY: None,
    Emotion.SURPRISE: None,
    Emotion.FEAR: None,
    Emotion.ANGER: Mood.ANGRY,
}


def load_from_db(
    dbfile: str,
) -> tuple[list[dict], list[dict], dict[str, str], dict[str, str]]:
    data = export_all_tables(db_path=dbfile)
    return (
        data.get("Emo", []),
        data.get("Image", []),
        {i["songId"]: i for i in data.get("Song", [])},
        {i["emoId"]: i["songId"] for i in data.get("EmoSongCrossRef", [])},
    )


def convert(esmfile: str, save_as: str):
    tmpfolder = "./emotmp/"
    assert os.path.isfile(esmfile), "Not a file: " + esmfile
    if os.path.exists(tmpfolder):
        shutil.rmtree(tmpfolder)
    os.mkdir(tmpfolder)

    extract_zip(esmfile, tmpfolder)
    emos, imgs, songs, songref = load_from_db(os.path.join(tmpfolder, "app_database"))

    archive = SwbkArchive(time.time())
    for emo in emos:
        if emo["isRecycled"]:
            continue
        text = emo["content"].replace("\n", "  \n")
        d = Diary(time_=emo["createTime"] / 1000, uuid_=emo["emoId"])

        for img in filter(lambda item: item["emoId"] == emo["emoId"], imgs):
            imgfile = os.path.join(tmpfolder, "images", img["imageId"])
            ext = get_image_ext(imgfile)
            d.add_media(Media(content=imgfile, type_=MediaType.IMAGE, ext=ext))
            text += "\n\n![Image %d](appdata/Image/%s.%s)" % (
                img["order"],
                Media.md5_from_file(imgfile),
                ext,
            )

        if emo["emoId"] in songref:
            song = songs[songref[emo["emoId"]]]
            imgfile = os.path.join(tmpfolder, "songs", song["songId"])
            ext = get_image_ext(imgfile)
            d.add_media(Media(content=imgfile, type_=MediaType.IMAGE, ext=ext))
            text += """\n
> ![Cover](appdata/Image/%s.%s)  
> Title: %s  
> Artist: %s  """ % (
                Media.md5_from_file(imgfile),
                ext,
                song["title"],
                song["artist"],
            )

        d.content = text
        d.mood = emo2mood.get(Emotion(emo["emotion"]))
        archive.add_diary(d)

    archive.export_as_zipfile(save_as)


if __name__ == "__main__":
    convert(
        input("ESM File:").strip(),
        "./export_%d.zip" % (round(time.time())),
        #
    )
