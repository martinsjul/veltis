import { memo, useEffect, useRef, useState } from 'react'
import { Map, Popup, config, MapStyle } from '@maptiler/sdk'
import '@maptiler/sdk/dist/maptiler-sdk.css'
import { getMarkerColor } from '../utils/institution'

const DEFAULT_CENTER = [-47.4521, -23.5015]
const DEFAULT_ZOOM = 7
const MUNICIPALITY_SOURCE_ID = 'veltis-municipalities'
const MUNICIPALITY_FILL_ID = 'veltis-municipalities-fill'
const MUNICIPALITY_LINE_ID = 'veltis-municipalities-outline'
const SELECTED_SOURCE_ID = 'veltis-selected-municipality'
const SELECTED_FILL_ID = 'veltis-selected-municipality-fill'
const SELECTED_LINE_ID = 'veltis-selected-municipality-outline'
const RMS_SOURCE_ID = 'veltis-rms-dataset'
const RMS_FILL_ID = 'veltis-rms-dataset-fill'
const RMS_LINE_ID = 'veltis-rms-dataset-outline'

// Instituições: uma única fonte GeoJSON desenhada pela GPU (em vez de um elemento HTML por pino).
const INST_SOURCE_ID = 'veltis-instituicoes'
const INST_CLUSTER_LAYER_ID = 'veltis-instituicoes-grupos'
const INST_COUNT_LAYER_ID = 'veltis-instituicoes-contagem'
const INST_POINT_LAYER_ID = 'veltis-instituicoes-pontos'
const PICKED_SOURCE_ID = 'veltis-instituicao-selecionada'
const PICKED_LAYER_ID = 'veltis-instituicao-selecionada-anel'
const CLUSTER_MAX_ZOOM = 13 // acima disso os pontos aparecem individualmente
const FOCUS_ZOOM = 15

const MUNICIPALITY_NAME_KEYS = ['NM_MUN', 'nm_mun', 'NO_MUNICIPIO', 'no_municipio', 'nome_municipio', 'municipio', 'nome', 'name']
const MUNICIPALITY_CODE_KEYS = ['CD_MUN', 'cd_mun', 'codigo_ibge', 'codigo_municipio', 'co_municipio', 'id']

function normalizeName(value) {
  return String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim().toLocaleLowerCase('pt-BR')
}

function findProperty(properties, keys) {
  for (const key of keys) {
    if (properties?.[key] !== undefined && properties[key] !== null && properties[key] !== '') return properties[key]
  }
  return null
}

