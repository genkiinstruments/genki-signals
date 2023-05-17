from genki_signals.functions.base import SignalFunction
import genki_signals.functions as f


def encode_signal_fn(obj):
    """
    JSON encoder for SignalFunction objects, to be used with json.dump.
    """
    if isinstance(obj, SignalFunction):
        return {
            "__signal_function__": True,
            "type": obj.__class__.__name__,
            "inputs": obj.input_signals,
            "name": obj.name,
            "params": obj.params,
        }
    else:
        type_name = obj.__class__.__name__
        raise TypeError(f"Object of type '{type_name}' is not JSON serializable")


def decode_signal_fn(obj):
    """
    JSON decoder for SignalFunction objects, to be used with json.load.
    """
    if obj.get("__signal_function__"):
        cls = getattr(f, obj["type"])
        return cls(*obj["inputs"], name=obj["name"], **obj["params"])
    return obj
