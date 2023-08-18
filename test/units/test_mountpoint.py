#!/usr/bin/env python
"""
udocker unit tests: MountPoint
"""
import pytest
from udocker.utils.mountpoint import MountPoint


@pytest.fixture
def lrepo(mocker):
    mock_lrepo = mocker.patch('udocker.container.localrepo.LocalRepository')
    return mock_lrepo


@pytest.fixture
def mpoint(mocker, lrepo):
    return MountPoint(lrepo, 'contID123')


data_setup = ((True, False, True, 0),
              (False, True, True, 1),
              (False, False, False, 1)
              )


@pytest.mark.parametrize('isdir,ismkdir,expected,mkdircall', data_setup)
def test_01_setup(mpoint, mocker, isdir, ismkdir, mkdircall, expected):
    """Test01 MountPoint().setup()."""
    mock_isdir = mocker.patch('os.path.isdir', return_value=isdir)
    mock_mkdir = mocker.patch('udocker.utils.mountpoint.FileUtil.mkdir', return_value=ismkdir)
    resout = mpoint.setup()
    assert resout == expected
    mock_isdir.assert_called()
    assert mock_mkdir.call_count == mkdircall


data_add = (('/.udocker/contID123/ROOT/mycpath', 'mycpath', '/.udocker/contID123/ROOT/mycpath'),)


@pytest.mark.parametrize('vpath,cpath,expected', data_add)
def test_02_add(mpoint, mocker, vpath, cpath, expected):
    """Test02 MountPoint().add()."""
    mock_validpath = mocker.patch('udocker.utils.mountpoint.FileUtil.getvalid_path',
                                  return_value=vpath)
    mpointattr = mpoint.mountpoints
    mpoint.add(cpath)
    assert mpointattr == {cpath: expected}
    mock_validpath.assert_called()


def test_03_delete(mpoint, mocker):
    """Test03 MountPoint().delete()."""
    mock_rpath = mocker.patch('os.path.realpath', return_value='/tmp')
    mock_npath = mocker.patch('os.path.normpath',
                              side_effect=['/controot/cont_path', '/controot/cont_path'])
    mock_dirname = mocker.patch('os.path.dirname', return_value='/ROOT/tmp')
    mock_furm = mocker.patch('udocker.utils.mountpoint.FileUtil.remove', return_value=True)
    mpoint.mountpoints = {'cont_path': '/cont/bin'}
    resout = mpoint.delete('cont_path')
    assert resout
    assert mpoint.mountpoints == {}
    mock_rpath.assert_called()


def test_04_delete(mpoint, mocker):
    """Test04 MountPoint().delete()."""
    mock_rpath = mocker.patch('os.path.realpath', return_value='/tmp')
    mpoint.mountpoints = {'some_path': '/cont/bin'}
    resout = mpoint.delete('cont_path')
    assert not resout



# @patch('udocker.utils.mountpoint.os.path.normpath')
# @patch.object(MountPoint, 'setup')
# @patch('udocker.utils.mountpoint.os.path.realpath')
# def test_05_delete_all(self, mock_realpath, mock_setup, mock_norm):
#     """Test05 MountPoint().delete_all()."""
#     container_id = "CONTAINERID"
#     mock_realpath.return_value = "/tmp"
#     mock_setup.return_value = True
#     mock_norm.side_effect = ['/controot/cont_path', '/controot/cont_path']
#     mpoint = MountPoint(self.local, container_id)
#     mpoint.mountpoints = {'cont_path': '/cont/bin'}
#     mpoint.delete_all()
#     self.assertEqual(mpoint.mountpoints, {})

# @patch.object(MountPoint, 'delete')
# @patch.object(MountPoint, 'add')
# @patch('udocker.utils.mountpoint.os.path.isdir')
# @patch('udocker.utils.mountpoint.os.path.islink')
# @patch('udocker.utils.mountpoint.FileUtil.putdata')
# @patch('udocker.utils.mountpoint.FileUtil.mkdir')
# @patch('udocker.utils.mountpoint.os.path.isfile')
# @patch('udocker.utils.mountpoint.os.path.exists')
# @patch.object(MountPoint, 'setup')
# @patch('udocker.utils.mountpoint.os.path.realpath')
# def test_06_create(self, mock_realpath, mock_setup, mock_exists, mock_isfile, mock_mkdir,
#                     mock_putdata, mock_islink, mock_isdir, mock_add, mock_del):
#     """Test06 MountPoint().create()."""
#     container_id = "CONTAINERID"
#     mock_realpath.return_value = "/tmp"
#     mock_setup.return_value = True
#     mock_exists.return_value = False
#     hpath = '/bin'
#     cpath = '/ROOT/bin'
#     mock_add.return_value = None
#     mock_del.return_value = True
#     mock_isfile.side_effect = [True, True]
#     mock_mkdir.return_value = False
#     mock_putdata.return_value = None
#     mock_islink.return_value = True
#     mock_isdir.return_value = False
#     mpoint = MountPoint(self.local, container_id)
#     status = mpoint.create(hpath, cpath)
#     self.assertTrue(mock_add.called)
#     self.assertTrue(mock_isfile.called)
#     self.assertTrue(mock_mkdir.called)
#     self.assertTrue(mock_putdata.called)
#     self.assertFalse(mock_del.called)
#     self.assertTrue(status)

