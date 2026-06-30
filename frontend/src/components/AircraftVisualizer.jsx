import { Plane } from 'lucide-react';

export default function AircraftVisualizer({ windDir, crosswind, status, runwayHeading }) {
  // Calculate relative wind direction to the runway
  const relativeAngle = windDir - runwayHeading;
  
  // Determine wind effect color based on status
  let windClass = 'wind-safe';
  if (status === 'WARNING') windClass = 'wind-warning';
  if (status === 'DANGER') windClass = 'wind-danger';

  // Determine which side the wind is coming from to position the arrow
  // If relative angle is between 0 and 180, wind is coming from the right side of the plane
  // If relative angle is between 180 and 360 (or negative), wind is from the left.
  const normalizedAngle = (relativeAngle + 360) % 360;
  
  // Very basic visual mapping:
  const isFromRight = normalizedAngle > 0 && normalizedAngle < 180;
  
  return (
    <div className="glass-panel" style={{ marginTop: '24px', padding: '0', overflow: 'hidden' }}>
      <div style={{ padding: '24px' }}>
        <h3>Aircraft Crosswind Visualizer</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Visual representation of wind impact on RWY 04.</p>
      </div>

      <div className="visualizer-container">
        {/* The Runway */}
        <div className="runway"></div>
        
        {/* The Aircraft - Always points straight up (along runway) */}
        <div className="aircraft">
          <Plane size={80} color="#f8fafc" strokeWidth={1.5} style={{ transform: 'rotate(-45deg)' }} />
        </div>

        {/* The Wind Effect Arrow */}
        <div 
          className={`wind-arrow ${windClass}`}
          style={{ 
            transform: `rotate(${relativeAngle}deg)`,
            left: isFromRight ? '70%' : '10%',
            top: '40%'
          }}
        >
          {/* Using a unicode arrow or lucide icon */}
          💨
        </div>
      </div>
    </div>
  );
}
