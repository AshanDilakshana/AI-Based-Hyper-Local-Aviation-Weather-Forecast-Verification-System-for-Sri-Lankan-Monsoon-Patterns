import { Plane, ArrowRight, ArrowLeft, ArrowUp, ArrowDown } from 'lucide-react';

export default function AircraftVisualizer({ windDir, crosswind, headwind, status, runwayHeading }) {
  // Determine if it's a tailwind (negative headwind)
  const isTailwind = headwind < 0;
  const absHeadwind = Math.abs(headwind);
  
  // Calculate relative angle for the wind particles
  const relativeAngle = windDir - runwayHeading;
  const normalizedAngle = (relativeAngle + 360) % 360;
  const isFromRight = normalizedAngle > 0 && normalizedAngle < 180;

  // Determine Turbulence / Danger classes
  let turbulenceClass = '';
  if (status === 'WARNING') turbulenceClass = 'turbulence-warning';
  if (status === 'DANGER') turbulenceClass = 'turbulence-danger';

  // Crosswind color
  let crosswindColor = 'var(--safe)';
  if (crosswind > 15) crosswindColor = 'var(--warning)';
  if (crosswind > 25) crosswindColor = 'var(--danger)';

  // Generate random particles for the wind flow effect
  const particles = Array.from({ length: 12 }).map((_, i) => (
    <div 
      key={i} 
      className="particle" 
      style={{
        top: `${Math.random() * 100}%`,
        animationDelay: `${Math.random() * 2}s`
      }}
    ></div>
  ));

  return (
    <div className="glass-panel" style={{ marginTop: '24px', padding: '0', overflow: 'hidden' }}>
      <div style={{ padding: '24px', borderBottom: '1px solid rgba(255,255,255,0.05)', background: 'rgba(0,0,0,0.2)' }}>
        <h3>Aircraft Crosswind Visualizer</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Realistic vector analysis for Takeoff.</p>
      </div>

      <div className="visualizer-container">
        
        {/* Animated Wind Flow Background */}
        <div className="wind-particles" style={{ transform: `rotate(${relativeAngle}deg)` }}>
          {particles}
        </div>

        {/* Realistic Runway */}
        <div className="runway-realistic">
          <div className="runway-centerline"></div>
        </div>
        
        {/* Aircraft & Vectors Container */}
        <div className={`aircraft-container ${turbulenceClass}`}>
          <Plane size={80} color="#f8fafc" strokeWidth={1.5} style={{ transform: 'rotate(-45deg)' }} />

          {/* Headwind / Tailwind Vector */}
          <div className={`vector-arrow ${isTailwind ? 'vector-tailwind' : 'vector-headwind'}`}>
            {isTailwind ? <ArrowUp size={20} color="var(--danger)"/> : <ArrowDown size={20} color="var(--safe)"/>}
            <span style={{ marginTop: '4px', color: isTailwind ? 'var(--danger)' : 'var(--safe)' }}>
              {absHeadwind.toFixed(1)} Kts
            </span>
          </div>

          {/* Crosswind Vector */}
          {crosswind > 0 && (
            <div 
              className={`vector-arrow ${isFromRight ? 'vector-crosswind-right' : 'vector-crosswind-left'}`}
              style={{ color: crosswindColor, borderColor: crosswindColor }}
            >
              {isFromRight ? <ArrowLeft size={20} /> : <ArrowRight size={20} />}
              <span style={{ margin: '0 8px', color: crosswindColor }}>
                {crosswind.toFixed(1)} Kts
              </span>
            </div>
          )}
        </div>
        
      </div>
    </div>
  );
}
