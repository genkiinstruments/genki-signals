<script lang="ts">
    export let name: string;
    export let onSelect: () => void;
    export let onDelete: () => void;

</script>

<div>
    <button on:click={() => onSelect()}>{name}</button>
    <button on:click={() => onDelete()}>x</button>
</div>
    