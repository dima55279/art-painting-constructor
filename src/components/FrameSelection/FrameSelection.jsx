import React, { useRef, Suspense, useState } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { selectFrame } from '../../store/slices/frameSlice'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { OrbitControls, Center } from '@react-three/drei'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader'
import * as THREE from 'three'
import styles from './FrameSelection.module.css'

import cowboyModel from '../../frames/cowboy.glb'
import pumpkinModel from '../../frames/pumpkin.glb'
import flowersModel from '../../frames/flowers.glb'
import christmasModel from '../../frames/christmas.glb'
import seaModel from '../../frames/sea.glb'
import popartModel from '../../frames/cowboy.glb'
import woodModel from '../../frames/cowboy.glb'
import metalModel from '../../frames/cowboy.glb'
import goldModel from '../../frames/cowboy.glb'

import cowboyPreview from '../../images/frames/cowboy.png'
import pumpkinPreview from '../../images/frames/pumpkin.png'
import flowersPreview from '../../images/frames/flowers.png'
import christmasPreview from '../../images/frames/christmas.png'
import seaPreview from '../../images/frames/sea.png'
import popartPreview from '../../images/frames/cowboy.png'
import woodPreview from '../../images/frames/cowboy.png'
import metalPreview from '../../images/frames/cowboy.png'
import goldPreview from '../../images/frames/cowboy.png'
import defaultPreview from '../../images/frames/cowboy.png'

const CameraController = ({ model }) => {
  const { camera, controls } = useThree()
  
  React.useEffect(() => {
    if (model && controls) {

      const box = new THREE.Box3().setFromObject(model)
      const center = box.getCenter(new THREE.Vector3())
      const size = box.getSize(new THREE.Vector3())

      const maxDim = Math.max(size.x, size.y, size.z)
      const fov = camera.fov * (Math.PI / 180)
      let cameraDistance = maxDim / (2 * Math.tan(fov / 2))

      cameraDistance *= 1.5
      
      camera.position.set(0, 0, cameraDistance)
      controls.target.set(center.x, center.y, center.z)
      controls.update()
    }
  }, [model, camera, controls])
  
  return null
}

const FrameModel = ({ modelUrl }) => {
  const [model, setModel] = useState(null)
  const groupRef = useRef()
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  React.useEffect(() => {
    const loadModel = async () => {
      try {
        setLoading(true)
        setError(null)

        const loader = new GLTFLoader()
        const gltf = await loader.loadAsync(modelUrl)
        
        console.log('GLB model loaded:', gltf)
        
        gltf.scene.traverse((child) => {
          if (child.isMesh) {
            child.material = new THREE.MeshStandardMaterial({
              color: child.material?.color || '#cccccc',
              roughness: 0.7,
              metalness: 0.3,
              side: THREE.DoubleSide
            })
            child.castShadow = true
            child.receiveShadow = true
          }
        })
        
        setModel(gltf.scene)
      } catch (err) {
        console.error('Error loading model:', err)
        setError('Ошибка загрузки модели')
      } finally {
        setLoading(false)
      }
    }

    if (modelUrl) {
      loadModel()
    }
  }, [modelUrl])

  useFrame(() => {
    if (groupRef.current && model) {
      groupRef.current.rotation.y += 0.005
    }
  })

  if (loading) {
    return (
      <mesh>
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial color="gray" wireframe />
      </mesh>
    )
  }

  if (error || !model) {
    return (
      <mesh>
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial color="red" />
      </mesh>
    )
  }

  return (
    <group ref={groupRef}>
      <Center>
        <primitive 
          object={model} 
          scale={1}
          position={[0, 0, 0]}
        />
      </Center>
      <CameraController model={model} />
    </group>
  )
}

const ModelFallback = () => {
  const meshRef = useRef()
  
  useFrame(() => {
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.01
    }
  })

  return (
    <Center>
      <mesh ref={meshRef}>
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial color="#666666" wireframe />
      </mesh>
    </Center>
  )
}

const SimpleFrame = ({ type }) => {
  const meshRef = useRef()
  
  useFrame(() => {
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.005
    }
  })

  let geometry
  let scale = 0.8
  let color = "#cccccc"

  switch(type) {
    case 'cowboy':
      geometry = <ringGeometry args={[1.2, 1.5, 32]} />
      color = "#8B4513"
      break
    case 'pumpkin':
      geometry = <ringGeometry args={[1.2, 1.5, 32]} />
      color = "#228B22"
      break
    case 'flowers':
      geometry = <torusGeometry args={[1, 0.1, 16, 100]} />
      color = "#DAA520"
      break
    case 'christmas':
      geometry = <circleGeometry args={[1.3, 32]} />
      color = "#FFFFFF"
      break
    case 'sea':
      geometry = <ringGeometry args={[1, 1.4, 32]} />
      color = "#FFD700"
      break
    case 'popart':
      geometry = <cylinderGeometry args={[1, 1.3, 0.15, 8]} />
      color = "#FF69B4"
      break
    case 'wood':
      geometry = <boxGeometry args={[1.5, 1.5, 0.2]} />
      color = "#8B4513"
      break
    case 'metal':
      geometry = <ringGeometry args={[1.1, 1.3, 32]} />
      color = "#708090"
      break
    case 'gold':
      geometry = <ringGeometry args={[1, 1.4, 32]} />
      color = "#FFD700"
      break
    default:
      geometry = <ringGeometry args={[1.2, 1.5, 32]} />
  }

  return (
    <Center>
      <mesh ref={meshRef} scale={scale}>
        {geometry}
        <meshStandardMaterial 
          color={color}
          roughness={0.7}
          metalness={0.3}
          wireframe={false}
        />
      </mesh>
    </Center>
  )
}

