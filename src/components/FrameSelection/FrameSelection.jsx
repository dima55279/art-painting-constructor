import React, { useRef, Suspense, useState, useEffect } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { 
  selectFrame, 
  setFrames, 
  setLoading, 
  setError,
  selectSelectedFrame,
  selectAllFrames,
  getCameraSettingsByType
} from '../../store/slices/frameSlice'
import { useGetFramesQuery, useSelectFrameMutation } from '../../services/api'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { OrbitControls, Center, SoftShadows } from '@react-three/drei'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader'
import * as THREE from 'three'
import styles from './FrameSelection.module.css'

const CameraController = ({ model, cameraSettings }) => {
  const { camera, controls } = useThree()
  
  React.useEffect(() => {
    if (model && controls && cameraSettings) {
      const box = new THREE.Box3().setFromObject(model)
      const center = box.getCenter(new THREE.Vector3())
      const size = box.getSize(new THREE.Vector3())

      const maxDim = Math.max(size.x, size.y, size.z)
      const fov = camera.fov * (Math.PI / 180)
      let cameraDistance = maxDim / (2 * Math.tan(fov / 2))

      cameraDistance *= 1.5
      
      const initialZ = cameraSettings?.initialPosition?.[2] || cameraDistance
      camera.position.set(0, 0, initialZ)
      controls.target.set(center.x, center.y, center.z)
      controls.update()
    }
  }, [model, camera, controls, cameraSettings])
  
  return null
}

const Lighting = () => {
  return (
    <>
      <directionalLight
        position={[10, 10, 5]}
        intensity={1.2}
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
        shadow-camera-far={50}
        shadow-camera-left={-20}
        shadow-camera-right={20}
        shadow-camera-top={20}
        shadow-camera-bottom={-20}
      />
      <directionalLight position={[0, 0, 10]} intensity={0.8} color="#ffffff" />
      <directionalLight position={[-10, 5, 0]} intensity={0.6} color="#ffffee" />
      <directionalLight position={[0, -5, -10]} intensity={0.4} color="#aaaaff" />
      <ambientLight intensity={0.3} color="#ffffff" />
      <pointLight position={[5, 5, 5]} intensity={0.5} color="#fff8e1" distance={30} decay={2} />
      <pointLight position={[-5, -5, 5]} intensity={0.3} color="#e3f2fd" distance={25} decay={2} />
    </>
  )
}

