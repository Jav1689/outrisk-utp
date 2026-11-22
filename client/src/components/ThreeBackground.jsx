import { useEffect, useRef } from 'react'
import * as THREE from 'three'

// Procedural organic leaf geometry with gentle beveling
function createLeafGeometry() {
  const shape = new THREE.Shape()
  shape.moveTo(0, -1.2) // Stem base
  // Right side curve to tip
  shape.bezierCurveTo(0.85, -0.5, 1.15, 0.5, 0, 1.4)
  // Left side curve back to stem base
  shape.bezierCurveTo(-1.15, 0.5, -0.85, -0.5, 0, -1.2)

  return new THREE.ExtrudeGeometry(shape, {
    depth: 0.08,
    bevelEnabled: true,
    bevelSegments: 3,
    steps: 1,
    bevelSize: 0.04,
    bevelThickness: 0.04,
  })
}

export default function ThreeBackground() {
  const containerRef = useRef(null)

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return

    const container = containerRef.current
    if (!container) return

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 100)
    camera.position.z = 20

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: false, powerPreference: 'high-performance' })
    renderer.setSize(window.innerWidth, window.innerHeight)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.25))
    container.appendChild(renderer.domElement)

    // Natural lighting for fresh outdoor ambiance
    scene.add(new THREE.AmbientLight(0xe9f4ec, 0.85))
    const sunLight = new THREE.DirectionalLight(0xffffff, 0.65)
    sunLight.position.set(6, 12, 8)
    scene.add(sunLight)

    // Lightweight Lambert material for organic botanical leaves (eliminates expensive PBR lighting)
    const leafMaterial = (color) =>
      new THREE.MeshLambertMaterial({
        color,
        side: THREE.DoubleSide,
      })

    const leafGeometry = createLeafGeometry()
    // Fresh botanical green palette (lush green, sage, mint, emerald)
    const leafColors = [0x185b42, 0x23805d, 0x3a8060, 0x277b5d, 0x4a9d77, 0x1d6a4d]

    const leaves = []
    // Scatter 10 leaves strictly along the left (X <= -11) and right (X >= 11) flanks
    for (let i = 0; i < 10; i++) {
      const material = leafMaterial(leafColors[i % leafColors.length])
      const mesh = new THREE.Mesh(leafGeometry, material)

      const isLeft = i % 2 === 0
      const xSpan = 11 + Math.random() * 10 // Range: 11 to 21 units from center
      const posX = isLeft ? -xSpan : xSpan
      const posY = (Math.random() - 0.5) * 26
      const posZ = (Math.random() - 0.5) * 8 - 4
      const scale = 0.75 + Math.random() * 0.45

      mesh.position.set(posX, posY, posZ)
      mesh.scale.set(scale, scale, scale)
      mesh.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, Math.random() * Math.PI)

      mesh.userData = {
        rotSpeedX: (Math.random() - 0.5) * 0.008,
        rotSpeedY: (Math.random() - 0.5) * 0.008,
        flutterSpeed: 1.2 + Math.random() * 1.0,
        swaySpeed: 0.6 + Math.random() * 0.8,
        fallSpeed: 0.018 + Math.random() * 0.022,
        initialX: posX,
      }

      scene.add(mesh)
      leaves.push(mesh)
    }

    // Animation loop: natural falling and fluttering leaves with visibility check
    let animationId
    const clock = new THREE.Clock()

    function animate() {
      if (document.hidden) {
        animationId = requestAnimationFrame(animate)
        return
      }

      animationId = requestAnimationFrame(animate)
      const elapsed = clock.getElapsedTime()

      for (const leaf of leaves) {
        const data = leaf.userData

        // Tumbling leaf flutter
        leaf.rotation.x += data.rotSpeedX
        leaf.rotation.y += data.rotSpeedY
        leaf.rotation.z = Math.sin(elapsed * data.flutterSpeed) * 0.35

        // Gentle downward drift
        leaf.position.y -= data.fallSpeed
        if (leaf.position.y < -14) {
          leaf.position.y = 14
        }

        // Sinusoidal breeze oscillation
        leaf.position.x = data.initialX + Math.sin(elapsed * data.swaySpeed) * 0.45
      }

      renderer.render(scene, camera)
    }
    animate()

    function onResize() {
      camera.aspect = window.innerWidth / window.innerHeight
      camera.updateProjectionMatrix()
      renderer.setSize(window.innerWidth, window.innerHeight)
    }
    window.addEventListener('resize', onResize)

    return () => {
      cancelAnimationFrame(animationId)
      window.removeEventListener('resize', onResize)
      renderer.dispose()
      leafGeometry.dispose()
      for (const leaf of leaves) {
        leaf.material.dispose()
      }
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement)
      }
    }
  }, [])

  return <div ref={containerRef} className="three-bg" />
}
