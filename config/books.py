# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/3/22
#
#  古籍 TXT 版本 https://github.com/tanpero/Reservator
# ====================
from pathlib import Path
import random
from typing import List
import re


class Book(dict):
    def __init__(self, name: str):
        self.name: str = name
        super().__init__()

    def _read_txt(self):
        path = str(Path(__file__).absolute().parent.parent / f"files/{self.name}.txt")
        with open(path, "r") as rf:
            lines = [l.strip() for l in rf.readlines() if l.strip()]
        return lines

    def random(self, n: int = 50, **kwargs):
        return random.sample([p for v, article in self.items() for p in article], n)


class Volume(list):

    def __init__(self, name: str = None, author: str = None, articles: List["Article"] = None):
        self.name = name
        self.author = author
        super().__init__(*(articles or []))


class Article(list):

    def __init__(self, title: str = None, author: str = None, content: List[str] = None):
        self.title = title
        self.author = author
        super().__init__(*(content or []))


class _TangPoetryCollection(Book):
    """全唐诗"""

    def __init__(self):
        super().__init__(name="全唐诗")
        lines = self._read_txt()
        self._parser(lines)
        self.volume_names = [vol for vol, _ in self.items()]

    def _parser(self, lines):
        current_vol = None
        poetry = None
        for line in lines:
            if not line:
                continue

            # 1. 新的一卷开始
            if match := re.match(r"第(.*)卷(.*)", line):
                if poetry:
                    self[current_vol].append(poetry)
                    poetry = None
                current_vol = f"第{match.group(1)}卷"
                self[current_vol] = Volume(name=current_vol, author=match.group(2))
            # 新开始一篇诗
            if match := re.match(r"◎(卷\.\d+)【(.*)】(.*)", line):
                if poetry:
                    self[current_vol].append(poetry)
                poetry = Article(
                    title=match.group(2),
                    author=match.group(3)
                )
            elif poetry is not None:
                poetry.append(line)

    def random(self, n: int = 50, **kwargs):
        choice_volumes = random.sample(self.volume_names[30: 800], n)
        return random.sample([p  for v, poetries in self.items() if v in choice_volumes for p in poetries], n)


class _TheSheKing(Book):
    """诗经"""
    def __init__(self):
        super().__init__(name="诗经")
        lines = self._read_txt()
        self._parser(lines)

    def _parser(self, lines):
        current_vol = None
        poetry = None
        for line in lines:
            if not line:
                continue

            # 1. 新的一卷开始
            if match := re.match(r"(\w+)·(\w+)", line):
                if poetry:
                    self[current_vol].append(poetry)
                    poetry = None
                current_vol = line
                self[current_vol] = Volume(name=current_vol, author="")
            # 新开始一篇诗，诗经的题目最长为 5
            if len(line) <= 5:
                if poetry:
                    self[current_vol].append(poetry)
                poetry = Article(title=f"{self.name}·{line}", author="")
            elif poetry is not None:
                poetry.append(line)


class _SongOfChu(Book):
    """楚辞"""

    def __init__(self):
        super().__init__(name="楚辞")
        lines = self._read_txt()
        self._parser(lines)

    def _parser(self, lines):
        current_vol = None
        poetry = None
        for line in lines:
            if not line:
                continue

            # 1. 新的一卷开始
            if match := re.match(r"##\s+(\w+)", line):
                if poetry:
                    self[current_vol].append(poetry)
                    poetry = None
                current_vol = match.group(1)
                self[current_vol] = Volume(name=current_vol, author="")
            elif match := re.match(r"\*(\w+)\*", line):
                self[current_vol].author = match.group(1)
            # 新开始一篇诗
            if match := re.match(r"###\s+(\w+)", line):
                if poetry:
                    self[current_vol].append(poetry)
                poetry = Article(
                    title=match.group(1), author=self[current_vol].author)
            elif poetry is not None:
                poetry.append(line)


TangPoetryCollection = _TangPoetryCollection()
TheSheKing = _TheSheKing()
SongOfChu = _SongOfChu()


class _Books(dict):

    def __init__(self):
        super().__init__(
            全唐诗=TangPoetryCollection,
            诗经=TheSheKing,
            楚辞=SongOfChu,
        )

    def random(self, n: int = 50, **kwargs):
        book: Book = random.sample(list(self.values()), 1)[0]
        n = 3 if book.name == "楚辞" else n
        return book.random(n)


Books = _Books()


if __name__ == "__main__":
    print(TangPoetryCollection.random(3))
    # print(TheSheKing)
    # print(SongOfChu)
