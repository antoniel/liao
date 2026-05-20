import folium
import pandas as pd

SITUACAO_COLORS = {"Operante": "green", "Pane": "red"}


def mapa_estacoes(df: pd.DataFrame, center=(-12.5, -41.5), zoom=6) -> folium.Map:
    m = folium.Map(location=list(center), zoom_start=zoom, tiles="CartoDB positron")
    for _, r in df.dropna(subset=["latitude", "longitude"]).iterrows():
        folium.CircleMarker(
            location=[r.latitude, r.longitude],
            radius=6,
            color=SITUACAO_COLORS.get(r.situacao, "gray"),
            fill=True,
            fill_opacity=0.8,
            tooltip=f"{r.codigo} — {r.nome}",
            popup=folium.Popup(
                f"<b>{r.codigo}</b> — {r.nome}<br>"
                f"Lat: {r.latitude}<br>Lon: {r.longitude}<br>"
                f"Altitude: {r.altitude_m} m<br>Situação: {r.situacao}",
                max_width=250,
            ),
        ).add_to(m)
    return m
