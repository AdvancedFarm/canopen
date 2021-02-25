from .base import PdoBase, RPDOMap, TPDOMap, Variable

import logging
import itertools
import canopen

logger = logging.getLogger(__name__)


class PDO(PdoBase):
    """PDO Class for backwards compatibility
    :param rpdo: RPDO object holding the Receive PDO mappings
    :param tpdo: TPDO object holding the Transmit PDO mappings
    """

    def __init__(self, node, rpdo, tpdo):
        super(PDO, self).__init__(node)
        self.rx = rpdo.map
        self.tx = tpdo.map

        self.map = {}
        # the object 0x1A00 equals to key '1' so we remove 1 from the key
        for key, value in self.rx.items():
            self.map[0x1A00 + (key - 1)] = value
        for key, value in self.tx.items():
            self.map[0x1600 + (key - 1)] = value

    def __repr__(self):
        return "RPDOs:\n{}".format(self.rx) + "\nTPDOs:\n{}".format(self.tx)

class RPDO(PdoBase):
    """PDO specialization for the Receive PDO enabling the transfer of data from the master to the node.
    Properties 0x1400 to 0x1403 | Mapping 0x1600 to 0x1603.
    :param object node: Parent node for this object."""

    def __init__(self, node, com_offset=0x1400, map_offset=0x1600):
        super(RPDO, self).__init__(node)
        self.map = {}
        for map_no in range(512):
            if com_offset + map_no in node.object_dictionary:
                new_map = RPDOMap(
                    self,
                    com_offset + map_no,
                    map_offset + map_no)

                self.map[map_no + 1] = new_map

        logger.debug('RPDO Map as {0}'.format(len(self.map)))

    def __repr__(self):
        return "RPDOs:\n{}".format(self.map)

    def stop(self):
        """Stop transmission of all RPDOs.
        :raise TypeError: Exception is thrown if the node associated with the PDO does not
        support this function"""
        if isinstance(self.node, canopen.RemoteNode):
            for pdo in self.map.values():
                pdo.stop()
        else:
            raise TypeError('The node type does not support this function.')


class TPDO(PdoBase):
    """PDO specialization for the Transmit PDO enabling the transfer of data from the node to the master.
    Properties 0x1800 to 0x1803 | Mapping 0x1A00 to 0x1A03."""

    def __init__(self, node, com_offset=0x1800, map_offset=0x1A00):
        super(TPDO, self).__init__(node)
        self.map = {}
        for map_no in range(512):
            if com_offset + map_no in node.object_dictionary:
                new_map = TPDOMap(
                    self,
                    com_offset + map_no,
                    map_offset + map_no)

                self.map[map_no + 1] = new_map

        logger.debug('TPDO Map as {0}'.format(len(self.map)))

    def __repr__(self):
        return "TPDOs:\n{}".format(self.map)

    def stop(self):
        """Stop transmission of all TPDOs.
        :raise TypeError: Exception is thrown if the node associated with the PDO does not
        support this function"""
        if isinstance(canopen.LocalNode, self.node):
            for pdo in self.map.values():
                pdo.stop()
        else:
            raise TypeError('The node type does not support this function.')
