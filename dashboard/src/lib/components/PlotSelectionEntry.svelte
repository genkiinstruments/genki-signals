<script lang="ts">
    export let name: string;
    export let onSelect: () => void;
    export let onDelete: () => void;

</script>

<div class="plotSelectionEntry">
    <button on:click={() => onSelect()} class="plotNameButton">{name}</button>
    <button on:click={() => onDelete()} class="plotDeleteButton">x</button>
</div>

<style>
    .plotSelectionEntry {
        width: 100%;
        display: flex;
        justify-content: space-between;
        border-top-style: solid;
        border-width: thin;
    }

    .plotDeleteButton {
        position: relative;
        right: 0;
        height: 100%;
        border: none;
    }

    .plotNameButton {
        text-align: left;
        height: 100%;
        width: 100%;
        border: none;
        padding-right: 20px;
    }
</style>
    