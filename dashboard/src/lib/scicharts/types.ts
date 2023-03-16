export interface ArrayDict {
	[key: string]: number[][];
}

export class SignalConfig {
    sig_key: string;
    sig_idx: number;
    sig_name: string;

    constructor(sig_key: string, sig_idx: number, sig_name?: string) {
        this.sig_key = sig_key;
        this.sig_idx = sig_idx;

        if (sig_name) {
            this.sig_name = sig_name;
        } else {
            this.sig_name = `${sig_key}_${sig_idx}`;
        }

    }
	// TODO: This is a bit of a hack but we want sig_key and sig_idx to be indicators of equality
    public get_id(): string {
		return `${this.sig_key}_${this.sig_idx}`;
	}

    public compare_to(o: SignalConfig): boolean {
		console.log('comparing...')
        // return this.sig_key === o.sig_key && this.sig_idx === o.sig_idx;
    }
}
