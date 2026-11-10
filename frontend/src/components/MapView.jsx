import { useEffect, useRef, useState } from 'react'
import { Map, Marker, config, MapStyle } from '@maptiler/sdk'
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

export default function MapView({ institutions, municipalitiesGeoJson, selectedMunicipality, selectedInstitution, onSelect }) {
  const containerRef = useRef(null)
  const mapRef = useRef(null)
  const markersRef = useRef([])
  const [mapReady, setMapReady] = useState(false)

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
      markersRef.current.forEach((marker) => marker.remove())
      markersRef.current = []
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

  useEffect(() => {
    const map = mapRef.current
    if (!map || !mapReady) return

    // Ao abrir o site não há instituições carregadas (só as malhas municipais).
    // Os pontos aparecem quando um município é escolhido ou uma busca retorna resultados.
    markersRef.current.forEach((marker) => marker.remove())
    markersRef.current = []

    const bounds = []
    for (const institution of institutions) {
      const latitude = Number(institution.latitude)
      const longitude = Number(institution.longitude)
      if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) continue
      if (latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) continue

      const element = document.createElement('button')
      element.type = 'button'
      element.className = 'map-marker'
      element.title = institution.nome || 'Instituição de ensino'
      element.setAttribute('aria-label', `Ver detalhes de ${institution.nome || 'instituição'}`)
      element.style.setProperty('--marker-color', getMarkerColor(institution.tipo))
      element.innerHTML = '<span class="map-marker-pin"><i></i></span>'

      element.addEventListener('click', (event) => {
        event.stopPropagation()
        onSelect(institution)
      })

      const marker = new Marker({ element, anchor: 'bottom' })
        .setLngLat([longitude, latitude])
        .addTo(map)

      markersRef.current.push(marker)
      bounds.push([longitude, latitude])
    }

    // Enquadra os pontos exibidos (respeitando o padding da sidebar).
    if (bounds.length === 1) {
      map.flyTo({ center: bounds[0], zoom: Math.max(map.getZoom(), 13), duration: 600 })
    } else if (bounds.length > 1) {
      const lngs = bounds.map((b) => b[0])
      const lats = bounds.map((b) => b[1])
      map.fitBounds(
        [[Math.min(...lngs), Math.min(...lats)], [Math.max(...lngs), Math.max(...lats)]],
        { maxZoom: 14, duration: 600 },
      )
    }
  }, [institutions, onSelect, mapReady])

  useEffect(() => {
    const map = mapRef.current
    if (!map || !mapReady || !selectedInstitution) return
    const latitude = Number(selectedInstitution.latitude)
    const longitude = Number(selectedInstitution.longitude)
    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return

    map.flyTo({
      center: [longitude, latitude],
      zoom: Math.max(map.getZoom(), 13),
      duration: 700,
    })
  }, [selectedInstitution, mapReady])

  return <div className="map-stage" ref={containerRef} />
}
