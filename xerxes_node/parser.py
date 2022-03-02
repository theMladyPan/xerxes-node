#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from pprint import pprint
from typing import Dict, List
from xerxes_node.leaves.pleaf import AveragePLeafData, PLeaf


class Parser:
    @staticmethod
    def to_dict(averages: Dict, reference_addr: int):
        to_return = dict()
        for key in averages:
            to_return[hex(key)] = PLeaf.to_dict(averages[key], offset=averages[reference_addr].nivelation.preffered)

        return to_return