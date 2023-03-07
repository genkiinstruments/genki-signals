<script>
    import OptionWindow from '$lib/components/OptionWindow.svelte';
    import { get_default_line_plot_options } from '$lib/scicharts/line';

    const options = get_default_line_plot_options();

    options.sig_x.push(
        {'sig_name': 'timestamp', 'sig_idx': 0},
    );

    options.sig_y.push(
        {'sig_name': 'acc', 'sig_idx': 0},
        {'sig_name': 'acc', 'sig_idx': 1},
        {'sig_name': 'acc', 'sig_idx': 2},
    );

</script>

<!-- <OptionWindow/> -->
<OptionWindow object={options}/>