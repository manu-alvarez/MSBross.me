import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Points, PointMaterial, Float } from '@react-three/drei';
import * as THREE from 'three';

function ParticleSphere({ audioLevel = 0, emotion = 'neutral' }) {
  const ref = useRef();
  
  // Create a sphere of particles
  const [positions, colors] = useMemo(() => {
    const count = 2000;
    const pos = new Float32Array(count * 3);
    const cols = new Float32Array(count * 3);
    
    for (let i = 0; i < count; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);
      const r = 1.5;
      
      pos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      pos[i * 3 + 2] = r * Math.cos(phi);
      
      // Initial color (cyan/blue)
      cols[i * 3] = 0.0;
      cols[i * 3 + 1] = 0.8;
      cols[i * 3 + 2] = 1.0;
    }
    return [pos, cols];
  }, []);

  useFrame((state) => {
    const time = state.clock.getElapsedTime();
    
    // Rotate the sphere
    ref.current.rotation.y = time * 0.1;
    ref.current.rotation.z = time * 0.05;
    
    // Animate particles based on audio level
    const positions = ref.current.geometry.attributes.position.array;
    for (let i = 0; i < positions.length / 3; i++) {
      const ix = i * 3;
      const iy = i * 3 + 1;
      const iz = i * 3 + 2;
      
      const x = positions[ix];
      const y = positions[iy];
      const z = positions[iz];
      
      // Calculate distance from center
      const d = Math.sqrt(x*x + y*y + z*z);
      const factor = 1 + (Math.sin(time * 2 + d * 5) * 0.02) + (audioLevel * 0.5);
      
      // We don't want to move them permanently, just oscillate
      // So we use a base radius
      const baseR = 1.5;
      const currentR = baseR * factor;
      
      const ratio = currentR / d;
      // Note: this is a simple animation, for performance we'd use a shader
      // but let's stick to this for now to see the result.
    }
    // ref.current.geometry.attributes.position.needsUpdate = true;
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

export default function ParticleOrb({ audioLevel = 0, emotion = 'neutral' }) {
  return (
    <div className="particle-orb-container" style={{ width: '100%', height: '500px', position: 'relative' }}>
      <Canvas camera={{ position: [0, 0, 5], fov: 45 }}>
        <ambientLight intensity={0.5} />
        <Float speed={2} rotationIntensity={1} floatIntensity={1}>
          <ParticleSphere audioLevel={audioLevel} emotion={emotion} />
        </Float>
      </Canvas>
      
      {/* HUD Overlay inside Orb container if needed */}
      <div className="orb-overlay-text">
        <div className="neural-title">NEURAL INTERFACE V7.0</div>
      </div>
    </div>
  );
}
