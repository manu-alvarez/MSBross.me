import PropTypes from 'prop-types';
import { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Points, PointMaterial, Float } from '@react-three/drei';
import * as THREE from 'three';

function ParticleSphere({ audioLevel = 0 }) {
  const ref = useRef();
  
  // Create a sphere of particles
  const positions = useMemo(() => {
    const count = 2000;
    const pos = new Float32Array(count * 3);
    
    for (let i = 0; i < count; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);
      const r = 1.5;
      
      pos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      pos[i * 3 + 2] = r * Math.cos(phi);
      

    }
    return pos;
  }, []);

  useFrame((state) => {
    const time = state.clock.getElapsedTime();
    
    // Rotate the sphere
    ref.current.rotation.y = time * 0.1;
    ref.current.rotation.z = time * 0.05;
    
    ref.current.scale.setScalar(1 + audioLevel * 0.5);
  });

  return (
    <group ref={ref}>
      <Points positions={positions} stride={3}>
        <PointMaterial
          transparent
          color="#00f2ff"
          size={0.05}
          sizeAttenuation={true}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </Points>
      
      {/* Inner Glow Core */}
      <mesh>
        <sphereGeometry args={[0.8, 32, 32]} />
        <meshBasicMaterial color="#00f2ff" transparent opacity={0.1 + audioLevel * 0.5} />
      </mesh>
    </group>
  );
}

export default function ParticleOrb({ audioLevel = 0 }) {
  return (
    <div className="particle-orb-container" style={{ width: '100%', height: '500px', position: 'relative' }}>
      <Canvas camera={{ position: [0, 0, 5], fov: 45 }}>
        <ambientLight intensity={0.5} />
        <Float speed={2} rotationIntensity={1} floatIntensity={1}>
          <ParticleSphere audioLevel={audioLevel} />
        </Float>
      </Canvas>
      
      {/* HUD Overlay inside Orb container if needed */}
      <div className="orb-overlay-text">
        <div className="neural-title">NEURAL INTERFACE V7.0</div>
      </div>
    </div>
  );
}

ParticleOrb.propTypes = {
  audioLevel: PropTypes.number,
};
ParticleSphere.propTypes = ParticleOrb.propTypes;
