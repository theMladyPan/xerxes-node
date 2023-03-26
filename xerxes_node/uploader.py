#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from pymongo import MongoClient
from pymongo.collection import Collection
from threading import Thread
import os
import time
import pickle

log = logging.getLogger(__name__)

"""This module looks for new entries generated by worker and uploads them to the
database."""

class Uploader:
    worker: Thread
    
    def __init__(self, uri: str, database: str, collection: str, directory: str):
        
        log.info("Connecting to database...")
        self.shard = MongoClient(uri)
        
        self.database = self.shard.get_database(database)
        
        log.info("Creating collection...")
        self.collection: Collection = self.database[collection]
        
        log.info(f"Database:collection {database}:{collection} connected")
        
        # check if measurements directory exists, if not create it
        if not os.path.isdir(directory):
            raise AttributeError(f"Directory {directory} does not exist.")
        else:
            self._directory = directory
    
    def start(self) -> Thread:
        """Start new thread which periodically checks for new entries and
        uploads them to the database.
        
        returns: Thread object of the thread.
        """
        
        self._run = True
        self.worker = Thread(target=self._upload)
        self.worker.start()
        return self.worker
        
        
    def stop(self) -> None:
        """Stop the thread."""
        self._run = False
        
        # wait for thread to finish
        self.worker.join()
        
        
    def _upload(self) -> None:
        """Upload new entries to the database."""
        
        while self._run:
            for entry in os.listdir(self._directory):
                if entry.endswith(".dat"):
                    # unpickle data
                    filename = os.path.join(self._directory, entry)
                    with open(filename, "rb") as f:
                        data = pickle.load(f)
                    
                    try:
                        result = self.collection.insert_one(data)
                        os.remove(filename)
                        log.info(f"Uploaded {entry} to database. Result: {result.inserted_id}")
                        
                    except Exception as e:
                        # probably a timeout, try again in 60s
                        log.warning(f"Unable to upload {entry} to database: {e}")
                        time.sleep(60)
            
            # sleep for 100ms to avoid busy waiting
            time.sleep(.1)