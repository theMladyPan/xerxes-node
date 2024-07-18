#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from pymongo import UpdateOne
from pymongo.collection import Collection
from threading import Thread
import os
import time
import json

log = logging.getLogger(__name__)

"""This module looks for new entries generated by worker and uploads them to the
database."""


class Uploader:
    worker: Thread

    def __init__(
        self, collection: Collection, workdir: str, upload_period: int = 10
    ):
        self.col = collection

        # check if measurements directory exists, if not create it
        if not os.path.isdir(workdir):
            try:
                os.mkdir(workdir)
            except:
                raise AttributeError(f"Directory {workdir} does not exist.")

        self._directory = workdir
        self._upload_period = upload_period

    def start(self) -> Thread:
        """Start new thread which periodically checks for new entries and
        uploads them to the database.

        returns: Thread object of the thread.
        """

        self._run = True
        self.worker = Thread(target=self._upload, name="Uploader")
        self.worker.start()
        return self.worker

    def stop(self) -> None:
        """Stop the thread."""
        self._run = False

        log.info("Waiting for uploader thread to finish...")
        # wait for thread to finish
        self.worker.join()

    @property
    def alive(self) -> bool:
        return self.worker.is_alive()

    def _upload(self) -> None:
        """Upload new entries to the database."""

        while self._run:
            for entry in os.listdir(self._directory):
                if entry.endswith(".dat"):
                    # unpickle data
                    filename = os.path.join(self._directory, entry)
                    with open(filename, "r") as f:
                        try:
                            # wait 10ms so that file is not locked
                            time.sleep(0.01) 
                            data = json.load(f)
                        except EOFError:
                            log.warning(
                                f"Uploader encountered empty file {filename}"
                            )
                            continue
                        except Exception as e:
                            log.error(
                                f"Unable to read {filename}: {e}"
                            )
                            continue

                    try:
                        keys = list(
                            data.keys()
                        )  # eg. XAL-1, XAL-2, XAL-3, time
                        # remove time from keys because we dont need to update it
                        keys.remove("time")
                        to_set = {
                            f"{key}.{k}": data[key][k]
                            for key in keys
                            for k in data[key]
                        }
                        
                        update_filter = {"time.datetime": data["time"]["datetime"]}
                        update_data = {"$set": to_set}
                        # update right away
                        result = self.col.update_one(update_filter, update_data, upsert=True) 
                        
                        # op = UpdateOne(
                        #     {"time.datetime": data["time"]["datetime"]},
                        #     {"$set": to_set},
                        #     upsert=True,
                        # )
                        # operations.append(op)
                        if result.modified_count or result.upserted_id:
                            if result.modified_count:
                                log.info(f"Modified document in database")
                            else:
                                log.info(f"Inserted new document in database")
                                
                            log.debug(f"Removing file: {filename}")
                        else:
                            log.error(f"Failed to update document in database, {result}")
                            log.warning(f"Data lost: {update_data}")
                        os.remove(filename)
                            

                    except Exception as e:
                        # probably a timeout, try again in 10s
                        log.warning(
                            f"Unable to upload {entry} to database: {e}"
                        )
                        time.sleep(10)

            time.sleep(0.1) # wait 100ms

        log.warning("Uploader thread stopped.")
