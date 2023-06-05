# -*- coding: utf-8 -*-
"""Tools to manage the container structure"""

import os
import sys
import subprocess
import logging

from udocker import LOG
from udocker.config import Config
from udocker.utils.fileutil import FileUtil
from udocker.utils.uprocess import Uprocess
from udocker.helper.unique import Unique
from udocker.helper.hostinfo import HostInfo


class ContainerStructure:
    """Docker container structure.
    Creation of a container filesystem from a repository image.
    Creation of a container filesystem from a layer tar file.
    Access to container metadata.
    """

    def __init__(self, localrepo, container_id=None):
        self.localrepo = localrepo
        self.container_id = container_id
        self.tag = ""
        self.imagerepo = ""

    def get_container_attr(self):
        """Get container directory and JSON metadata by id or name"""
        if Config.conf['location']:
            container_dir = ""
            cntjson = []
        else:
            container_dir = self.localrepo.cd_container(self.container_id)
            if not container_dir:
                LOG.error("container id or name not found")
                return(False, False)

            fjson = container_dir + "/container.json"
            cntjson = self.localrepo.load_json(fjson)
            if not cntjson:
                LOG.error("invalid container json metadata")
                return(False, False)

        return(container_dir, cntjson)

    def get_container_meta(self, param, default, cntjson):
        """Get the metadata configuration from the container"""
        cidx = ""
        if "config" in cntjson:
            cidx = "config"
        elif "container_config" in cntjson:
            cidx = "container_config"

        meta_item = None
        if cntjson[cidx] and param in cntjson[cidx]:
            meta_item = cntjson[cidx][param]
        elif param in cntjson:
            meta_item = cntjson[param]

        if meta_item is None:
            pass
        elif (isinstance(meta_item, str) and (isinstance(default, (list, tuple)))):
            return meta_item.strip().split()
        elif (isinstance(default, str) and (isinstance(meta_item, (list, tuple)))):
            return " ".join(meta_item)
        elif (isinstance(default, str) and (isinstance(meta_item, dict))):
            return self._dict_to_str(meta_item)
        elif (isinstance(default, list) and (isinstance(meta_item, dict))):
            return self._dict_to_list(meta_item)
        else:
            return meta_item

        return default

    def _dict_to_str(self, in_dict):
        """Convert dict to str"""
        out_str = ""
        for (key, val) in in_dict.items():
            out_str += f"{str(key)}:{str(val)} "

        return out_str

    def _dict_to_list(self, in_dict):
        """Convert dict to list"""
        out_list = []
        for (key, val) in in_dict.items():
            out_list.append(f"{str(key)}:{str(val)}")

        return out_list

    def _chk_container_root(self, container_id=None):
        """Check container ROOT sanity"""
        if container_id:
            container_dir = self.localrepo.cd_container(container_id)
        else:
            container_dir = self.localrepo.cd_container(self.container_id)

        if not container_dir:
            return 0

        container_root = container_dir + "/ROOT"
        check_list = ["/lib", "/bin", "/etc", "/tmp", "/var", "/usr", "/sys",
                      "/dev", "/data", "/home", "/system", "/root", "/proc", ]
        found = 0
        for f_path in check_list:
            if os.path.exists(container_root + f_path):
                found += 1

        return found

    def create_fromimage(self, imagerepo, tag):
        """Create a container from an image in the repository.
        Since images are stored as layers in tar files, this
        step consists in extracting those layers into a ROOT
        directory in the appropriate sequence.
        first argument: imagerepo
        second argument: image tag in that repo
        """
        self.imagerepo = imagerepo
        self.tag = tag
        image_dir = self.localrepo.cd_imagerepo(self.imagerepo, self.tag)
        if not image_dir:
            LOG.error("create container: imagerepo is invalid")
            return False

        (cntjson, layer_files) = self.localrepo.get_image_attributes()
        if not cntjson:
            LOG.error("create container: getting layers or json")
            return False

        if not self.container_id:
            self.container_id = Unique().uuid(os.path.basename(self.imagerepo))

        container_dir = self.localrepo.setup_container(self.imagerepo, self.tag,
                                                       self.container_id)
        if not container_dir:
            LOG.error("create container: setting up container")
            return False

        self.localrepo.save_json(container_dir + "/container.json", cntjson)
        status = self._untar_layers(layer_files, container_dir + "/ROOT")
        if not status:
            LOG.error("creating container: %s", self.container_id)
        elif not self._chk_container_root():
            LOG.warning("check container content: %s", self.container_id)

        return self.container_id

    def create_fromlayer(self, imagerepo, tag, layer_file, cntjson):
        """Create a container from a layer file exported by Docker.
        """
        self.imagerepo = imagerepo
        self.tag = tag
        if not self.container_id:
            self.container_id = Unique().uuid(os.path.basename(self.imagerepo))

        if not cntjson:
            LOG.error("create container: getting json")
            return False

        container_dir = self.localrepo.setup_container(self.imagerepo, self.tag,
                                                       self.container_id)
        if not container_dir:
            LOG.error("create container: setting up")
            return False

        fjson = container_dir + "/container.json"
        self.localrepo.save_json(fjson, cntjson)
        status = self._untar_layers([layer_file, ], container_dir + "/ROOT")
        if not status:
            LOG.error("creating container: %s", self.container_id)
        elif not self._chk_container_root():
            LOG.warning("check container content: %s", self.container_id)

        return self.container_id

    def clone_fromfile(self, clone_file):
        """Create a cloned container from a file containing a cloned container
        exported by udocker.
        """
        if not self.container_id:
            self.container_id = Unique().uuid(os.path.basename(self.imagerepo))

        container_dir = self.localrepo.setup_container("CLONING", "inprogress", self.container_id)
        if not container_dir:
            LOG.error("create container: setting up")
            return False

        status = self._untar_layers([clone_file, ], container_dir)
        if not status:
            LOG.error("creating container clone: %s", self.container_id)
        elif not self._chk_container_root():
            LOG.warning("check container content: %s", self.container_id)

        return self.container_id

    def _apply_whiteouts(self, tarf, destdir):
        """The layered filesystem of docker uses whiteout files
        to identify files or directories to be removed.
        The format is .wh.<filename>
        """
        verbose = ""
        if Config.conf['verbose_level'] == logging.DEBUG:
            verbose = 'v'
            LOG.debug("applying whiteouts: %s", tarf)

        wildcards = ["--wildcards", ]
        if not HostInfo().cmd_has_option("tar", wildcards[0]):
            wildcards = []

        cmd = ["tar", "t" + verbose] + wildcards + ["-f", tarf, r"*/.wh.*"]
        whiteouts = Uprocess().get_output(cmd, True)
        if not whiteouts:
            return

        for wh_filename in whiteouts.split('\n'):
            if wh_filename:
                wh_basename = os.path.basename(wh_filename.strip())
                wh_dirname = os.path.dirname(wh_filename)
                if wh_basename == ".wh..wh..opq":
                    if not os.path.isdir(destdir + '/' + wh_dirname):
                        continue

                    for f_name in os.listdir(destdir + '/' + wh_dirname):
                        rm_filename = destdir + '/' + wh_dirname + '/' + f_name
                        FileUtil(rm_filename).remove(recursive=True)
                elif wh_basename.startswith(".wh."):
                    whbaserep = wh_basename.replace(".wh.", "", 1)
                    rm_filename = destdir + '/' + wh_dirname + '/' + whbaserep
                    FileUtil(rm_filename).remove(recursive=True)

        return

    def _untar_layers(self, tarfiles, destdir):
        """Untar all container layers. Each layer is extracted
        and permissions are changed to avoid file permission
        issues when extracting the next layer.
        """
        if not (tarfiles and destdir):
            return False

        stderror = None
        if Config.conf['verbose_level'] == logging.DEBUG:
            stderror = sys.stderr

        status = True
        gid = str(HostInfo.gid)
        optional_flags = ["--wildcards", "--delay-directory-restore", ]
        for option in optional_flags:
            if not HostInfo().cmd_has_option("tar", option):
                optional_flags.remove(option)

        for tarf in tarfiles:
            if tarf != '-':
                self._apply_whiteouts(tarf, destdir)

            verbose = ''
            if Config.conf['verbose_level'] == logging.DEBUG:
                verbose = 'v'
                LOG.debug("extracting: %s", tarf)

            cmd = ["tar", "-C", destdir, "-x" + verbose,
                   "--one-file-system", "--no-same-owner", "--overwrite",
                   "--exclude=dev/*", "--exclude=etc/udev/devices/*",
                   "--no-same-permissions", r"--exclude=.wh.*",
                   ] + optional_flags + ["-f", tarf]
            if subprocess.call(cmd, stderr=stderror, close_fds=True):
                LOG.error("while extracting image layer")
                status = False

            cmd = ["find", destdir, "(", "-type", "d", "!", "-perm", "-u=x", "-exec",
                   "chmod", "u+x", "{}", ";", ")", ",", "(", "!", "-perm", "-u=w",
                   "-exec", "chmod", "u+w", "{}", ";", ")", ",", "(", "!", "-perm",
                   "-u=r", "-exec", "chmod", "u+r", "{}", ";", ")", ",", "(", "!", "-gid",
                   gid, "-exec", "chgrp", gid, "{}", ";", ")", ",", "(", "-name", ".wh.*",
                   "-exec", "rm", "-f", "--preserve-root", "{}", ";", ")"]

            if subprocess.call(cmd, stderr=stderror, close_fds=True):
                status = False
                LOG.error("while modifying attributes of image layer")

        return status

    def export_tofile(self, clone_file):
        """Export a container creating a tar file of the rootfs
        """
        cont_dir = self.localrepo.cd_container(self.container_id)
        if not cont_dir:
            LOG.error("container not found: %s", self.container_id)
            return False

        status = FileUtil(cont_dir + "/ROOT").tar(clone_file)
        if not status:
            LOG.error("exporting container file system: %s", self.container_id)

        return self.container_id

    def clone_tofile(self, clone_file):
        """Create a cloned container tar file containing both the rootfs
        and all udocker control files. This is udocker specific.
        """
        container_dir = self.localrepo.cd_container(self.container_id)
        if not container_dir:
            LOG.error("container not found: %s", self.container_id)
            return False

        status = FileUtil(container_dir).tar(clone_file)
        if not status:
            LOG.error("export container as clone: %s", self.container_id)

        return self.container_id

    def clone(self):
        """Clone a container by creating a complete copy
        """
        source_container_dir = self.localrepo.cd_container(self.container_id)
        if not source_container_dir:
            LOG.error("source container not found: %s", self.container_id)
            return False

        dest_container_id = Unique().uuid(os.path.basename(self.imagerepo))
        dest_container_dir = self.localrepo.setup_container("CLONING", "inprogress",
                                                            dest_container_id)
        if not dest_container_dir:
            LOG.error("create destination container: setting up")
            return False

        status = FileUtil(source_container_dir).copydir(dest_container_dir)
        if not status:
            LOG.error("creating container: %s", dest_container_id)
            return False

        if not self._chk_container_root(dest_container_id):
            LOG.warning("check container content: %s", dest_container_id)

        return dest_container_id
