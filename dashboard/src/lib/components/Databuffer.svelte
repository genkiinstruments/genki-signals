<script lang="ts">
    let data: Record<string,any> = {}

    export let visible_rows = 25;
    export const update = (new_data: Record<string,any>) => {
        Object.keys(new_data).forEach(key => {
            const key_dim = new_data[key].length;
            new_data[key].forEach((_: any,i: number) => {
                const col_name = key + (key_dim > 1 ?  "_" + i : "");
                if (data[col_name] == null) {data[col_name] = new_data[key][i];}
                else {data[col_name] = data[col_name].concat(new_data[key][i]);}
                data[col_name] = data[col_name].slice(-visible_rows);
            });
        })
    }
</script>

<table class="my_table">
    <tr>
        {#each Object.keys(data) as colname}
            <th scope="col">{colname}</th>
        {/each}
    </tr>
    {#each Array(visible_rows) as _,i}
        <tr class={i%2==0 ? "even_row" : "odd_row"}>
            {#each Object.keys(data) as key}
                <td>{data[key][i]}</td>
            {/each}
        </tr>
    {/each}
</table>

<style>
    table.my_table {
        table-layout: fixed;
        width: 100%;
    }

    .even_row {
        background-color: rgb(222, 222, 222);
    }

    th, td {
        text-align: center;
        overflow: hidden;
    }
</style>