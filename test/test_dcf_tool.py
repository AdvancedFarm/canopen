import os
import unittest
import canopen
import logging
import time
import tempfile

from canopen.dcf_tool import read_dcf_from_node, write_dcf_to_node

# logging.basicConfig(level=logging.DEBUG)

EDS_PATH = os.path.join(os.path.dirname(__file__), 'sample.eds')
DCF_PATH = os.path.join(os.path.dirname(__file__), 'sample.dcf')


class TestDCFTool(unittest.TestCase):
    """
    Test DCF Tool
    """

    @classmethod
    def setUpClass(cls):
        cls.nodeid = 1
        cls.network1 = canopen.Network()
        cls.network1.connect("test", bustype="virtual")
        cls.local_node = cls.network1.create_node(cls.nodeid, EDS_PATH)

        cls.network2 = canopen.Network()
        cls.network2.connect("test", bustype="virtual")

    # @classmethod
    # def tearDownClass(cls):
    #     import pdb; pdb.set_trace()
    #     cls.network1.disconnect()
    #     cls.network2.disconnect()

    @unittest.skip("Not working yet")
    def test_read(self):
        #set some configs in the local node, so we can read them to a dcf
        self.local_node.tpdo[1].clear()
        self.local_node.tpdo[1].cob_id = 0x181
        self.local_node.tpdo[1].add_variable('INTEGER16 value')
        self.local_node.tpdo[1].add_variable('BOOLEAN value', length=1)
        self.local_node.tpdo[1].trans_type = 254
        self.local_node.tpdo[1].enabled = True
        self.local_node.od[0x2000].value = "Test String"

        outdir = tempfile.TemporaryDirectory()
        dcf_file = os.path.join(outdir.name, 'outfile.dcf')
        logging.debug("Creating dcf file: {}".format(dcf_file))
        read_dcf_from_node(self.network2, self.nodeid, EDS_PATH, dcf_file)

        #read back the DCF and check to see that everything matches
        node = canopen.RemoteNode(self.nodeid, dcf_file)
        self.assertEqual(node.od[0x2000].value, "Test String")
        self.assertEqual(node.tpdo[1], self.local_node.tpdo[1])

    def test_write(self):

        write_dcf_to_node(self.network2, self.nodeid, DCF_PATH)

        #check that we correctly wrote some values
        self.assertEqual(self.local_node.od[0x2000].value, 'hello!')
        self.assertEqual(self.local_node.od[0x2001].value, 12345)
        self.assertEqual(self.local_node.od[0x2002].value, 12)
        self.assertEqual(self.local_node.od[0x2003].value, 123)
        self.assertEqual(self.local_node.od[0x2004].value, 123456)
        self.assertEqual(self.local_node.od[0x2005].value, True)
        self.assertEqual(self.local_node.od[0x2006].value, False)

        #check the rpdo cobids
        self.assertEqual(self.local_node.rpdo[1].cob_id, 0x00000201)
        self.assertEqual(self.local_node.rpdo[2].cob_id, 0x80000000)
        self.assertEqual(self.local_node.rpdo[3].cob_id, 0x80000000)
        self.assertEqual(self.local_node.rpdo[4].cob_id, 0x80000000)

        #check rpdo 1 map
        self.assertEqual(self.local_node.rpdo[1].map[0].index, 0x6040)
        self.assertEqual(self.local_node.rpdo[1].map[1].index, 0x60FF)

        #check the tpdo cobids
        self.assertEqual(self.local_node.tpdo[1].cob_id, 0x00000181)
        self.assertEqual(self.local_node.tpdo[2].cob_id, 0x00000281)
        self.assertEqual(self.local_node.tpdo[3].cob_id, 0x80000000)
        self.assertEqual(self.local_node.tpdo[4].cob_id, 0x80000000)

        #check tpdo 1 map
        self.assertEqual(self.local_node.tpdo[1].map[0].index, 0x6041)
        self.assertEqual(self.local_node.tpdo[2].map[0].index, 0x606C)

if __name__ == "__main__":
    unittest.main()