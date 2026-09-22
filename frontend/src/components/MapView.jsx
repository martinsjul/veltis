import { useEffect, useRef } from 'react'
import { Map, Marker, config, MapStyle } from '@maptiler/sdk'
import '@maptiler/sdk/dist/maptiler-sdk.css'
import { getMarkerColor } from '../utils/institution'

const DEFAULT_CENTER = [-47.4521, -23.5015]
const DEFAULT_ZOOM = 10

export default function MapView({ institutions, selectedInstitution, onSelect }) {
  const containerRef = useRef(null)
  const mapRef = useRef(null)
  const markersRef = useRef([])

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return

    const apiKey = import.meta.env.VITE_MAPTILER_KEY
    if (!apiKey) {
      console.warn('VITE_MAPTILER_KEY não configurada. O mapa não poderá ser inicializado.')
      return
    }

    config.apiKey = apiKey

    const map = new Map({
      container: containerRef.current,
      style: MapStyle.STREETS,
      center: DEFAULT_CENTER,
      zoom: DEFAULT_ZOOM,
      minZoom: 8,
      maxZoom: 18,
      maxBounds: [
        [-48.35, -24.25],
        [-46.75, -22.75],
      ],
    })

    mapRef.current = map

    return () => {
      markersRef.current.forEach((marker) => marker.remove())
      markersRef.current = []
      map.remove()
      mapRef.current = null
    }
  }, [])

  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    markersRef.current.forEach((marker) => marker.remove())
    markersRef.current = []

    for (const institution of institutions) {
      if (institution.latitude == null || institution.longitude == null) continue

      const element = document.createElement('button')
      element.type = 'button'
      element.className = 'map-marker'
      element.title = institution.nome
      element.style.setProperty('--marker-color', getMarkerColor(institution.tipo))
      element.innerHTML = '<span></span>'

      element.addEventListener('click', (event) => {
        event.stopPropagation()
        onSelect(institution)
      })

      const marker = new Marker({ element, anchor: 'bottom' })
        .setLngLat([institution.longitude, institution.latitude])
        .addTo(map)

      markersRef.current.push(marker)
    }
  }, [institutions, onSelect])

  useEffect(() => {
    const map = mapRef.current
    if (!map || !selectedInstitution) return
    if (selectedInstitution.latitude == null || selectedInstitution.longitude == null) return

    map.flyTo({
      center: [selectedInstitution.longitude, selectedInstitution.latitude],
      zoom: Math.max(map.getZoom(), 13),
      duration: 700,
    })
  }, [selectedInstitution])

  return <div className="map-stage" ref={containerRef} />
}
