import time
import logging
from service import Singleton


EPOCH_TIMESTAMP = 1288834974657

class Snowflake(Singleton):

    def __init__(self, dc, worker):
        print("--------Snowflake--init-------")
        self.dc = dc
        self.worker = worker
        self.node_id = ((dc & 0x03)<< 8) | (worker & 0xff)
        self.last_timestamp = EPOCH_TIMESTAMP
        self.sequence = 0
        self.sequence_overload = 0
        self.errors = 0
        self.generated_ids = 0
        super().__init__(dc, worker)

    def get_next_id(self):
        curr_time = int(time.time() * 1000)

        if curr_time < self.last_timestamp:
            # stop handling requests til we've caught back up
            self.errors += 1
            raise Exception(f'Clock went backwards! {curr_time} < {self.last_timestamp}')

        if curr_time > self.last_timestamp:
            self.sequence = 0
            self.last_timestamp = curr_time

        self.sequence += 1

        if self.sequence > 4095:
            # the sequence is overload, just wait to next sequence
            logging.warning('The sequence has been overload')
            # raise Exception("The sequence has been overload")
            self.sequence_overload += 1
            time.sleep(0.001)
            return self.get_next_id()

        generated_id = ((curr_time - EPOCH_TIMESTAMP) << 22) | (self.node_id << 12) | self.sequence

        self.generated_ids += 1
        # print("------Snowflake------get_next_id---generated_id:", self.sequence, self.generated_ids, generated_id)
        return generated_id

    @property
    def stats(self):
        return {
            'dc': self.dc,
            'worker': self.worker,
            'timestamp': int(time.time()*1000), # current timestamp for this worker
            'last_timestamp': self.last_timestamp, # the last timestamp that generated ID on
            'sequence': self.sequence, # the sequence number for last timestamp
            'sequence_overload': self.sequence_overload, # the number of times that the sequence is overflow
            'errors': self.errors, # the number of times that clock went backward
        }


if __name__ == "__main__":
    pass

