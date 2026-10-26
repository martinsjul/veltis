"""Monta respostas GeoJSON, o formato que o Leaflet desenha direto."""

from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


TIPO_GEOJSON = "application/geo+json"


def colecao(
    linhas: list[dict],
    coluna_geometria: str = "geometria",
    coluna_id: str | None = None,
    metadados: dict[str, Any] | None = None,
) -> JSONResponse:
    """Transforma linhas do banco em uma FeatureCollection.

    A coluna de geometria precisa vir do banco já como GeoJSON
    (ST_AsGeoJSON(...)::json). As demais colunas viram "properties".
    """

    features = []
    for linha in linhas:
        propriedades = dict(linha)
        geometria = propriedades.pop(coluna_geometria)
        feature = {"type": "Feature", "geometry": geometria, "properties": propriedades}
        if coluna_id:
            feature["id"] = propriedades[coluna_id]
        features.append(feature)

    conteudo: dict[str, Any] = {"type": "FeatureCollection", "features": features}
    if metadados:
        conteudo["metadados"] = metadados

    return JSONResponse(content=jsonable_encoder(conteudo), media_type=TIPO_GEOJSON)


RESPOSTA_GEOJSON = {
    200: {
        "description": "FeatureCollection GeoJSON (coordenadas em WGS 84 / EPSG:4326).",
        "content": {TIPO_GEOJSON: {}},
    }
}
