import { useRef, useState, useCallback } from 'react'
import './App.css'

import Sidebar from './components/Sidebar'
import Tooltip from './components/Tooltip'
import DetailPanel from './components/DetailPanel'
import { useFeasibilityMap } from './hooks/useFeasibilityMap'

export default function App() {
  const mapContainer = useRef(null)
  const [activeTiers, setActiveTiers] = useState(new Set(['green', 'yellow', 'red']))

  const { selectedFeature, tooltip, stats, loading, clearSelection } =
    useFeasibilityMap(mapContainer, activeTiers)

  const toggleTier = useCallback(tier => {
    setActiveTiers(prev => {
      const next = new Set(prev)
      if (next.has(tier)) {
        if (next.size > 1) next.delete(tier)
      } else {
        next.add(tier)
      }
      return next
    })
  }, [])

  return (
    <div className="app">
      <Sidebar
        loading={loading}
        stats={stats}
        activeTiers={activeTiers}
        onToggleTier={toggleTier}
      />

      <div ref={mapContainer} className="map-container" />

      {tooltip && <Tooltip tooltip={tooltip} />}

      {selectedFeature && (
        <DetailPanel feature={selectedFeature} onClose={clearSelection} />
      )}
    </div>
  )
}
