export interface ISignalConfig {
    key: string;
    idx: number;
    name?: string;
}


export class Signal implements ISignalConfig {
    public key: string;
    public idx: number;
    public name: string = '';

    constructor(key: string, idx: number, name?: string) {
        this.key = key;
        this.idx = idx;
        this.update_name(name);
    }

    public static from_config(sig: ISignalConfig): Signal {
        return new Signal(sig.key, sig.idx, sig.name);
    }

    public get_config(): ISignalConfig {
        return {
            key: this.key,
            idx: this.idx,
            name: this.name,
        };
    }

    public set_config(sig: ISignalConfig): void {
        this.key = sig.key;
        this.idx = sig.idx;
        this.update_name(sig.name);
    }

	// TODO: This is a bit of a hack but we want key and idx to be indicators of equality
    public get_id(): string {
		return `${this.key}_${this.idx}`;
	}

    public compare_to(o: Signal | ISignalConfig): boolean {
        const other_signal = o instanceof Signal ? o : Signal.from_config(o);
        return this.get_id() === other_signal.get_id(); 
    }

    private update_name(name?: string): void {
        if (name) {
            this.name = name;
        } else {
            this.name = `${this.key}_${this.idx}`;
        }
    }
}