const FrameSelection = () => {
  const dispatch = useDispatch()
  const { frames, selectedFrame } = useSelector((state) => state.frame)
  const { isDark } = useSelector((state) => state.theme)

  const framesWithPreview = frames.map(frame => ({
    ...frame,
    previewImage: getFramePreview(frame.id),
    modelUrl: getFrameModelUrl(frame.id),
    type: getFrameType(frame.id),
  }))

  const handleFrameSelect = (frameId) => {
    dispatch(selectFrame(frameId))
  }

  const themeClass = isDark ? styles.dark : styles.light
  const selectedFrameData = framesWithPreview.find(f => f.id === selectedFrame)

  function getFramePreview(frameId) {
    const previews = {
      1: cowboyPreview,
      2: pumpkinPreview,
      3: flowersPreview,
      4: christmasPreview,
      5: seaPreview,
      6: popartPreview,
      7: woodPreview,
      8: metalPreview,
      9: goldPreview
    }
    return previews[frameId] || defaultPreview
  }

  function getFrameModelUrl(frameId) {
    const models = {
      1: cowboyModel,
      2: pumpkinModel,
      3: flowersModel,
      4: christmasModel,
      5: seaModel,
      6: popartModel,
      7: woodModel,
      8: metalModel,
      9: goldModel
    }
    return models[frameId] || cowboyModel
  }

  function getFrameType(frameId) {
    const types = {
      1: 'cowboy',
      2: 'pumpkin', 
      3: 'flowers',
      4: 'christmas',
      5: 'sea',
      6: 'popart',
      7: 'wood',
      8: 'metal',
      9: 'gold'
    }
    return types[frameId] || 'cowboy'
  }

  return (
    <div className={`${styles.frameSelection} ${themeClass}`}>
      <h3 className={styles.frameTitle}>Выбор рамки</h3>
      
      <div className={styles.framesContainer}>
        <div className={styles.framesScroll}>
          {framesWithPreview.map((frame) => (
            <div
              key={frame.id}
              className={`${styles.frame} ${themeClass} ${
                selectedFrame === frame.id ? styles.selected : ''
              }`}
              onClick={() => handleFrameSelect(frame.id)}
            >
              <div className={styles.frameContent}>
                <div className={styles.framePreview}>
                  <img 
                    src={frame.previewImage} 
                    alt={`Превью ${frame.name}`}
                    className={styles.framePreviewImage}
                    onError={(e) => {
                      e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjMzMzIiBvcGFjaXR5PSIwLjMiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE4IiBmaWxsPSIjZmZmIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+UHJldmlldzwvdGV4dD48L3N2Zz4='
                    }}
                  />
                </div>
                <span className={styles.frameName}>{frame.name}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {selectedFrameData && (
        <div className={`${styles.selectedFrameInfo} ${themeClass}`}>
          <h4 className={styles.selectedFrameTitle}>3D модель выбранной рамки</h4>
          <div className={styles.selectedFrameDetails}>
            <div className={styles.frameDetailRow}>
              <span className={styles.detailLabel}>Выбрана рамка:</span>
              <span className={styles.detailValue}>{selectedFrameData.name}</span>
            </div>
            
            <div className={styles.modelViewerContainer}>
              <Canvas
                camera={{ position: [0, 0, 0], fov: 50 }}
                className={styles.modelCanvas}
                shadows
              >
                <ambientLight intensity={0.6} />
                <spotLight 
                  position={[5, 5, 5]} 
                  angle={0.3} 
                  penumbra={1} 
                  intensity={1} 
                  castShadow
                />
                <pointLight position={[-5, -5, -5]} intensity={0.3} />
                
                <Suspense fallback={<ModelFallback />}>
                  <FrameModel modelUrl={selectedFrameData.modelUrl} />
                </Suspense>
                
                <OrbitControls 
                  enableZoom={true}
                  enablePan={false}
                  enableRotate={true}
                  maxDistance={20}
                  minDistance={10}
                  autoRotate={false}
                />
              </Canvas>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default FrameSelection