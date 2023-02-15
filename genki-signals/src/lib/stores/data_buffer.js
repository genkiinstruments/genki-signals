import { buffer_size } from '$lib/utils/constants';

/**
 * A custom buffer that can be subscribed to.
 * @param {Number} max_size 
 * @returns Object with subscribe, unsubscribe, push, view and clear functions.
 */
function create_buffer(max_size) {
    const buffer = [{}];
    /**
     * @type {Function[]}
     */
    const subscribers = []; // Assumes that all callbacks want a single argument i.e. the buffer.

    return {
        subscribe: (/** @type {Function} */ callback) => {
            subscribers.push(callback);
        },
        unsubscribe: (/** @type {Function} */ callback) => {
            const index = subscribers.indexOf(callback);
            if (index !== -1) {
                subscribers.splice(index, 1);
            }
        },
        push: (/** @type {Array<Object>} */ value) => {
            buffer.push(... value);
            if (buffer.length >= max_size) {
                buffer.splice(0, buffer.length - max_size);
            }
            subscribers.forEach((callback) => callback(buffer));
            // return buffer;
        },
        view: () => buffer,
        clear: () => { buffer.splice(0, buffer.length)}
    };
}

// The main store for all data.
// "main.js" imports the store and pushes data to it.
// "*.svelte" (e.g. Trace.svelte) files import the store and subscribe to it.
export const data_buffer = create_buffer(buffer_size);