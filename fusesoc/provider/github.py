# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os.path
import sys
import tarfile
import tempfile

from fusesoc.provider.provider import Provider
from fusesoc.utils import unobscure_token

logger = logging.getLogger(__name__)

if sys.version_info[0] >= 3:
    import urllib.request as urllib
    from urllib.error import URLError
else:
    import urllib

    from urllib2 import URLError

URL = "https://github.com/{user}/{repo}/archive/{version}.tar.gz"

class Github(Provider):
    def _checkout(self, local_dir):
        user = self.config.get("user")
        repo = self.config.get("repo")
        otoken = self.config.get("token")
        

        version = self.config.get("version", "master")

        # TODO : Sanitize URL
        url = URL.format(user=user, repo=repo, version=version)
        logger.info("Downloading {}/{} from github".format(user, repo))
        logger.info("URL: {}".format(url))

        # if authentication token is given use it
        if (otoken)  :
            token = unobscure_token(str.encode(otoken)).decode("utf-8")
            logger.info("Token: {}".format(token))

            r = urllib.Request(url)
            r.add_header('Authorization', ("token " + token))
            try:
                with urllib.urlopen(r) as resp:
                    fd, filename = tempfile.mkstemp()
                    try:
                        with os.fdopen(fd, 'wb') as out:
                            data = resp.read()
                            if data:
                                out.write(data)
                    except:
                        raise RuntimeError("Failed to write to '{}'".format(filename))
            except URLError as e:
                raise RuntimeError("Failed to download '{}'. '{}'".format(url, e.reason))
        else:
            try:
                (filename, headers) = urllib.urlretrieve(url)
            except URLError as e:
                raise RuntimeError("Failed to download '{}'. '{}'".format(url, e.reason))


        logger.info("filename: {}".format(filename))

        t = tarfile.open(filename)
        (cache_root, core) = os.path.split(local_dir)

        # Ugly hack to get the first part of the directory name of the extracted files
        tmp = t.getnames()[0]
        t.extractall(cache_root)
        os.rename(os.path.join(cache_root, tmp), os.path.join(cache_root, core))
