import { buffer_size } from '$lib/utils/constants';

/**
 * A custom buffer that can be subscribed to.
 * @param {Number} max_size 
 * @returns Object with subscribe, unsubscribe, push, view and clear functions.
 */
function create_buffer(max_size) {
    const buffer = [];
    /**
     * Maps graph id to its callback function.
     * @type {Object.<String, Function>}
     */
    const subscribers = {}; // Assumes that all callbacks want a single argument i.e. newly added data.

    return {
        subscribe: (/** @type {String} */ id, /** @type {Function} */ callback) => {
            if (id in subscribers) {
                throw new Error(`Duplicate subscriber id: ${id}`);
            }
            subscribers[id] = callback;
        },
        unsubscribe: (/** @type {String} */ id) => {
            delete subscribers[id];
        },
        push: (/** @type {Object[]} */ value) => {
            buffer.push(... value);
            if (buffer.length >= max_size) {
                buffer.splice(0, buffer.length - max_size);
            }
            const data = value.length == 0 ? [buffer[buffer.length-1]] : value;
            Object.values(subscribers).forEach((callback) => callback(data));
        },
        view: () => buffer,
        clear: () => { buffer.splice(0, buffer.length) },
        timestamp_range: () => {
            if (buffer.length == 0) return { min: 0, max: 0 };
            if (!('timestamp_us' in buffer[0])) throw new Error('No timestamp_us in buffer.');

            return {
                min: buffer[0]['timestamp_us'],
                // @ts-ignore - we can assume that timestamp_us is also in the last element of the buffer.
                max: buffer[buffer.length-1]['timestamp_us']
            }
        }
    };
}

// The main store for all data.
// "main.js" imports the store and pushes data to it.
// "*.svelte" (e.g. Trace.svelte) files import the store and subscribe to it.
export const data_buffer = create_buffer(buffer_size);