function MapView({ institutions, fitKey = '', municipalitiesGeoJson, selectedMunicipality, selectedInstitution, onSelect }) {
  const containerRef = useRef(null)
  const mapRef = useRef(null)
  const [mapReady, setMapReady] = useState(false)
  const byIdRef = useRef(new globalThis.Map())
  const onSelectRef = useRef(onSelect)
  const lastFitKeyRef = useRef('')

  useEffect(() => {
    onSelectRef.current = onSelect
  }, [onSelect])

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return undefined

    const apiKey = import.meta.env.VITE_MAPTILER_KEY
    if (!apiKey) {
      console.warn('VITE_MAPTILER_KEY não configurada. O mapa não poderá ser inicializado.')
      return undefined
    }

    config.apiKey = apiKey

    const map = new Map({
      container: containerRef.current,
      style: MapStyle.STREETS,
      center: DEFAULT_CENTER,
      zoom: DEFAULT_ZOOM,
      minZoom: 8,
      maxZoom: 18,
      // Limites um pouco mais amplos para permitir enquadrar toda a RMS sem prender
      // a região atrás da barra lateral.
      maxBounds: [
        [-48.55, -24.45],
        [-46.55, -22.55],
      ],
    })

    // Reserva espaço visual para a sidebar fixa à esquerda. Em telas pequenas,
    // a sidebar ocupa menos espaço e o mapa volta a usar quase toda a largura.
    const applyMapPadding = () => {
      const width = window.innerWidth
      const left = width > 860 ? 390 : width > 620 ? 360 : 16
      map.setPadding({ top: 24, right: 24, bottom: 24, left })
    }
    applyMapPadding()
    window.addEventListener('resize', applyMapPadding)

    mapRef.current = map
    const handleLoad = () => setMapReady(true)
    map.on('load', handleLoad)

    return () => {
      map.off('load', handleLoad)
      window.removeEventListener('resize', applyMapPadding)
      map.remove()
      mapRef.current = null
    }
  }, [])

  // Desenha os contornos municipais retornados por GET /municipios, quando a API os fornece em GeoJSON.
  useEffect(() => {
    const map = mapRef.current
    if (!map || !mapReady || !municipalitiesGeoJson?.features?.length) return

    const wanted = normalizeName(selectedMunicipality)
    const selectedFeatures = wanted
      ? municipalitiesGeoJson.features.filter((feature) => {
          const properties = feature?.properties || {}
          const name = findProperty(properties, MUNICIPALITY_NAME_KEYS)
          return normalizeName(name) === wanted
        })
      : null
    const visibleMunicipalities = wanted
      ? { type: 'FeatureCollection', features: selectedFeatures }
      : municipalitiesGeoJson

    if (map.getSource(MUNICIPALITY_SOURCE_ID)) {
      map.getSource(MUNICIPALITY_SOURCE_ID).setData(visibleMunicipalities)
      return
    }

    try {
      map.addSource(MUNICIPALITY_SOURCE_ID, {
        type: 'geojson',
        data: visibleMunicipalities,
      })

      map.addLayer({
        id: MUNICIPALITY_FILL_ID,
        type: 'fill',
        source: MUNICIPALITY_SOURCE_ID,
        paint: {
          'fill-color': '#0E7C79',
          'fill-opacity': 0.045,
        },
      })

      map.addLayer({
        id: MUNICIPALITY_LINE_ID,
        type: 'line',
        source: MUNICIPALITY_SOURCE_ID,
        paint: {
          'line-color': '#0A7774',
          'line-width': 1.15,
          'line-opacity': 0.58,
        },
      })
    } catch (error) {
      console.warn('Não foi possível desenhar os contornos de /municipios. Confira se a resposta é GeoJSON válido.', error)
    }
  }, [municipalitiesGeoJson, selectedMunicipality, mapReady])

  // Destaca apenas o município pesquisado/selecionado usando a malha recebida pela API.
  useEffect(() => {
    const map = mapRef.current
    if (!map || !mapReady || !municipalitiesGeoJson?.features) return

    const wanted = normalizeName(selectedMunicipality)
    const features = wanted
      ? municipalitiesGeoJson.features.filter((feature) => {
          const properties = feature?.properties || {}
          const name = findProperty(properties, MUNICIPALITY_NAME_KEYS)
          return normalizeName(name) === wanted
        })
      : []
    const selectedGeoJson = { type: 'FeatureCollection', features }

    try {
      if (map.getSource(SELECTED_SOURCE_ID)) {
        map.getSource(SELECTED_SOURCE_ID).setData(selectedGeoJson)
      } else {
        map.addSource(SELECTED_SOURCE_ID, { type: 'geojson', data: selectedGeoJson })
        map.addLayer({
          id: SELECTED_FILL_ID,
          type: 'fill',
          source: SELECTED_SOURCE_ID,
          paint: { 'fill-color': '#F2C14E', 'fill-opacity': 0.12 },
        })
        map.addLayer({
          id: SELECTED_LINE_ID,
          type: 'line',
          source: SELECTED_SOURCE_ID,
          paint: { 'line-color': '#D88916', 'line-width': 3.5, 'line-opacity': 0.98 },
        })
      }
      if (wanted && features.length === 0) {
        console.warn(`Não encontrei a geometria de "${selectedMunicipality}" em /municipios. Confira as propriedades do GeoJSON.`)
      }
    } catch (error) {
      console.warn('Não foi possível destacar o município selecionado.', error)
    }
  }, [municipalitiesGeoJson, selectedMunicipality, mapReady])

  // Dataset publicado no MapTiler Cloud. Configure o ID em VITE_MAPTILER_RMS_DATASET_ID.
  useEffect(() => {
    const map = mapRef.current
    const datasetId = import.meta.env.VITE_MAPTILER_RMS_DATASET_ID
    const apiKey = import.meta.env.VITE_MAPTILER_KEY
    if (!map || !mapReady || !datasetId || !apiKey) return

    let cancelled = false
    async function loadRmsDataset() {
      try {
        const url = `https://api.maptiler.com/data/${encodeURIComponent(datasetId)}/features.json?key=${encodeURIComponent(apiKey)}`
        const response = await fetch(url)
        if (!response.ok) throw new Error(`MapTiler respondeu HTTP ${response.status}`)
        const geoJson = await response.json()
        if (cancelled || !geoJson?.features) return

        if (map.getSource(RMS_SOURCE_ID)) {
          map.getSource(RMS_SOURCE_ID).setData(geoJson)
          return
        }
        map.addSource(RMS_SOURCE_ID, { type: 'geojson', data: geoJson })
        map.addLayer({
          id: RMS_FILL_ID,
          type: 'fill',
          source: RMS_SOURCE_ID,
          filter: ['in', ['geometry-type'], ['literal', ['Polygon', 'MultiPolygon']]],
          layout: { visibility: selectedMunicipality ? 'none' : 'visible' },
          paint: { 'fill-color': '#13A89E', 'fill-opacity': 0.035 },
        })
        map.addLayer({
          id: RMS_LINE_ID,
          type: 'line',
          source: RMS_SOURCE_ID,
          layout: { visibility: selectedMunicipality ? 'none' : 'visible' },
          paint: { 'line-color': '#007E78', 'line-width': 2.1, 'line-opacity': 0.9 },
        })
      } catch (error) {
        console.warn('Não foi possível carregar o dataset da Região Metropolitana de Sorocaba no MapTiler. Confira o ID do dataset e a chave.', error)
      }
    }
    loadRmsDataset()
    return () => { cancelled = true }
  }, [mapReady, selectedMunicipality])

  // Camadas das instituições (criadas uma vez): grupos, contagem, pontos e anel da seleção.
  useEffect(() => {
    const map = mapRef.current
    if (!map || !mapReady) return undefined

    const empty = { type: 'FeatureCollection', features: [] }
    map.addSource(INST_SOURCE_ID, {
      type: 'geojson',
      data: empty,
      cluster: true,
      clusterRadius: 45,
      clusterMaxZoom: CLUSTER_MAX_ZOOM,
    })
    map.addSource(PICKED_SOURCE_ID, { type: 'geojson', data: empty })

    map.addLayer({
      id: INST_CLUSTER_LAYER_ID,
      type: 'circle',
      source: INST_SOURCE_ID,
      filter: ['has', 'point_count'],
      paint: {
        'circle-color': '#0E7C79',
        'circle-radius': ['step', ['get', 'point_count'], 16, 10, 20, 50, 26],
        'circle-stroke-width': 3,
        'circle-stroke-color': '#ffffff',
        'circle-opacity': 0.92,
      },
    })

    // O número dentro do grupo reaproveita a fonte de texto do estilo do mapa.
    const labelFont = map.getStyle()?.layers?.find((layer) => layer.type === 'symbol' && layer.layout?.['text-font'])?.layout['text-font']
    if (labelFont) {
      map.addLayer({
        id: INST_COUNT_LAYER_ID,
        type: 'symbol',
        source: INST_SOURCE_ID,
        filter: ['has', 'point_count'],
        layout: {
          'text-field': ['get', 'point_count_abbreviated'],
          'text-font': labelFont,
          'text-size': 13,
          'text-allow-overlap': true,
        },
        paint: { 'text-color': '#ffffff' },
      })
    }

    map.addLayer({
      id: INST_POINT_LAYER_ID,
      type: 'circle',
      source: INST_SOURCE_ID,
      filter: ['!', ['has', 'point_count']],
      paint: {
        'circle-color': ['get', 'cor'],
        'circle-radius': ['interpolate', ['linear'], ['zoom'], 9, 4, 13, 7, 16, 10],
        'circle-stroke-width': 2,
        'circle-stroke-color': '#ffffff',
      },
    })

    map.addLayer({
      id: PICKED_LAYER_ID,
      type: 'circle',
      source: PICKED_SOURCE_ID,
      paint: {
        'circle-radius': 15,
        'circle-color': 'rgba(0, 0, 0, 0)',
        'circle-stroke-width': 3.5,
        'circle-stroke-color': '#D88916',
      },
    })

    const popup = new Popup({ closeButton: false, closeOnClick: false, offset: 14, className: 'map-hover-popup' })

    const handlePointClick = (event) => {
      const feature = event.features?.[0]
      const institution = feature && byIdRef.current.get(feature.properties.id)
      if (institution) onSelectRef.current(institution)
    }
    const handleClusterClick = async (event) => {
      const feature = event.features?.[0]
      if (!feature) return
      try {
        const zoom = await map.getSource(INST_SOURCE_ID).getClusterExpansionZoom(feature.properties.cluster_id)
        map.easeTo({ center: feature.geometry.coordinates, zoom: Math.min(zoom + 0.3, 17), duration: 500 })
      } catch {
        map.easeTo({ center: feature.geometry.coordinates, zoom: map.getZoom() + 2, duration: 500 })
      }
    }
    const handlePointEnter = (event) => {
      map.getCanvas().style.cursor = 'pointer'
      const feature = event.features?.[0]
      if (feature) popup.setLngLat(feature.geometry.coordinates).setText(feature.properties.nome).addTo(map)
    }
    const handleClusterEnter = () => { map.getCanvas().style.cursor = 'pointer' }
    const handleLeave = () => {
      map.getCanvas().style.cursor = ''
      popup.remove()
    }

    map.on('click', INST_POINT_LAYER_ID, handlePointClick)
    map.on('click', INST_CLUSTER_LAYER_ID, handleClusterClick)
    map.on('mouseenter', INST_POINT_LAYER_ID, handlePointEnter)
    map.on('mouseleave', INST_POINT_LAYER_ID, handleLeave)
    map.on('mouseenter', INST_CLUSTER_LAYER_ID, handleClusterEnter)
    map.on('mouseleave', INST_CLUSTER_LAYER_ID, handleLeave)

    return () => {
      popup.remove()
      // Se o mapa já foi destruído (desmontagem), não há nada a limpar.
      if (mapRef.current !== map) return
      map.off('click', INST_POINT_LAYER_ID, handlePointClick)
      map.off('click', INST_CLUSTER_LAYER_ID, handleClusterClick)
      map.off('mouseenter', INST_POINT_LAYER_ID, handlePointEnter)
      map.off('mouseleave', INST_POINT_LAYER_ID, handleLeave)
      map.off('mouseenter', INST_CLUSTER_LAYER_ID, handleClusterEnter)
      map.off('mouseleave', INST_CLUSTER_LAYER_ID, handleLeave)
    }
  }, [mapReady])

  // Atualiza os dados quando a lista muda. Nada é destruído nem recriado: só setData.
  useEffect(() => {
    const map = mapRef.current
    const source = map && mapReady ? map.getSource(INST_SOURCE_ID) : null
    if (!source) return

    const features = []
    const byId = new globalThis.Map()
    const coordinates = []
    for (const institution of institutions) {
      const latitude = Number(institution.latitude)
      const longitude = Number(institution.longitude)
      if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) continue
      if (latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) continue

      const id = String(institution.id)
      byId.set(id, institution)
      coordinates.push([longitude, latitude])
      features.push({
        type: 'Feature',
        geometry: { type: 'Point', coordinates: [longitude, latitude] },
        properties: {
          id,
          nome: institution.nome || 'Instituição de ensino',
          cor: getMarkerColor(institution.tipo),
        },
      })
    }
    byIdRef.current = byId
    source.setData({ type: 'FeatureCollection', features })

    // Enquadra os pontos só quando muda o que foi carregado (município ou busca),
    // e não a cada filtro de rede/nível, para o mapa não "pular" enquanto o usuário filtra.
    if (!fitKey || fitKey === lastFitKeyRef.current || coordinates.length === 0) return
    lastFitKeyRef.current = fitKey
    if (coordinates.length === 1) {
      map.flyTo({ center: coordinates[0], zoom: FOCUS_ZOOM, duration: 600 })
      return
    }
    const lngs = coordinates.map((c) => c[0])
    const lats = coordinates.map((c) => c[1])
    map.fitBounds(
      [[Math.min(...lngs), Math.min(...lats)], [Math.max(...lngs), Math.max(...lats)]],
      { maxZoom: 14, duration: 600 },
    )
  }, [institutions, fitKey, mapReady])

  // Instituição selecionada: anel de destaque + voo até ela.
  useEffect(() => {
    const map = mapRef.current
    const source = map && mapReady ? map.getSource(PICKED_SOURCE_ID) : null
    if (!source) return

    const latitude = Number(selectedInstitution?.latitude)
    const longitude = Number(selectedInstitution?.longitude)
    if (!selectedInstitution || !Number.isFinite(latitude) || !Number.isFinite(longitude)) {
      source.setData({ type: 'FeatureCollection', features: [] })
      return
    }

    source.setData({
      type: 'FeatureCollection',
      features: [{ type: 'Feature', geometry: { type: 'Point', coordinates: [longitude, latitude] }, properties: {} }],
    })
    map.flyTo({
      center: [longitude, latitude],
      zoom: Math.max(map.getZoom(), FOCUS_ZOOM),
      duration: 700,
    })
  }, [selectedInstitution, mapReady])

  return <div className="map-stage" ref={containerRef} />
}

export default memo(MapView)
