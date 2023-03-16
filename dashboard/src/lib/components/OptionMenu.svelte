<script lang="ts">
	import { writable, get, type Writable } from 'svelte/store';

	import type { PlotOptions } from '$lib/scicharts/baseplot';
	import { get_default_line_plot_options } from '$lib/scicharts/line';
	import { get_default_trace_plot_options } from '$lib/scicharts/trace';
    import { get_default_bar_plot_options } from '$lib/scicharts/barplot';
    import { get_default_spectrogram_plot_options } from '$lib/scicharts/spectrogram';
    import { option_store, selected_index_store} from '$lib/stores/chart_stores';


    const demo: boolean = false;

    function change_selected(idx: number) {
        selected_index_store.set(idx);
    }

    function add_option(type: string) {
        let new_options: PlotOptions;
        if (type === 'line') {
            new_options = get_default_line_plot_options();
            new_options.description = 'New line plot';
            if (demo) {
                new_options.sig_x = [{sig_key: 'timestamp_us', sig_idx: 0}];
                new_options.sig_y = [{sig_key: 'random', sig_idx: 0}];
                new_options.x_axis_visible = false;
                new_options.n_visible_points = 200;
            }
        }
        else if (type === 'trace') {
            new_options = get_default_trace_plot_options();
            new_options.description = 'New trace plot';
            if (demo) {
                new_options.sig_x = [{sig_key: 'mouse_position', sig_idx: 0}];
                new_options.sig_y = [{sig_key: 'mouse_position', sig_idx: 1}];
                new_options.y_axis_flipped = true;
                new_options.n_visible_points = 150;
            }
        } 
        else if (type === 'bar') {
            new_options = get_default_bar_plot_options();
            new_options.sig_y = [{sig_name: "mouse_position", sig_idx: 0}, {sig_name: "mouse_position", sig_idx: 1}];
            new_options.auto_range = false;
            new_options.y_domain_max = 3000
            new_options.description = 'New bar plot';
            if (demo) {
                new_options.sig_y = [
                    {sig_key: 'stc', sig_idx: 0, sig_name: '❌'},
                    {sig_key: 'stc', sig_idx: 1, sig_name: '🟥'},
                    {sig_key: 'stc', sig_idx: 2, sig_name: '🔺'},
                    {sig_key: 'stc', sig_idx: 3, sig_name: '🔴'}
                ];
                new_options.auto_range = false;
            }
        }
        else if (type === 'spectrogram') {
            new_options = get_default_spectrogram_plot_options();
            new_options.sig_y = [{sig_key: "fourier", sig_idx: 0}];
            new_options.window_size = 1024;
            new_options.sampling_rate = 48000;
            new_options.colormap_max = 1;
            new_options.n_visible_windows = 300;
            new_options.description = 'New spectrogram';
            if (demo) {
                new_options.sig_y = [{sig_key: 'fourier', sig_idx: 0}];
                new_options.n_visible_windows = 1000;
                new_options.sampling_rate = 100;
                new_options.window_size = 32;
                new_options.colormap_max = 15;
            }
        }
        else {
            throw new Error('Invalid option type');
        }

        return () => {
            option_store.add_option(structuredClone(new_options)); // Not enough to spread the object
            const idx = option_store.count()-1;
            change_selected(idx);
        };
    }

    function add_derived_signal(){
        return () => {
            change_selected(-1)
        }
    }
</script>

<div class="option_menu">
    <div class="add_option_buttons">
        <button on:click={add_option('line')}>
            Add line plot
        </button>
        <button on:click={add_option('trace')}>
            Add trace plot
        </button>
        <button on:click={add_option('bar')}>
            Add bar plot
        </button>
        <button on:click={add_option('spectrogram')}>
            Add spectrogram
        </button>
        <button on:click={add_derived_signal()}>
            Add derived signal
        </button>
    </div>
    <div class="option_list">
        {#each $option_store as store, idx}
            <button on:click={() => change_selected(idx)} style='background-color: {idx===$selected_index_store? '#FF5F49': '#A5A6A5'}'>
                {idx}: {get(store).description}
            </button>
        {/each}
    </div>
</div>

<style>
    .option_menu {
        display: flex;
        flex-direction: column;
        align-items: center;
        max-width: 10%;
        overflow-y: scroll;
        overflow-x: hidden;
        margin-left: 10px;
    }

    .add_option_buttons {
        background-color: #F0F0F0;
        width: 100%;
    }

    .option_list {
        width: 100%;
        padding: 10px;
		list-style-type: none;
        display: flex;
        justify-content: center;
        flex-direction: row;
        flex-wrap: wrap;
    }

    .add_option_buttons button {
        width: 100%;
    }

    .option_list button {
        height: 3rem;
        width: 40%;
        margin: 5px 1px;
    }


</style>
