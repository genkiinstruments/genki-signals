/**
 * A SignalID defines how a specific attribute of a signal is accessed.
 * @typedef SignalID
 * @type {Object}
 * @property {string} key - The name of the attribute.
 * @property {number} index - The index of the attribute.
 */

/**
 * A RangeConfig defines which range of values are plotted on the graph and whether the range should be automatically adjusted.
 * @typedef RangeConfig
 * @type {Object}
 * @property {number} min - The minimum value of the range.
 * @property {number} max - The maximum value of the range.
 * @property {boolean} auto - Whether the range should be automatically adjusted.
 */

/**
 * s
 * @typedef DomainConfig
 * @type {Object}
 * @property {number} min - The minimum value of the domain.
 * @property {number} max - The maximum value of the domain.
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

