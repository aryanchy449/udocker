#!/usr/bin/env python
"""
udocker unit tests: Uprocess
"""
import subprocess
from unittest import TestCase, main
from unittest.mock import patch
from udocker.utils.uprocess import Uprocess, LOG
from udocker.config import Config
import collections
collections.Callable = collections.abc.Callable


class UprocessTestCase(TestCase):
    """Test case for the Uprocess class."""

    def setUp(self):
        LOG.setLevel(100)
        Config().getconf()

    def tearDown(self):
        pass

    @patch('udocker.utils.uprocess.os.path.lexists')
    @patch('udocker.utils.uprocess.os.path.basename')
    def test_01_find_inpath(self, mock_base, mock_lexists):
        """Test01 Uprocess().find_inpath()."""
        fname = ''
        path = ''
        uproc = Uprocess()
        status = uproc.find_inpath(fname, path)
        self.assertEqual(status, '')

        fname = 'ls'
        path = '/bin'
        mock_base.return_value = 'ls'
        mock_lexists.return_value = True
        uproc = Uprocess()
        status = uproc.find_inpath(fname, path)
        self.assertEqual(status, '/bin/ls')

    @patch('udocker.utils.uprocess.subprocess.Popen')
    def test_02__check_output(self, mock_popen):
        """Test02 Uprocess()._check_output()."""
        mock_popen.return_value.communicate.return_value = ("OUTPUT", None)
        mock_popen.return_value.poll.return_value = 0
        uproc = Uprocess()
        status = uproc._check_output("CMD")
        self.assertEqual(status, "OUTPUT")

        mock_popen.return_value.communicate.return_value = ("OUTPUT", None)
        mock_popen.return_value.poll.return_value = 1
        uproc = Uprocess()
        self.assertRaises(subprocess.CalledProcessError, uproc._check_output, "CMD")

    @patch.object(Uprocess, '_check_output')
    @patch('udocker.utils.uprocess.subprocess.check_output')
    def test_03_check_output(self, mock_subp_chkout, mock_chkout):
        """Test03 Uprocess().check_output()."""
        mock_subp_chkout.return_value = b""
        mock_chkout.side_effect = OSError("fail")
        uproc = Uprocess()
        status = uproc.check_output()
        self.assertEqual(status, "")

        mock_subp_chkout.return_value = b"cmd"
        uproc = Uprocess()
        status = uproc.check_output("CMD")
        self.assertTrue(mock_subp_chkout.called)
        self.assertEqual(status, "cmd")

    @patch('udocker.utils.uprocess.Uprocess.check_output')
    def test_04_get_output(self, mock_uproc_chkout):
        """Test04 Uprocess().get_output()."""
        mock_uproc_chkout.return_value = "OUTPUT"
        uproc = Uprocess()
        self.assertEqual("OUTPUT", uproc.get_output("CMD"))

    @patch.object(Uprocess, 'find_inpath')
    @patch('udocker.utils.uprocess.subprocess.call')
    def test_05_call(self, mock_subcall, mock_find):
        """Test05 Uprocess().call()."""
        mock_find.return_value = '/bin/ls'
        mock_subcall.return_value = 0
        uproc = Uprocess()
        status = uproc.call('/bin/ls')
        self.assertEqual(status, 0)

    # @patch.object(Uprocess, 'find_inpath')
    # @patch('udocker.utils.uprocess.subprocess.Popen')
    # def test_06_pipe(self, mock_popen, mock_find):
    #     """Test06 Uprocess().pipe()."""
    #     mock_find.side_effect = ["/bin/ls", "/usr/bin/grep"]


if __name__ == '__main__':
    main()
