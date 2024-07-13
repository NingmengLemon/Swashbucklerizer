import os
import hashlib
import zipfile
import sqlite3
from typing import BinaryIO
from datetime import datetime, timezone, timedelta

from PIL import Image
import ffmpeg

__all__ = [
    "md5_from_io",
    "get_ext_ffmpeg",
    "get_image_ext",
    "open_unique",
    "timestamp_to_iso8601",
    "timestamp_to_iso8601_no_timezone",
    "walk_compress",
    "get_all_table_names",
    "export_to_list",
    "export_all_tables",
    "extract_zip",
]


def extract_zip(zip_path, extract_to):
    # 确保目标目录存在，不存在则创建
    if not os.path.exists(extract_to):
        os.makedirs(extract_to)

    # 打开 ZIP 文件并解压所有内容
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)


def get_all_table_names(database_path):
    # 连接到 SQLite 数据库
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # 查询所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    # 关闭连接
    cursor.close()
    conn.close()

    # 返回表名列表
    return [table[0] for table in tables]


def export_to_list(database_path, table_name):  # , json_file_path):
    # 连接到 SQLite 数据库
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # 查询数据
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    # 获取列名
    column_names = [description[0] for description in cursor.description]

    # 组合数据为字典列表
    data = [dict(zip(column_names, row)) for row in rows]

    # # 写入 JSON 文件
    # with open(json_file_path, 'w') as jsonfile:
    #     json.dump(data, jsonfile, indent=4)

    # 关闭连接
    cursor.close()
    conn.close()
    return data


def export_all_tables(db_path):
    return {i: export_to_list(db_path, i) for i in get_all_table_names(db_path)}


def walk_compress(path: str, save_as: str):
    with zipfile.ZipFile(save_as, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, path))


def md5_from_io(stream: BinaryIO, buffer_size=1024 * 1024):
    md5 = hashlib.md5()
    while chunk := stream.read(buffer_size):
        md5.update(chunk)
    stream.seek(0)
    return md5.hexdigest()


def get_image_ext(file_path):
    try:
        with Image.open(file_path) as img:
            return img.format.lower()
    except Exception:
        return None


def get_ext_ffmpeg(file_path):
    try:
        probe = ffmpeg.probe(file_path)
        return probe["format"]["format_name"].split(",")[0]
    except Exception:
        return None


def open_unique(file, **kwargs):
    if "encoding" not in kwargs:
        kwargs["encoding"] = "utf-8"
    directory, filename = os.path.split(file)
    if not directory:
        directory = "."
    base, extension = os.path.splitext(filename)
    unique_filename = filename
    counter = 1

    while os.path.exists(os.path.join(directory, unique_filename)):
        unique_filename = f"{base}({counter}){extension}"
        counter += 1

    unique_filepath = os.path.join(directory, unique_filename)

    return open(unique_filepath, **kwargs)


def timestamp_to_iso8601(timestamp: float | int):
    # 将时间戳转换为datetime对象
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    # 转换为目标时区，东八区（+08:00）
    target_timezone = timezone(timedelta(hours=8))
    dt = dt.astimezone(target_timezone)
    # 格式化为ISO 8601格式的字符串
    iso8601_str = dt.isoformat()
    return iso8601_str


def timestamp_to_iso8601_no_timezone(timestamp):
    # 将时间戳转换为datetime对象
    dt = datetime.fromtimestamp(timestamp)
    # 格式化为所需格式的字符串，不带时区信息
    iso8601_str = dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
    return iso8601_str
