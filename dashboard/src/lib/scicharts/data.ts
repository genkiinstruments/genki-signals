export interface ArrayDict {
	[key: string]: number[][];
}

export interface SignalConfig {
    key: string;
    idx: number;
    name?: string;
}

export class Signal implements SignalConfig {
    public key: string;
    public idx: number;
    public name: string = '';

    constructor(key: string, idx: number, name?: string) {
        this.key = key;
        this.idx = idx;
        this.update_name(name);
    }

    public static from_config(sig: SignalConfig): Signal {
        return new Signal(sig.key, sig.idx, sig.name);
    }

    public get_config(): SignalConfig {
        return {
            key: this.key,
            idx: this.idx,
            name: this.name,
        };
    }

    public set_config(sig: SignalConfig): void {
        this.key = sig.key;
        this.idx = sig.idx;
        this.update_name(sig.name);
    }

	// TODO: This is a bit of a hack but we want key and idx to be indicators of equality
    public get_id(): string {
		return `${this.key}_${this.idx}`;
	}

    public compare_to(o: Signal | SignalConfig): boolean {
        return this.key === o.key && this.idx === o.idx;
    }

    private update_name(name?: string): void {
        if (name) {
            this.name = name;
        } else {
            this.name = `${this.key} ${this.idx}`;
        }
    }
}
