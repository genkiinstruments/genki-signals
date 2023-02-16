/**
 * A SignalID defines how a specific attribute of a signal is accessed.
 * @typedef SignalID
 * @type {Object}
 * @property {string} key - The name of the attribute.
 * @property {number} index - The index of the attribute.
 */

/**
 * s
 * @typedef DomainConfig
 * @type {Object}
 * @property {number} min - The minimum value of the domain.
 * @property {number} max - The maximum value of the domain.
 * @property {boolean} auto - Whether the domain should be automatically adjusted.
 */ 


// // @ts-nocheck
// // default values for the range and domain configs
// /**
//  * @param {Object} partial_config
//  * @returns {RangeConfig}
//  */
// export function range_factory(partial_config) {
//     /** @type {RangeConfig} */
//     const default_config = { min: 0, max: 1, auto: false };
//     for (const key in partial_config) {
//         // @ts-ignore
//         if ( key in default_config && typeof partial_config[key] === typeof default_config[key] ) {
//             default_config[key] = partial_config[key];
//         } 
//         else {
//             throw new Error(`Invalid config key: ${key}`);
//         }
//     }
//     return default_config;
// }

