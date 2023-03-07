<script lang="ts">
    import { writable, get } from "svelte/store";

    import type { PlotOptions } from "$lib/scicharts/baseplot";
    import { get_default_line_plot_options, type LinePlotOptions } from "$lib/scicharts/line";

    import OptionWindow from "./OptionWindow.svelte";

</script>