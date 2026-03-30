import { useEffect, useRef, memo } from 'react';
import * as THREE from 'three';

/**
 * LIVING ORB 3.0 — The Hex-Plasma Singularity
 * A biometric, sentient energy entity with THREE.js custom shaders.
 * Props match NeuralOrb interface for easy switching:
 *   audioLevel (0-1), orbState ('ready'|'listening'|'processing'|'speaking'|'error')
 */
function Orb3D({ audioLevel = 0, orbState = 'ready' }) {
  const emotionColor = orbState === 'error' ? 0xff3c3c 
    : orbState === 'listening' ? 0xff3c3c 
    : orbState === 'processing' ? 0x3b82f6 
    : 0xa855f7;
  const mountRef = useRef(null);

  // ── SHADERS ──

  const vertexShader = `
    varying vec2 vUv;
    varying vec3 vNormal;
    varying vec3 vPosition;
    uniform float uTime;
    uniform float uIntensity;
    uniform float uVolume;

    // Simplex noise (simplified)
    vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
    vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
    vec4 permute(vec4 x) { return mod289(((x*34.0)+1.0)*x); }
    vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }
    float snoise(vec3 v) {
      const vec2  C = vec2(1.0/6.0, 1.0/3.0) ;
      const vec4  D = vec4(0.0, 0.5, 1.0, 2.0);
      vec3 i  = floor(v + dot(v, C.yyy) );
      vec3 x0 =   v - i + dot(i, C.xxx) ;
      vec3 g = step(x0.yzx, x0.xyz);
      vec3 l = 1.0 - g;
      vec3 i1 = min( g.xyz, l.zxy );
      vec3 i2 = max( g.xyz, l.zxy );
      vec3 x1 = x0 - i1 + C.xxx;
      vec3 x2 = x0 - i2 + C.yyy;
      vec3 x3 = x0 - D.yyy;
      i = mod289(i);
      vec4 p = permute( permute( permute(
                i.z + vec4(0.0, i1.z, i2.z, 1.0 ))
              + i.y + vec4(0.0, i1.y, i2.y, 1.0 ))
              + i.x + vec4(0.0, i1.x, i2.x, 1.0 ));
      float n_ = 0.142857142857;
      vec3  ns = n_ * D.wyz - D.xzx;
      vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
      vec4 x_ = floor(j * ns.z);
      vec4 y_ = floor(j - 7.0 * x_ );
      vec4 x = x_ * ns.x + ns.yyyy;
      vec4 y = y_ * ns.x + ns.yyyy;
      vec4 h = 1.0 - abs(x) - abs(y);
      vec4 b0 = vec4( x.xy, y.xy );
      vec4 b1 = vec4( x.zw, y.zw );
      vec4 s0 = floor(b0)*2.0 + 1.0;
      vec4 s1 = floor(b1)*2.0 + 1.0;
      vec4 sh = -step(h, vec4(0.0));
      vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy ;
      vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww ;
      vec3 p0 = vec3(a0.xy,h.x);
      vec3 p1 = vec3(a0.zw,h.y);
      vec3 p2 = vec3(a1.xy,h.z);
      vec3 p3 = vec3(a1.zw,h.w);
      vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2, p2), dot(p3,p3)));
      p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
      vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
      m = m * m;
      return 42.0 * dot( m*m, vec4( dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3) ) );
    }

    void main() {
      vUv = uv;
      vNormal = normal;
      vPosition = position;
      
      // Breathing & Displacement
      float breathing = sin(uTime * 1.5) * 0.02;
      float noise = snoise(normal * 2.0 + uTime * 0.4);
      float displacement = breathing + (noise * uIntensity) + (uVolume * 0.25 * noise);
      
      vec3 newPosition = position + normal * displacement;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(newPosition, 1.0);
    }
  `;

  const fragmentShader = `
    varying vec2 vUv;
    varying vec3 vNormal;
    varying vec3 vPosition;
    uniform vec3 uColor;
    uniform float uTime;
    uniform float uIntensity;
    uniform float uVolume;
    uniform int uState; // 0: Idle, 1: Speaking, 2: Listening, 3: Thinking

    // Hexagon math
    float hexDist(vec2 p) {
      p = abs(p);
      return max(dot(p, vec2(0.5, 0.866025)), p.x);
    }

    vec2 hexCoords(vec2 uv) {
      vec2 r = vec2(1.0, 1.73);
      vec2 h = r * 0.5;
      vec2 a = mod(uv, r) - h;
      vec2 b = mod(uv - h, r) - h;
      return dot(a, a) < dot(b, b) ? a : b;
    }

    void main() {
      // 1. Base Energy & Glow
      float fresnel = pow(1.0 - dot(vNormal, vec3(0, 0, 1.0)), 3.0);
      vec3 color = uColor;

      // 2. Interior Plasma (Nebula Effect)
      float noise = sin(vPosition.x * 5.0 + uTime) * cos(vPosition.y * 5.0 - uTime) * 0.5 + 0.5;
      vec3 plasma = mix(color * 0.5, vec3(1.0), noise * uIntensity);
      
      // 3. Hexagonal Grid
      vec2 hc = hexCoords(vUv * 20.0 + uTime * 0.05);
      float dist = hexDist(hc);
      float grid = smoothstep(0.4, 0.45, dist);
      float gridStrength = (uState == 3) ? 0.8 : 0.2; // Intensify on thinking
      
      vec3 finalColor = mix(plasma, color * 2.0, grid * gridStrength);
      
      // 4. Fresnel & Volume Glow
      finalColor += color * fresnel * 1.2;
      
      // 5. Pulsing Alpha
      float alpha = 0.8 + sin(uTime * 2.0) * 0.1;
      
      gl_FragColor = vec4(finalColor, alpha);
    }
  `;

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const w = container.clientWidth;
    const h = container.clientHeight;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, w / h, 0.1, 100);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(w, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // ── GEOMETRY LAYERS ──

    // 1. The Core (Plasma & Hex)
    const coreGeo = new THREE.SphereGeometry(0.7, 128, 128);
    const coreUniforms = {
      uTime: { value: 0 },
      uColor: { value: new THREE.Color(emotionColor) },
      uIntensity: { value: 0.2 },
      uVolume: { value: 0 },
      uState: { value: 0 }
    };
    const coreMat = new THREE.ShaderMaterial({
      vertexShader: `
        varying vec2 vUv;
        varying vec3 vNormal;
        varying vec3 vPosition;
        uniform float uTime;
        uniform float uIntensity;
        uniform float uVolume;

        // Simplex noise (simplified)
        vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
        vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
        vec4 permute(vec4 x) { return mod289(((x*34.0)+1.0)*x); }
        vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }
        float snoise(vec3 v) {
          const vec2  C = vec2(1.0/6.0, 1.0/3.0) ;
          const vec4  D = vec4(0.0, 0.5, 1.0, 2.0);
          vec3 i  = floor(v + dot(v, C.yyy) );
          vec3 x0 =   v - i + dot(i, C.xxx) ;
          vec3 g = step(x0.yzx, x0.xyz);
          vec3 l = 1.0 - g;
          vec3 i1 = min( g.xyz, l.zxy );
          vec3 i2 = max( g.xyz, l.zxy );
          vec3 x1 = x0 - i1 + C.xxx;
          vec3 x2 = x0 - i2 + C.yyy;
          vec3 x3 = x0 - D.yyy;
          i = mod289(i);
          vec4 p = permute( permute( permute(
                    i.z + vec4(0.0, i1.z, i2.z, 1.0 ))
                  + i.y + vec4(0.0, i1.y, i2.y, 1.0 ))
                  + i.x + vec4(0.0, i1.x, i2.x, 1.0 ));
          float n_ = 0.142857142857;
          vec3  ns = n_ * D.wyz - D.xzx;
          vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
          vec4 x_ = floor(j * ns.z);
          vec4 y_ = floor(j - 7.0 * x_ );
          vec4 x = x_ * ns.x + ns.yyyy;
          vec4 y = y_ * ns.x + ns.yyyy;
          vec4 h = 1.0 - abs(x) - abs(y);
          vec4 b0 = vec4( x.xy, y.xy );
          vec4 b1 = vec4( x.zw, y.zw );
          vec4 s0 = floor(b0)*2.0 + 1.0;
          vec4 s1 = floor(b1)*2.0 + 1.0;
          vec4 sh = -step(h, vec4(0.0));
          vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy ;
          vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww ;
          vec3 p0 = vec3(a0.xy,h.x);
          vec3 p1 = vec3(a0.zw,h.y);
          vec3 p2 = vec3(a1.xy,h.z);
          vec3 p3 = vec3(a1.zw,h.w);
          vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2, p2), dot(p3,p3)));
          p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
          vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
          m = m * m;
          return 42.0 * dot( m*m, vec4( dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3) ) );
        }

        void main() {
          vUv = uv;
          vNormal = normal;
          vPosition = position;
          
          // Breathing & Displacement
          float breathing = sin(uTime * 1.5) * 0.02;
          float noise = snoise(normal * (2.0 + uVolume * 2.0) + uTime * 0.4);
          float displacement = breathing + (noise * uIntensity * 1.5) + (uVolume * 0.4 * noise);
          
          vec3 newPosition = position + normal * displacement;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(newPosition, 1.0);
        }
      `,
      fragmentShader: `
        varying vec2 vUv;
        varying vec3 vNormal;
        varying vec3 vPosition;
        uniform vec3 uColor;
        uniform float uTime;
        uniform float uIntensity;
        uniform float uVolume;
        uniform int uState; // 0: Idle, 1: Speaking, 2: Listening, 3: Thinking

        // Hexagon math
        float hexDist(vec2 p) {
          p = abs(p);
          return max(dot(p, vec2(0.5, 0.866025)), p.x);
        }

        vec2 hexCoords(vec2 uv) {
          vec2 r = vec2(1.0, 1.73);
          vec2 h = r * 0.5;
          vec2 a = mod(uv, r) - h;
          vec2 b = mod(uv - h, r) - h;
          return dot(a, a) < dot(b, b) ? a : b;
        }

        void main() {
          // 1. Base Energy & Glow
          float fresnel = pow(1.0 - dot(vNormal, vec3(0, 0, 1.0)), 2.5);
          vec3 color = uColor;

          // 2. Interior Plasma (Nebula Effect) - Higher frequency with volume
          float noise = sin(vPosition.x * (5.0 + uVolume * 10.0) + uTime) * cos(vPosition.y * (5.0 + uVolume * 10.0) - uTime) * 0.5 + 0.5;
          vec3 plasma = mix(color * 0.3, vec3(1.0), noise * (uIntensity + uVolume * 0.5));
          
          // 3. Hexagonal Grid - Pulsing grid lines
          vec2 hc = hexCoords(vUv * (20.0 + uVolume * 5.0) + uTime * 0.05);
          float dist = hexDist(hc);
          float grid = smoothstep(0.35, 0.45, dist);
          float gridStrength = (uState == 3) ? 0.8 : (0.2 + uVolume * 0.6);
          
          vec3 finalColor = mix(plasma, color * 2.0, grid * gridStrength);
          
          // 4. Fresnel & Volume Glow
          finalColor += color * fresnel * (1.2 + uVolume * 2.0);
          
          // 5. Pulsing Alpha
          float alpha = 0.8 + sin(uTime * 2.0) * 0.1 + uVolume * 0.2;
          
          gl_FragColor = vec4(finalColor, alpha);
        }
      `,
      uniforms: coreUniforms,
      transparent: true,
      side: THREE.DoubleSide,
    });
    const core = new THREE.Mesh(coreGeo, coreMat);
    scene.add(core);

    // 2. The Glass Shell (Refraction & Protection)
    const shellGeo = new THREE.SphereGeometry(1.0, 64, 64);
    const shellMat = new THREE.MeshPhysicalMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.15,
      transmission: 0.9,
      thickness: 2.0,
      roughness: 0.05,
      ior: 1.45,
      clearcoat: 1.0,
      attenuationColor: new THREE.Color(emotionColor),
      attenuationDistance: 0.5
    });
    const shell = new THREE.Mesh(shellGeo, shellMat);
    scene.add(shell);

    // 3. Energy Rings (Sleek interaction)
    const ringGeo = new THREE.TorusGeometry(1.2, 0.01, 16, 100);
    const ringMat = new THREE.MeshBasicMaterial({
      color: emotionColor,
      transparent: true,
      opacity: 0.3,
      blending: THREE.AdditiveBlending
    });
    const ring1 = new THREE.Mesh(ringGeo, ringMat);
    const ring2 = new THREE.Mesh(ringGeo, ringMat);
    ring2.rotation.x = Math.PI / 2;
    scene.add(ring1);
    scene.add(ring2);

    camera.position.z = 4;

    const clock = new THREE.Clock();
    let animId;

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const t = clock.getElapsedTime();

      // Update Universal Params
      coreUniforms.uTime.value = t;
      coreUniforms.uColor.value.lerp(new THREE.Color(emotionColor), 0.05);
      ringMat.color.lerp(new THREE.Color(emotionColor), 0.05);

      // Organic Rotation
      core.rotation.y = t * 0.15;
      core.rotation.z = t * 0.1;
      shell.rotation.y = -t * 0.05;
      
      ring1.rotation.z = t * 0.2;
      ring2.rotation.z = -t * 0.3;

      // State Mapping
      let stateVal = 0;
      if (orbState === 'speaking') stateVal = 1;
      else if (orbState === 'listening') stateVal = 2;
      else if (orbState === 'processing') stateVal = 3;
      coreUniforms.uState.value = stateVal;

      // Dynamics — audioLevel is already 0-1 normalized
      if (orbState === 'speaking') {
        const v = audioLevel;
        coreUniforms.uIntensity.value = 0.4 + v;
        coreUniforms.uVolume.value = v;
        shell.scale.setScalar(1 + v * 0.3);
        ring1.scale.setScalar(1 + v * 0.6);
        ring2.scale.setScalar(1 + v * 0.6);
        
        ring1.rotation.x = Math.sin(t * 10) * v * 0.5;
        ring2.rotation.y = Math.cos(t * 12) * v * 0.5;
      } else if (orbState === 'listening') {
        coreUniforms.uIntensity.value = 0.5 + Math.sin(t * 10) * 0.2;
        shell.scale.setScalar(1.05 + Math.sin(t * 5) * 0.02);
      } else {
        coreUniforms.uIntensity.value = 0.2 + Math.sin(t * 0.5) * 0.1;
        coreUniforms.uVolume.value = 0;
        shell.scale.setScalar(THREE.MathUtils.lerp(shell.scale.x, 1, 0.1));
      }

      renderer.render(scene, camera);
    };

    animate();

    const onResize = () => {
      const nw = container.clientWidth;
      const nh = container.clientHeight;
      camera.aspect = nw / nh;
      camera.updateProjectionMatrix();
      renderer.setSize(nw, nh);
    };
    window.addEventListener('resize', onResize);

    return () => {
      window.removeEventListener('resize', onResize);
      cancelAnimationFrame(animId);
      if (container && renderer.domElement) container.removeChild(renderer.domElement);
      renderer.dispose();
    };
  }, [orbState, emotionColor, audioLevel]);

  return <div ref={mountRef} className="w-full h-full" style={{ minHeight: '300px' }} />;
}

export default memo(Orb3D);
