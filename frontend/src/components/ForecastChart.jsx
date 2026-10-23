import {
    ComposedChart,
    Area,
    Line,
    XAxis,
    YAxis,
    Tooltip,
    CartesianGrid,
    ResponsiveContainer,
} from "recharts";

const rupees = (v) => "₹" + Math.round(v).toLocaleString("en-IN");

// forecast = {dates, expected, low, high, negative_probability}
// stress   = same shape, optional. Drawn as a second line.
export default function ForecastChart({ forecast, stress }) {
    const rows = forecast.dates.map((d, i) => ({
        date: d,
        expected: forecast.expected[i],
        band: [forecast.low[i], forecast.high[i]],
        stressed: stress ? stress.expected[i] : undefined,
    }));

    return (
        <div style={{ width: "100%", height: 320 }}>
            <ResponsiveContainer>
                <ComposedChart data={rows}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" minTickGap={40} />
                    <YAxis tickFormatter={rupees} width={90} />
                    <Tooltip formatter={(v) => (Array.isArray(v) ? v.map(rupees).join(" to ") : rupees(v))} />
                    <Area dataKey="band" name="Low to high range" fillOpacity={0.15} />
                    <Line dataKey="expected" name="Expected" dot={false} strokeWidth={2} />
                    {stress && <Line dataKey="stressed" name="Stressed" dot={false} strokeDasharray="6 4" strokeWidth={2} />}
                </ComposedChart>
            </ResponsiveContainer>
        </div>
    );
}