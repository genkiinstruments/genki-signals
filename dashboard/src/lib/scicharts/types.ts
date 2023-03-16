export interface ArrayDict {
	[key: string]: number[][];
}

export interface SignalConfig {
	sig_key: string;
	sig_idx: number;
	sig_name?: string;
}

export function compare_signals(a: SignalConfig, b: SignalConfig): boolean {
	return a.sig_name === b.sig_name && a.sig_idx === b.sig_idx;
}
