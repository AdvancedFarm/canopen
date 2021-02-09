#!/usr/bin/env python
"""
A tool for reading and writing dcf files to/from canopen devices
"""
import argparse
import sys
try:
    from configparser import RawConfigParser
except ImportError:
    from ConfigParser import RawConfigParser

import canopen


def read_dcf_from_node(network, node_id, eds_file):

    # Create a configparser that preserves comments
    eds = RawConfigParser(allow_no_value=True)
    # Also preserve case
    eds.optionxform = lambda option: option

    # TODO: how should we set the bitrate?
    eds['DeviceComissioning'] = {
        'NodeID': node_id,
        'Baudrate': None,
    }

    with open(eds_file) as fp:
        try:
            # Python 3
            eds.read_file(fp)
        except AttributeError:
            # Python 2
            eds.readfp(fp)

    #connect to the node by also specifying the eds file
    node = canopen.RemoteNode(node_id, eds_file)
    network.add_node(node)

    for entry in node.object_dictionary.values():

        if isinstance(entry, canopen.objectdictionary.Record):
            objs = entry.values()
        elif isinstance(entry, canopen.objectdictionary.Array):
            objs = entry.values()
        else:
            objs = [entry]

        for obj in objs:
            if not obj.readable:
                continue

            if obj.refuse_read_on_scan:
                continue

            try:
                val = node.sdo.upload(obj.index, obj.subindex)
                section = "{:04X}".format(obj.index)
                if len(objs) > 1:
                    section += "sub{:X}".format(obj.subindex)
                eds.set(section, 'ParameterValue', "0x{}".format(val.hex()))
            except Exception as exc:
                print(
                    "{:04x}:{:02x} ({})\n\t{}\n".format(
                        obj.index, obj.subindex, obj.name, exc
                    )
                )
                continue

    root, _ = os.path.splitext(eds_file)
    dcffile = os.path.join(root, '.dcf')

    with open(dcffile, 'w') as configfile:
        eds.write(configfile)

def write_dcf_to_node(network, node_id, dcf_file):
    node = canopen.RemoteNode(node_id, dcf_file)
    network.add_node(node)

    # TODO: how do we set the nodeid and bitrate?

    tpdo_comm_regs = [x.com_record.od.index for x in node.tpdo.values()]
    tpdo_map_regs = [x.map_array.od.index for x in node.tpdo.values()]
    rpdo_comm_regs = [x.com_record.od.index for x in node.rpdo.values()]
    rpdo_map_regs = [x.map_array.od.index for x in node.rpdo.values()]

    pdo_regs = tpdo_comm_regs + tpdo_map_regs + rpdo_comm_regs + rpdo_map_regs

    for entry in node.object_dictionary.values():

        if entry.index in pdo_regs:
            continue

        if isinstance(entry, canopen.objectdictionary.Record):
            objs = entry.values()
        elif isinstance(entry, canopen.objectdictionary.Array):
            objs = entry.values()
        else:
            objs = [entry]

        for obj in objs:
            if not obj.writable:
                continue

            if obj.refuse_write_on_download:
                continue

            try:
                raw = obj.encode_raw(obj.value)
                node.sdo.download(obj.index, obj.subindex, raw)
            except Exception as exc:
                print(
                    "{:04x}:{:02x} ({})\n\t{}\n".format(
                        obj.index, obj.subindex, obj.name, exc
                    )
                )
                continue

    # save the pdo configs
    node.tpdo.save()
    node.rpdo.save()


def setup_opts():
    desc = ''' DCF Read/Write Tool
    Allows reading a DCF from a node, or writing a DCF to a node.
    Examples: 
        python dcf_tool.py -i can0 -n 1 read node1.eds
        python dcf_tool.py -i can0 -n 1 write node1.dcf
    '''
    parser = argparse.ArgumentParser(
        description=desc,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-b",
        "--bustype",
        default='socketcan',
        type=str,
        help=(
            "Network interface. Default: %(default)s"
        )
    )

    parser.add_argument(
        "-i",
        "--interface",
        default='can0',
        type=str,
        help=(
            "Network interface Default: %(default)s"
        )
    )

    parser.add_argument(
        "-n",
        "--nodeid",
        default=1,
        type=int,
        help=(
            "CANopen node id. Default: %(default)s"
        )
    )

    commands = parser.add_subparsers(
        title="commands",
        metavar="<command>",
        parser_class=argparse.ArgumentParser
    )

    read_cmd = commands.add_parser(
        "read",
        help="Read object dictionary from device",
    )
    read_cmd.set_defaults(func='read')
    read_cmd.add_argument(
        "edsfile", help=("EDS file for the node from which to read")
    )

    write_cmd = commands.add_parser(
        "write",
        help="Write object dictionary to device",
    )
    write_cmd.set_defaults(func='write')
    write_cmd.add_argument("dcffile", help=("DCF file to write to the node"))

    return parser.parse_args()

def main():
    opts = setup_opts()

    network = canopen.Network()
    try:
        network.connect(bustype=opts.bustype, channel=opts.interface)
    except Exception as exc:
        print("Error connecting to network:\n{}".format(exc))
        sys.exit(1)

    if opts.func == 'read':
        read_dcf_from_node(network, opts.nodeid, opts.edsfile)
    elif opts.func == 'write':
        write_dcf_to_node(network, opts.nodeid, opts.dcffile)


if __name__ == "__main__":
    main()