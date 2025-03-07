# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/15
# 
# ====================
from pathlib import Path

from sqlmodel import SQLModel

import sys

sys.path.append(str(Path(__file__).absolute().parent.parent))

from service.db import engine, session
from service.model import * # noqa


def create_db_tables():

    SQLModel.metadata.create_all(engine)



if __name__ == "__main__":
    create_db_tables()

    # name = Name(id=1, user_id=2, session_id=2, name="刘宇宸")
    #
    # with session() as sess:
    #     sess.add(name)
    #     sess.commit()