#     mock_exists.return_value = False
#     mock_add.return_value = None
#     mock_del.return_value = True
#     mock_isfile.side_effect = [False, False]
#     mock_mkdir.return_value = True
#     mock_putdata.return_value = None
#     mock_islink.return_value = True
#     mock_isdir.return_value = True
#     mpoint = MountPoint(self.local, container_id)
#     status = mpoint.create(hpath, cpath)
#     self.assertTrue(mock_mkdir.called)
#     self.assertTrue(status)

#     mock_exists.return_value = False
#     mock_add.return_value = None
#     mock_del.return_value = True
#     mock_isfile.side_effect = [False, False]
#     mock_mkdir.return_value = False
#     mock_putdata.return_value = None
#     mock_islink.return_value = True
#     mock_isdir.return_value = True
#     mpoint = MountPoint(self.local, container_id)
#     status = mpoint.create(hpath, cpath)
#     self.assertTrue(mock_mkdir.called)
#     self.assertTrue(mock_del.called)
#     self.assertFalse(status)

# @patch('udocker.utils.mountpoint.os.path.realpath')
# @patch('udocker.utils.mountpoint.os.symlink')
# @patch('udocker.utils.mountpoint.os.path.exists')
# def test_07_save(self, mock_exists, mock_syml, mock_realpath):
#     """Test07 MountPoint().save()."""
#     container_id = "CONTAINERID"
#     cpath = 'cont_path'
#     mock_realpath.return_value = "/tmp"
#     mpoint = MountPoint(self.local, container_id)
#     mpoint.mountpoints = {'some_path': '/cont/bin'}
#     status = mpoint.save(cpath)
#     self.assertTrue(status)

#     mock_exists.return_value = False
#     mock_syml.return_value = None
#     mock_realpath.return_value = "/tmp"
#     mpoint = MountPoint(self.local, container_id)
#     mpoint.mountpoints = {'cont_path': '/cont/bin'}
#     status = mpoint.save(cpath)
#     self.assertTrue(status)
#     self.assertTrue(mock_exists.called)
#     self.assertTrue(mock_syml.called)

#     mock_realpath.return_value = "/tmp"
#     mock_exists.side_effect = IOError("fail")
#     mpoint = MountPoint(self.local, container_id)
#     mpoint.mountpoints = {'cont_path': '/cont/bin'}
#     status = mpoint.save(cpath)
#     self.assertFalse(status)

# @patch.object(MountPoint, 'save')
# @patch.object(MountPoint, 'setup')
# @patch('udocker.utils.mountpoint.os.path.realpath')
# def test_08_save_all(self, mock_realpath, mock_setup, mock_save):
#     """Test08 MountPoint().save_all()."""
#     container_id = "CONTAINERID"
#     mock_realpath.return_value = "/tmp"
#     mock_setup.return_value = True
#     mock_save.return_value = None
#     mpoint = MountPoint(self.local, container_id)
#     mpoint.mountpoints = {'cont_path': '/cont/bin'}
#     mpoint.save_all()
#     self.assertTrue(mock_save.called)

# @patch('udocker.utils.mountpoint.os.readlink')
# @patch('udocker.utils.mountpoint.os.listdir')
# @patch.object(MountPoint, 'setup')
# @patch('udocker.utils.mountpoint.os.path.realpath')
# def test_09_load_all(self, mock_realpath, mock_setup, mock_ldir, mock_readl):
#     """Test09 MountPoint().load_all()."""
#     container_id = "CONTAINERID"
#     result = {'/dir1': '/dir1', '/dir2': '/dir2'}
#     mock_realpath.return_value = "/tmp"
#     mock_setup.return_value = True
#     mock_ldir.return_value = ['/dir1', '/dir2']
#     mock_readl.side_effect = ['/dir1', '/dir2']
#     mpoint = MountPoint(self.local, container_id)
#     mpoint.load_all()
#     self.assertEqual(mpoint.mountpoints, result)

# @patch('udocker.utils.mountpoint.FileUtil.remove')
# @patch.object(MountPoint, 'delete_all')
# @patch.object(MountPoint, 'load_all')
# @patch.object(MountPoint, 'save_all')
# @patch.object(MountPoint, 'setup')
# @patch('udocker.utils.mountpoint.os.path.realpath')
# def test_10_restore(self, mock_realpath, mock_setup, mock_save, mock_load, mock_del, mock_rm):
#     """Test10 MountPoint().restore()."""
#     container_id = "CONTAINERID"
#     mock_realpath.return_value = "/tmp"
#     mock_setup.return_value = True
#     mock_save.return_value = None
#     mock_load.return_value = None
#     mock_del.return_value = None
#     mock_rm.return_value = None
#     mpoint = MountPoint(self.local, container_id)
#     mpoint.restore()
#     self.assertTrue(mock_save.called)
#     self.assertTrue(mock_load.called)
#     self.assertTrue(mock_del.called)
#     self.assertTrue(mock_rm.called)
