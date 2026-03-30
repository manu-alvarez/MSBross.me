import React from 'react';
import './NeuralOrb.css';

const NeuralOrb = ({ audioLevel = 0, orbState = 'ready' }) => {
  // Map orbState to CSS classes for different animations
  const getStateClass = () => {
    switch (orbState) {
      case 'listening': return 'orb-listening';
      case 'processing': return 'orb-processing';
      case 'speaking': return 'orb-speaking';
      case 'error': return 'orb-error';
      default: return 'orb-ready';
    }
  };

  // Scale influence by audio volume (0 to 1) multiplied aggressively for "speaking"
  const multiplier = orbState === 'speaking' ? 0.8 : 0.3;
  const dynamicScale = 1 + (audioLevel * multiplier);

  return (
    <div className={`neural-orb-container ${getStateClass()}`}>
      <div className="orb-layers" style={{ transform: `scale(${dynamicScale})` }}>
        {/* Outer energy plasma rings */}
        <div className="orb-layer energy-ring ring-1"></div>
        <div className="orb-layer energy-ring ring-2"></div>
        
        {/* Magnetic field effect */}
        <div className="orb-layer magnetic-field"></div>

        {/* Core glowing liquid */}
        <div className="orb-layer core-glow"></div>
        
        {/* Advanced Liquid Plasma Filters */}
        <svg className="orb-svg-filters">
          <defs>
            {/* Gooey Filter for Liquid Effect */}
            <filter id="gooey-plasma">
              <feGaussianBlur in="SourceGraphic" stdDeviation="15" result="blur" />
              <feColorMatrix in="blur" mode="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 30 -12" result="goo" />
              <feComposite in="SourceGraphic" in2="goo" operator="atop" />
            </filter>
            
            {/* Noise Filter for Magnetic Distortion */}
            <filter id="orb-noise">
              <feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="4" stitchTiles="stitch" />
              <feColorMatrix type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 20 -8" />
              <feDisplacementMap in="SourceGraphic" scale="25" />
            </filter>
          </defs>
        </svg>
      </div>
    </div>
  );
};

export default NeuralOrb;
