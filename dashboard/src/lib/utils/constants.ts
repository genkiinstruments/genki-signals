import { EAutoRange } from 'scichart/types/AutoRange';
import { ENumericFormat } from 'scichart/types/NumericFormat';
import type { INumericAxisOptions } from 'scichart/Charting/Visuals/Axis/NumericAxis';

export const MAX_BUFFER_SIZE: number = 10_000_000;

export const SCICHART_KEY: string =
	'36Eec/LdUqldqIV84CeRxeRvuN7krPdlK50832MhwqFQPLirRVQeNidwq3C/7Rgjid4IFoW2YSDYd9Dlb6Czb5qqnr7jYNeaUe6r2M2GKlJTnr1itLIlilFM9XOVJ+OC+jq59zqXAzQ7Q51IlmYgMtOlhigYO0W6oXKQN3OPJD3krTncQgjXEBaGZZgztevO457P2M6ErMgf8gpRd9OYSoZ4Ua3CYtzjUGuevlU1a9DPjE+euEeyFC7Sa6KysxS7LNGlS6j9xB8Qb3CamaUZ0H7urWOh6yQkaQfDWuaUggb4zFq/lar0InMcfV0AvawPoqf0lER3ggpXMinfoSYgYRy6l7XM505Af9kOoFWl5Sf5SZd5fZNPObRPCB0jVgoNiIumrreVMOVvi5rsSBBD73lFiAeFEgrca9scT77bEU634apbBDxQTPMuukWIG2ZtU5iA9H9VKlAIbl4HfnJgop0eM7cu3tR0DFlOKkX1pPzGLtXT7DZbuSrVIkiA+usyz5asYjlM4UgUCo0cZL4aDSx5HGyPsjEzqSXvxqVGbmpON8JIhkD3SANSBWbK0SJ0+C0lcjm8RacgkRPFR9D7iefhK0O/';

export const default_axis_options: INumericAxisOptions = {
	useNativeText: true,
	isVisible: true,
	drawMajorBands: true,
	drawMinorGridLines: true,
	drawMinorTickLines: true,
	drawMajorTickLines: true,
	drawMajorGridLines: true,
	labelStyle: { fontSize: 8 },
	labelFormat: ENumericFormat.Decimal,
	labelPrecision: 0,
	autoRange: EAutoRange.Never
};
