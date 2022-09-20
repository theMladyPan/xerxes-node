#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from enum import Enum
import logging
import sys
from subprocess import TimeoutExpired
from threading import Lock
from threading import Thread
import time
from typing import List
from xerxes_node.hierarchy.branches.branch import Branch
from xerxes_node.network import ChecksumError, LengthError, MessageIncomplete, XerxesNetwork
log = logging.getLogger(__name__)

class NetworkBusy(Exception):
    pass


class Duplex(Enum):
    HALF = 1
    FULL = 0


class XerxesSystem:
    def __init__(self, branches: List[Branch], mode: Duplex, network: XerxesNetwork, std_timeout_s=-1):
        self._branches = branches
        self._mode = mode
        self._access_lock = Lock()
        self._std_timeout_s = std_timeout_s
        self._readings = []
        self._network = network

    def append_branch(self, branch: Branch):
        self._branches.append(branch)

    def _poll(self):
        
        # if network is read/write exclusive:
        if self._mode == Duplex.HALF:
            lock_acq = self._access_lock.acquire(blocking=True, timeout=self._std_timeout_s)
            if not lock_acq:
                log.warning("trying to access busy network")
                raise TimeoutExpired("unable to access network within timeout")

        # sync sensors 
        self._network.sync()
        time.sleep(0.1) # wait for sensors to acquire measurement

        for branch in self._branches:
            for leaf in branch:
                try:
                    leaf.fetch()
                except ChecksumError:
                    log.warning(f"message from leaf {leaf.address} has invalid checksum")
                except MessageIncomplete:
                    log.warning(f"message from leaf {leaf.address} is not complete.")
                except TimeoutError:
                    log.warning(f"Leaf {leaf.address} is not responding.")
                except Exception as e:
                    tbk = sys.exc_info()[2]
                    log.error(f"Unexpected error: {e}")    
                
        
        # release access lock
        if self._mode == Duplex.HALF:
            self._access_lock.release()

    def poll(self) -> None:
        if self._access_lock.locked() and self._mode == Duplex.HALF:
           raise NetworkBusy("Previous command is still in progress")
        poller = Thread(target = self._poll)
        poller.start()

    def busy(self) -> bool:
        return self._access_lock.locked()
        
    def wait(self, timeout=-1):
        locked = self._access_lock.acquire(timeout=timeout)
        self._access_lock.release()
        return locked
    
    @property
    def branches(self) -> List[Branch]:
        return list(self._branches)
    
    @branches.setter
    def branches(self, __b):
        raise NotImplementedError