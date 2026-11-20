import { useEffect, useRef } from 'react'
import * as THREE from 'three'

export default function ThreeBackground() {
  const containerRef = useRef(null)

  useEffect(() => {
    // Respect user preference
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return

    const container = containerRef.current
    if (!container) return

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 100)
    camera.position.z = 20

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })
    renderer.setSize(window.innerWidth, window.innerHeight)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    container.appendChild(renderer.domElement)

    // Soft lighting
    scene.add(new THREE.AmbientLight(0xe9f4ec, 0.8))
    const directional = new THREE.DirectionalLight(0xffffff, 0.6)
    directional.position.set(5, 10, 7)
    scene.add(directional)

    // Clay-like material using the brand green palette
    const clayMaterial = (color) =>
      new THREE.MeshStandardMaterial({
        color,
        roughness: 0.85,
        metalness: 0.05,
      })

    // Create floating shapes — distributed strictly on left and right flanks
    const shapes = []
    const geometries = [
      new THREE.SphereGeometry(1, 32, 32),
      new THREE.TorusGeometry(0.8, 0.35, 16, 32),
      new THREE.IcosahedronGeometry(0.9, 0),
      new THREE.OctahedronGeometry(0.8, 0),
      new THREE.CapsuleGeometry(0.5, 1, 8, 16),
    ]
    // Brand-derived pastel colors
    const colors = [0x185b42, 0x3a8060, 0x9bbfa9, 0xe9f4ec, 0x277b5d, 0xd9f4e4]

    // Scatter 8 shapes exclusively along the left (X <= -11) and right (X >= 11) flanks
    for (let i = 0; i < 8; i++) {
      const geometry = geometries[i % geometries.length]
      const material = clayMaterial(colors[i % colors.length])
      const mesh = new THREE.Mesh(geometry, material)

      const isLeft = i % 2 === 0
      const xSpan = 11 + Math.random() * 11 // Range: 11 to 22 units from center
      const posX = isLeft ? -xSpan : xSpan
      const posY = (Math.random() - 0.5) * 24
      const posZ = (Math.random() - 0.5) * 8 - 4

      mesh.position.set(posX, posY, posZ)
      mesh.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, 0)

      // Store animation parameters
      mesh.userData = {
        rotationSpeed: {
          x: (Math.random() - 0.5) * 0.004,
          y: (Math.random() - 0.5) * 0.004,
        },
        floatSpeed: 0.25 + Math.random() * 0.45,
        floatAmplitude: 0.35 + Math.random() * 0.5,
        initialY: posY,
        initialX: posX,
        driftSpeed: 0.2 + Math.random() * 0.3,
      }

      scene.add(mesh)
      shapes.push(mesh)
    }

    // Animation loop
    let animationId
    const clock = new THREE.Clock()

    function animate() {
      animationId = requestAnimationFrame(animate)
      const elapsed = clock.getElapsedTime()

      for (const shape of shapes) {
        const { rotationSpeed, floatSpeed, floatAmplitude, initialY, initialX, driftSpeed } = shape.userData
        shape.rotation.x += rotationSpeed.x
        shape.rotation.y += rotationSpeed.y
        shape.position.y = initialY + Math.sin(elapsed * floatSpeed) * floatAmplitude
        shape.position.x = initialX + Math.cos(elapsed * driftSpeed) * 0.25
      }

      renderer.render(scene, camera)
    }
    animate()

    // Handle resize
    function onResize() {
      camera.aspect = window.innerWidth / window.innerHeight
      camera.updateProjectionMatrix()
      renderer.setSize(window.innerWidth, window.innerHeight)
    }
    window.addEventListener('resize', onResize)

    // Cleanup
    return () => {
      cancelAnimationFrame(animationId)
      window.removeEventListener('resize', onResize)
      renderer.dispose()
      for (const shape of shapes) {
        shape.geometry.dispose()
        shape.material.dispose()
      }
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement)
      }
    }
  }, [])

  return <div ref={containerRef} className="three-bg" />
}
