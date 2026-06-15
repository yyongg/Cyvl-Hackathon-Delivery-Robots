import { useEffect, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

const MAP_STYLE = 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json'
const SCORED_GEOJSON_URL = '/scored.geojson'
const SEGMENT_LAYERS = ['segments-base', 'segments-hover', 'segments-selected']

// Owns the MapLibre instance: loads the scored segments, wires up
// hover/select interactions, and exposes UI state to React.
export function useFeasibilityMap(mapContainer, activeTiers) {
  const map = useRef(null)
  const hoveredIdRef = useRef(null)
  const selectedIdRef = useRef(null)

  const [selectedFeature, setSelectedFeature] = useState(null)
  const [tooltip, setTooltip] = useState(null)
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  // ── Initialise the map once on mount ────────────────────────────────────
  useEffect(() => {
    if (map.current) return

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: MAP_STYLE,
      center: [-71.1097, 42.3876],
      zoom: 14,
      maxZoom: 19,
      minZoom: 11,
    })

    map.current.addControl(new maplibregl.NavigationControl({ visualizePitch: false }), 'top-right')
    map.current.addControl(new maplibregl.ScaleControl({ unit: 'metric' }), 'bottom-right')

    map.current.on('load', () => {
      fetch(SCORED_GEOJSON_URL)
        .then(r => r.json())
        .then(data => {
          const features = data.features
          const tiers = features.map(f => f.properties.tier)
          const scores = features.map(f => f.properties.composite_score).filter(s => s != null)
          const avg = scores.length ? (scores.reduce((a, b) => a + b, 0) / scores.length) : 0

          setStats({
            total: features.length,
            green: tiers.filter(t => t === 'green').length,
            yellow: tiers.filter(t => t === 'yellow').length,
            red: tiers.filter(t => t === 'red').length,
            avgScore: avg.toFixed(1),
          })

          map.current.addSource('segments', {
            type: 'geojson',
            data,
            generateId: true,
          })

          // Colored line layer (gradient by composite_score)
          map.current.addLayer({
            id: 'segments-base',
            type: 'line',
            source: 'segments',
            layout: { 'line-cap': 'round', 'line-join': 'round' },
            paint: {
              'line-color': [
                'interpolate', ['linear'], ['get', 'composite_score'],
                0, '#dc2626',
                40, '#f59e0b',
                70, '#22c55e',
                100, '#15803d',
              ],
              'line-width': ['interpolate', ['linear'], ['zoom'], 12, 1.5, 17, 5],
              'line-opacity': 0.85,
            },
          })

          // Hover highlight
          map.current.addLayer({
            id: 'segments-hover',
            type: 'line',
            source: 'segments',
            layout: { 'line-cap': 'round', 'line-join': 'round' },
            paint: {
              'line-color': '#ffffff',
              'line-width': ['interpolate', ['linear'], ['zoom'], 12, 3.5, 17, 9],
              'line-opacity': ['case', ['boolean', ['feature-state', 'hovered'], false], 0.7, 0],
            },
          })

          // Selected highlight
          map.current.addLayer({
            id: 'segments-selected',
            type: 'line',
            source: 'segments',
            layout: { 'line-cap': 'round', 'line-join': 'round' },
            paint: {
              'line-color': '#3b82f6',
              'line-width': ['interpolate', ['linear'], ['zoom'], 12, 4, 17, 10],
              'line-opacity': ['case', ['boolean', ['feature-state', 'selected'], false], 1, 0],
              'line-gap-width': ['interpolate', ['linear'], ['zoom'], 12, 1.5, 17, 5],
            },
          })

          setLoading(false)

          // Hover
          map.current.on('mousemove', 'segments-base', e => {
            map.current.getCanvas().style.cursor = 'pointer'
            if (e.features.length > 0) {
              if (hoveredIdRef.current !== null) {
                map.current.setFeatureState({ source: 'segments', id: hoveredIdRef.current }, { hovered: false })
              }
              hoveredIdRef.current = e.features[0].id
              map.current.setFeatureState({ source: 'segments', id: hoveredIdRef.current }, { hovered: true })
              setTooltip({
                x: e.originalEvent.clientX,
                y: e.originalEvent.clientY,
                props: e.features[0].properties,
              })
            }
          })

          map.current.on('mouseleave', 'segments-base', () => {
            map.current.getCanvas().style.cursor = ''
            if (hoveredIdRef.current !== null) {
              map.current.setFeatureState({ source: 'segments', id: hoveredIdRef.current }, { hovered: false })
              hoveredIdRef.current = null
            }
            setTooltip(null)
          })

          // Click on segment
          map.current.on('click', 'segments-base', e => {
            if (e.features.length > 0) {
              if (selectedIdRef.current !== null) {
                map.current.setFeatureState({ source: 'segments', id: selectedIdRef.current }, { selected: false })
              }
              selectedIdRef.current = e.features[0].id
              map.current.setFeatureState({ source: 'segments', id: selectedIdRef.current }, { selected: true })
              setSelectedFeature(e.features[0].properties)
            }
          })

          // Click on empty space → deselect
          map.current.on('click', e => {
            const hits = map.current.queryRenderedFeatures(e.point, { layers: ['segments-base'] })
            if (hits.length === 0) {
              if (selectedIdRef.current !== null) {
                map.current.setFeatureState({ source: 'segments', id: selectedIdRef.current }, { selected: false })
                selectedIdRef.current = null
              }
              setSelectedFeature(null)
            }
          })
        })
    })

    return () => {
      map.current?.remove()
      map.current = null
    }
  }, [mapContainer])

  // ── Apply the tier filter whenever the active set changes ────────────────
  useEffect(() => {
    if (!map.current) return
    const filter = activeTiers.size === 3
      ? null
      : ['in', ['get', 'tier'], ['literal', [...activeTiers]]]
    for (const layer of SEGMENT_LAYERS) {
      if (map.current.getLayer(layer)) {
        map.current.setFilter(layer, filter)
      }
    }
  }, [activeTiers])

  // Clears the current selection (and its map highlight).
  const clearSelection = () => {
    if (selectedIdRef.current !== null && map.current) {
      map.current.setFeatureState({ source: 'segments', id: selectedIdRef.current }, { selected: false })
      selectedIdRef.current = null
    }
    setSelectedFeature(null)
  }

  return { selectedFeature, tooltip, stats, loading, clearSelection }
}
