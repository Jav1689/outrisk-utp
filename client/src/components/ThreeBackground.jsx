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

    // Create floating shapes — keep it minimal (6-8 shapes)
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

    for (let i = 0; i < 7; i++) {
      const geometry = geometries[i % geometries.length]
      const material = clayMaterial(colors[i % colors.length])
      const mesh = new THREE.Mesh(geometry, material)

      // Scatter across the viewport
      mesh.position.set(
        (Math.random() - 0.5) * 30,
        (Math.random() - 0.5) * 20,
        (Math.random() - 0.5) * 10 - 5,
      )
      mesh.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, 0)

      // Store animation parameters on the mesh
      mesh.userData = {
        rotationSpeed: { x: (Math.random() - 0.5) * 0.005, y: (Math.random() - 0.5) * 0.005 },
        floatSpeed: 0.3 + Math.random() * 0.5,
        floatAmplitude: 0.3 + Math.random() * 0.5,
        initialY: mesh.position.y,
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
        const { rotationSpeed, floatSpeed, floatAmplitude, initialY } = shape.userData
        shape.rotation.x += rotationSpeed.x
        shape.rotation.y += rotationSpeed.y
        shape.position.y = initialY + Math.sin(elapsed * floatSpeed) * floatAmplitude
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