const FrameModel = ({ modelUrl, cameraSettings }) => {
  const [model, setModel] = useState(null)
  const groupRef = useRef()
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  React.useEffect(() => {
    const loadModel = async () => {
      try {
        setLoading(true)
        setError(null)

        if (!modelUrl) {
          setLoading(false)
          return
        }

        const loader = new GLTFLoader()
        const gltf = await loader.loadAsync(modelUrl)
        
        gltf.scene.traverse((child) => {
          if (child.isMesh) {
            child.material = new THREE.MeshStandardMaterial({
              color: child.material?.color || '#ffffff',
              roughness: 0.4,
              metalness: 0.6, 
              side: THREE.DoubleSide,
              envMapIntensity: 1
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

    loadModel()
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

  if (error || !modelUrl) {
    return <SimpleFrame type="default" />
  }

  return (
    <group ref={groupRef}>
      <Center>
        <primitive object={model} scale={1} position={[0, 0, 0]} />
      </Center>
      <CameraController model={model} cameraSettings={cameraSettings} />
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
        <meshStandardMaterial color="#666666" roughness={0.3} metalness={0.7} />
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
  let color = "#ffffff"

  switch(type) {
    case 'wood':
      geometry = <boxGeometry args={[1.5, 1.5, 0.2]} />
      color = "#8B4513"
      break
    case 'gold':
      geometry = <ringGeometry args={[1, 1.4, 32]} />
      color = "#FFD700"
      break
    case 'sea':
      geometry = <ringGeometry args={[1, 1.4, 32]} />
      color = "#1E90FF"
      break
    case 'popart':
      geometry = <cylinderGeometry args={[1, 1.3, 0.15, 8]} />
      color = "#FFFF00"
      break
    case 'halloween':
      geometry = <ringGeometry args={[1.2, 1.5, 32]} />
      color = "#FF7518"
      break
    default:
      geometry = <ringGeometry args={[1.2, 1.5, 32]} />
      color = "#cccccc"
  }

  return (
    <Center>
      <mesh ref={meshRef} scale={scale} castShadow receiveShadow>
        {geometry}
        <meshStandardMaterial color={color} roughness={0.3} metalness={0.7} />
      </mesh>
    </Center>
  )
}

const FrameSelection = () => {
  const dispatch = useDispatch()
  const selectedFrame = useSelector(selectSelectedFrame)
  const framesFromRedux = useSelector(selectAllFrames)
  const { isDark } = useSelector((state) => state.theme)

  const { data: framesData, isLoading: isFramesLoading, error: framesError } = useGetFramesQuery({ limit: 100 })
  const [selectFrameApi, { isLoading: isSelecting }] = useSelectFrameMutation()

  // Синхронизируем данные с сервера с Redux store
  useEffect(() => {
    if (framesData?.frames) {
      dispatch(setFrames(framesData.frames))
    }
    if (framesError) {
      dispatch(setError(framesError))
    }
  }, [framesData, framesError, dispatch])

  const getImageUrl = (imagePath) => {
    if (!imagePath) return null
    if (imagePath.startsWith('http')) return imagePath
    return `http://localhost:8000${imagePath}`
  }

  const handleFrameSelect = async (frameId) => {
    try {
      if (frameId === null) {
        // Сброс выбора
        dispatch(selectFrame(null))
        return
      }
      
      await selectFrameApi(frameId).unwrap()
      dispatch(selectFrame(frameId))
    } catch (error) {
      console.error('Error selecting frame:', error)
      // Если API выдает ошибку, все равно выбираем рамку локально
      dispatch(selectFrame(frameId))
    }
  }

  const themeClass = isDark ? styles.dark : styles.light

  // Используем frames из Redux store (которые уже обогащены настройками камеры)
  const availableFrames = framesFromRedux
  const selectedFrameData = availableFrames.find(f => f.id === selectedFrame)

  return (
    <div className={`${styles.frameSelection} ${themeClass}`}>
      <div className={styles.header}>
        <h3 className={styles.frameTitle}>Выбор рамки</h3>
      </div>
      
      {isFramesLoading ? (
        <div className={styles.loading}>Загрузка рамок...</div>
      ) : framesError ? (
        <div className={styles.error}>
          Ошибка загрузки рамок: {framesError.status} - {framesError.data?.detail || 'Неизвестная ошибка'}
        </div>
      ) : (
        <>
          <div className={styles.framesContainer}>
            <div className={styles.framesScroll}>
              {availableFrames.map((frame) => (
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
                        src={getImageUrl(frame.preview_image_url) || '/placeholder-frame.png'}
                        alt={`Превью ${frame.name}`}
                        className={styles.framePreviewImage}
                        onError={(e) => {
                          e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjMzMzIiBvcGFjaXR5PSIwLjMiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE4IiBmaWxsPSIjZmZmIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+UHJldmlldzwvdGV4dD48L3N2Zz4='
                        }}
                      />
                    </div>
                    <div className={styles.frameInfo}>
                      <span className={styles.frameName}>{frame.name}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {selectedFrameData && (
            <div className={`${styles.selectedFrameInfo} ${themeClass}`}>
              <h4 className={styles.selectedFrameTitle}>
                  3D модель выбранной рамки: {selectedFrameData.name}
                </h4>
              <div className={styles.selectedFrameHeader}>
                <button 
                  className={`${styles.resetButton} ${themeClass}`}
                  onClick={() => handleFrameSelect(null)}
                >
                Выбрать другую
                </button>
              </div>
              
              <div className={styles.frameDetails}>
                <div className={styles.framePriceInfo}>
                  <span className={styles.selectedFrameTitle}>Стоимость рамки:</span>
                  <span className={styles.selectedFrameTitle}>
                    {selectedFrameData.price > 0 ? 
                      ` ${(selectedFrameData.price).toFixed(0)} рублей` : 
                      'Бесплатно'
                    }
                  </span>
                </div>
              </div>
                
              <div className={styles.modelViewerContainer}>
                <Canvas
                  camera={{ 
                    position: selectedFrameData.cameraSettings?.initialPosition || [0, 0, 5], 
                    fov: 50 
                  }}
                  className={styles.modelCanvas}
                  shadows={{ enabled: true, type: THREE.PCFSoftShadowMap }}
                  gl={{ antialias: true, alpha: true }}
                >
                  <SoftShadows size={25} samples={16} focus={0.5} />
                  <Lighting />
                  <Suspense fallback={<ModelFallback />}>
                    {selectedFrameData.model_3d_url ? (
                      <FrameModel 
                        modelUrl={getImageUrl(selectedFrameData.model_3d_url)}
                        cameraSettings={selectedFrameData.cameraSettings}
                      />
                    ) : (
                      <SimpleFrame type={selectedFrameData.frame_type} />
                    )}
                  </Suspense>
                  <OrbitControls 
                    enableZoom={true}
                    enablePan={false}
                    enableRotate={true}
                    maxDistance={selectedFrameData.cameraSettings?.maxDistance || 10}
                    minDistance={selectedFrameData.cameraSettings?.minDistance || 3}
                    autoRotate={false}
                  />
                </Canvas>
              </div>
            </div>
          )}

          {availableFrames.length === 0 && (
            <div className={styles.noFrames}>
              Рамки не найдены. Убедитесь, что сервер запущен и база данных содержит рамки.
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default FrameSelection