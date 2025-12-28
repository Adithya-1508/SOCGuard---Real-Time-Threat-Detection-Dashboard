import React, { useMemo } from "react";
import { ComposableMap, Geographies, Geography, Marker } from "react-simple-maps";
import { scaleLinear } from "d3-scale";

const geoUrl = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

const WorldMap = ({ alerts = [] }) => {
    // Filter alerts with valid lat/long
    const markers = useMemo(() => {
        return alerts
            .map(a => {
                const lat = Number(a.latitude);
                const lng = Number(a.longitude);
                if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;

                return {
                    name: a.ip,
                    coordinates: [
                        lng,
                        Math.max(-85, Math.min(85, lat))
                    ],
                    severity: typeof a.severity_score === 'number' ? a.severity_score : 0
                };
            })
            .filter(marker => marker !== null);
    }, [alerts]);

    const sizeScale = scaleLinear()
        .domain([0, 1])
        .range([4, 10]);

    return (
        <div className="w-full h-full rounded-xl bg-slate-900/50 border border-slate-800 overflow-hidden relative">
            <div className="absolute top-4 left-4 z-10">
                <h3 className="text-lg font-semibold text-white">Live Threat Map</h3>
                <p className="text-xs text-slate-400">Real-time global attack sources</p>
            </div>

            <ComposableMap
                projection="geoMercator"
                projectionConfig={{
                    scale: 100,
                }}
                style={{ width: "100%", height: "100%" }}
            >
                <Geographies geography={geoUrl}>
                    {({ geographies }) =>
                        geographies.map((geo) => (
                            <Geography
                                key={geo.rsmKey}
                                geography={geo}
                                fill="#1e293b"
                                stroke="#334155"
                                strokeWidth={0.5}
                                style={{
                                    default: { outline: "none" },
                                    hover: { fill: "#334155", outline: "none" },
                                    pressed: { outline: "none" },
                                }}
                            />
                        ))
                    }
                </Geographies>

                {markers.map((marker, i) => (
                    <Marker key={i} coordinates={marker.coordinates}>
                        <circle
                            r={sizeScale(marker.severity) * 2}
                            fill="none"
                            stroke={marker.severity > 0.8 ? "#ef4444" : "#eab308"}
                            strokeWidth={2}
                            className="animate-ping opacity-75"
                        />
                        <circle
                            r={sizeScale(marker.severity)}
                            fill={marker.severity > 0.8 ? "#ef4444" : marker.severity > 0.5 ? "#eab308" : "#22c55e"}
                            stroke="#fff"
                            strokeWidth={1}
                            style={{ opacity: 0.8 }}
                        />
                        <title>{marker.name} (Sev: {marker.severity})</title>
                    </Marker>
                ))}
            </ComposableMap>
        </div>
    );
};

export default WorldMap;
