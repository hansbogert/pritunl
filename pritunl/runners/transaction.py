from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import mongo
from pritunl import logger
from pritunl import transaction
from pritunl import utils

import pymongo
import collections
import datetime
import bson
import threading
import time

@interrupter
def _check_thread():
    collection = mongo.get_collection('transaction')

    while True:
        try:
            spec = {
                'ttl_timestamp': {'$lt': utils.now()},
            }

            for doc in collection.find(spec).sort('priority'):
                try:
                    tran = transaction.Transaction(doc=doc)
                    tran.run()
                except:
                    logger.exception('Failed to run transaction. %r' % {
                        'transaction_id': doc['_id'],
                    })

            yield interrupter_sleep(settings.mongo.tran_ttl)
        except GeneratorExit:
            raise
        except:
            logger.exception('Error in transaction runner thread.')
            time.sleep(0.5)

def start_transaction():
    threading.Thread(target=_check_thread).start()
