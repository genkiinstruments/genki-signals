from genki_signals.signal_functions.base import SignalFunction
import genki_signals.signal_functions as s


def encode_signal_fn(obj):
    if isinstance(obj, SignalFunction):
        return {
            '__signal_function__': True,
            'type': obj.__class__.__name__,
            'inputs': obj.input_signals,
            'name': obj.name,
            'params': obj.params
        }
    else:
        type_name = obj.__class__.__name__
        raise TypeError(f"Object of type '{type_name}' is not JSON serializable")


def decode_signal_fn(obj):
    if obj.get('__signal_function__'):
        cls = getattr(s, obj['type'])
        return cls(*obj['inputs'], name=obj['name'], **obj['params'])
    return obj