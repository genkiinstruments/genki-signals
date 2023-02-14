import { io } from 'socket.io-client';

/**
 * Opens a websocket connection to the server.
 * @param {string} url The URL to connect to.
 * @param {string} namespace The namespace to connect to.
 * @returns The socket object.
 */
export function get_socket(url, namespace) {
    const socket = io(url, { path: namespace });
    socket.on('connect', () => {
        console.log('Connected to server.');
    });

    return {
        'socket': socket,
    };
}
    