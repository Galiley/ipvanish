#!/usr/bin/env python3

import zipfile
import requests
import io
import os
import shutil
import tempfile

from ipvanish.settings import (
    CONFIG_PATH, CONFIG_URL
)

def update_config():
    with tempfile.TemporaryDirectory() as tmpfolder:
        try:
            r = requests.get(CONFIG_URL, stream=True)
            r.raise_for_status()
            z = zipfile.ZipFile(io.BytesIO(r.content))
            z.extractall(tmpfolder)
            print(tmpfolder)
            tmp_config_content = os.listdir(tmpfolder)
            print(tmp_config_content)
            if len(tmp_config_content) == 0:
                raise Exception("Failed to extract the config archive")
            else:
                for file in os.listdir(CONFIG_PATH):
                    os.remove(os.path.join(CONFIG_PATH,file))
                print(os.listdir(CONFIG_PATH))
                for file in tmp_config_content:
                    shutil.copyfile(
                        os.path.join(tmpfolder, file),
                        os.path.join(CONFIG_PATH, file)
                    )
            return True
        except Exception as e:
            print(e)
            return False