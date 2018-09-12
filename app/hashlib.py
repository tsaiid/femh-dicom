import json
import numpy as np
import hashlib

class PredResultJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(MyEncoder, self).default(obj)

def hash_pred_id(pred_result_dict):
    return hashlib.sha256(json.dumps(pred_result_dict, sort_keys=True, cls=PredResultJsonEncoder).encode('utf-8')).hexdigest()
