import React, { useState, useEffect, useCallback, useRef } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { 
  useGenerateImageMutation, 
  useGetGeneratedImageQuery,
  useGetGenerationStatusQuery,
} from '../../services/api'
import { setGeneratedImage } from '../../store/slices/photoSlice'
import styles from './GenerationSection.module.css'

const GenerationSection = () => {
  const dispatch = useDispatch()
  const { isDark } = useSelector((state) => state.theme)
  const { uploadedPhoto } = useSelector((state) => state.photo)
  const { selectedFrame } = useSelector((state) => state.frame)
  const { answers } = useSelector((state) => state.questionnaire)

  const [generateImage, { isLoading: isGenerating }] = useGenerateImageMutation()
  
  const [localGenerationId, setLocalGenerationId] = useState(null)
  const [currentImageUrl, setCurrentImageUrl] = useState(null)
  const [isPolling, setIsPolling] = useState(false)
  const [generationError, setGenerationError] = useState(null)
  const [imageLoadError, setImageLoadError] = useState(false)
  const [retryCount, setRetryCount] = useState(0)
  const [displayStatus, setDisplayStatus] = useState(null) // Локальный статус для отображения
  
  const abortControllerRef = useRef(null)
  const generationCountRef = useRef(0)
  const retryTimeoutRef = useRef(null)

  // Базовый URL для API
  const API_BASE_URL = 'http://localhost:8000'

  // Получаем статус генерации
  const { 
    data: generationStatus, 
  } = useGetGenerationStatusQuery(localGenerationId, {
    skip: !localGenerationId || !isPolling,
    pollingInterval: 1000,
  })

  // Получаем данные сгенерированного изображения
  const { 
    data: generatedImageData, 
    refetch: refetchImageData,
  } = useGetGeneratedImageQuery(localGenerationId, {
    skip: !localGenerationId,
    refetchOnMountOrArgChange: true,
  })

  // Синхронизируем локальный статус с полученным из API
  useEffect(() => {
    if (generationStatus && localGenerationId) {
      console.log(`📊 Updating display status for generation ${localGenerationId}:`, generationStatus.status)
      setDisplayStatus(generationStatus)
    }
  }, [generationStatus, localGenerationId])

  // Очистка при размонтировании
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current)
      }
    }
  }, [])

  // Функция для получения полного URL изображения
  const getFullImageUrl = useCallback((imagePath) => {
    if (!imagePath) return null
    
    if (imagePath.startsWith('http')) {
      return imagePath
    }
    
    if (imagePath.startsWith('/')) {
      return `${API_BASE_URL}${imagePath}`
    }
    
    return `${API_BASE_URL}/static/generated_images/${imagePath}`
  }, [API_BASE_URL])

  // Функция для проверки доступности изображения
  const checkImageAvailability = useCallback(async (imageUrl, generationId) => {
    if (!imageUrl) return false
    
    const fullUrl = getFullImageUrl(imageUrl)
    console.log(`🔍 Checking image availability for generation ${generationId}: ${fullUrl}`)
    
    try {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
      
      abortControllerRef.current = new AbortController()
      
      const response = await fetch(fullUrl, { 
        method: 'HEAD',
        signal: abortControllerRef.current.signal 
      })
      
      if (response.ok) {
        console.log(`✅ Image is available: ${fullUrl}`)
        return { available: true, url: fullUrl }
      } else {
        console.warn(`⚠️ Image not available (status ${response.status}): ${fullUrl}`)
        return { available: false, url: fullUrl }
      }
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error(`❌ Error checking image: ${error}`)
      }
      return { available: false, url: fullUrl }
    }
  }, [getFullImageUrl])

  // Основная функция для установки изображения
  const setImageFromData = useCallback(async (imageData, generationId) => {
    if (!imageData || !generationId) return false
    
    console.log(`🖼️ Processing image data for generation ${generationId}:`, {
      status: imageData.status,
      hasUrl: !!imageData.generated_image_url,
      url: imageData.generated_image_url
    })
    
    // Если в данных есть URL, пробуем его
    if (imageData.generated_image_url) {
      const checkResult = await checkImageAvailability(imageData.generated_image_url, generationId)
      if (checkResult.available) {
        console.log(`✅ Setting image from data: ${checkResult.url}`)
        setCurrentImageUrl(checkResult.url)
        setImageLoadError(false)
        setGenerationError(null)
        return true
      }
    }
    
    console.warn(`⚠️ Could not find image for generation ${generationId}`)
    return false
  }, [checkImageAvailability])

  // Сброс состояния для новой генерации
  const resetForNewGeneration = useCallback(() => {
    console.log("🔄 Resetting state for new generation")
    
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current)
    }
    
    setCurrentImageUrl(null)
    setGenerationError(null)
    setImageLoadError(false)
    setRetryCount(0)
    setDisplayStatus(null) // Сбрасываем статус при новой генерации
    setIsPolling(false)
    generationCountRef.current++
  }, [])

  // Функция для повторной попытки получения изображения
  const retryImageLoad = useCallback(async () => {
    if (!localGenerationId) return
    
    const newRetryCount = retryCount + 1
    setRetryCount(newRetryCount)
    
    console.log(`🔄 Retry attempt ${newRetryCount} for generation ${localGenerationId}`)
    
    if (newRetryCount > 5) {
      console.error(`❌ Max retry attempts reached for generation ${localGenerationId}`)
      setGenerationError("Не удалось загрузить изображение после нескольких попыток")
      return
    }
    
    // Перезапрашиваем данные
    try {
      const result = await refetchImageData()
      if (result.data) {
        const success = await setImageFromData(result.data, localGenerationId)
        if (!success) {
          // Если не удалось, пробуем снова через 2 секунды
          retryTimeoutRef.current = setTimeout(retryImageLoad, 2000)
        }
      }
    } catch (error) {
      console.error(`❌ Error during retry: ${error}`)
      retryTimeoutRef.current = setTimeout(retryImageLoad, 2000)
    }
  }, [localGenerationId, retryCount, refetchImageData, setImageFromData])

  // Обработка завершения генерации
  useEffect(() => {
    if (generationStatus?.status === 'completed' && localGenerationId) {
      console.log(`✅ Generation ${localGenerationId} completed`)
      setIsPolling(false)
      
      // Даем бэкенду время на сохранение
      setTimeout(async () => {
        console.log(`🔄 Loading image data for completed generation ${localGenerationId}`)
        try {
          const result = await refetchImageData()
          if (result.data) {
            const success = await setImageFromData(result.data, localGenerationId)
            if (!success) {
              // Если не удалось с первого раза, начинаем повторные попытки
              retryTimeoutRef.current = setTimeout(retryImageLoad, 1000)
            }
          }
        } catch (error) {
          console.error(`❌ Error loading image data: ${error}`)
          retryTimeoutRef.current = setTimeout(retryImageLoad, 1000)
        }
      }, 1500)
    } else if (generationStatus?.status === 'failed' && localGenerationId) {
      console.error(`❌ Generation ${localGenerationId} failed:`, generationStatus.error_message)
      setIsPolling(false)
      setGenerationError(generationStatus.error_message || "Ошибка при генерации изображения")
    }
  }, [generationStatus, localGenerationId, refetchImageData, setImageFromData, retryImageLoad])

  // Обработка изменения данных из API
  useEffect(() => {
    if (generatedImageData && localGenerationId === generatedImageData.id) {
      console.log(`📦 Received API data for generation ${localGenerationId}`)
      
      if (generatedImageData.status === 'completed') {
        setImageFromData(generatedImageData, localGenerationId)
      } else if (generatedImageData.status === 'failed') {
        setGenerationError(generatedImageData.error_message || "Ошибка при генерации изображения")
      }
    }
  }, [generatedImageData, localGenerationId, setImageFromData])

  const handleGenerate = async () => {
    if (!uploadedPhoto) {
      alert("Пожалуйста, сначала загрузите фото")
      return
    }
    
    if (!selectedFrame) {
      alert("Пожалуйста, выберите рамку")
      return
    }
    
    if (!answers.setting || !answers.clothing || !answers.pose) {
      alert("Пожалуйста, заполните все поля анкеты")
      return
    }

    console.log("🔄 Starting new image generation...")
    console.log(`📊 Generation count: ${generationCountRef.current + 1}`)

    try {
      // Полностью сбрасываем состояние
      resetForNewGeneration()
      
      const generationData = {
        photo_id: uploadedPhoto.id,
        frame_id: selectedFrame,
        questionnaire: {
          setting: answers.setting,
          clothing: answers.clothing,
          pose: answers.pose,
          additional_notes: answers.translated_prompt || answers.additional_notes || ''
        },
        theme: isDark ? 'dark' : 'light',
        style: 'realistic',
        enhance_face: true
      }

      console.log("📤 Sending generation data:", generationData)

      const result = await generateImage(generationData).unwrap()
      
      console.log("✅ Generation task created:", result)
      
      // Устанавливаем новый ID и начинаем опрос
      setLocalGenerationId(result.id)
      setIsPolling(true)
      
    } catch (error) {
      console.error("❌ Generation request failed:", error)
      
      let errorMessage = 'Неизвестная ошибка'
      if (error.data?.detail) {
        errorMessage = typeof error.data.detail === 'string' 
          ? error.data.detail 
          : JSON.stringify(error.data.detail)
      } else if (error.error) {
        errorMessage = error.error
      }
      
      setGenerationError(errorMessage)
    }
  }

  const themeClass = isDark ? styles.dark : styles.light

  // Определяем статус загрузки
  const isCurrentlyGenerating = isGenerating || 
                               (isPolling && 
                                generationStatus?.status !== 'completed' && 
                                generationStatus?.status !== 'failed')

  const isButtonDisabled = isCurrentlyGenerating || !uploadedPhoto || !selectedFrame

  // Функция для получения текста статуса
  const getStatusDisplay = () => {
    if (displayStatus) {
      return getStatusText(displayStatus.status)
    }
    
    if (isCurrentlyGenerating && localGenerationId) {
      return "Генерация..."
    }
    
    return null
  }

  return (
    <div className={`${styles.generationSection} ${themeClass}`}>
      <h2 className={`${styles.sectionTitle} ${styles.themeText}`}>Генерация изображения</h2>
      
      {generationError && displayStatus?.status !== 'processing' && (
        <div className={styles.errorAlert}>
          <div className={styles.errorIcon}>⚠️</div>
          <div className={styles.errorContent}>
            <p><strong>Ошибка:</strong> {generationError}</p>
          </div>
        </div>
      )}

      <h3 className={styles.themeText}>Результат:</h3>
      <div className={`${styles.resultGenerationPlaceholder} ${themeClass}`}>
        {currentImageUrl ? (
          <div className={styles.generatedImageContainer}>
            <div className={styles.imageWrapper}>
              <img 
                key={`image-${localGenerationId}-${generationCountRef.current}`}
                src={currentImageUrl} 
                alt="Сгенерированное изображение" 
                className={styles.generatedImage}
                onError={(e) => {
                  console.error("❌ Image load failed:", currentImageUrl)
                  e.target.style.display = 'none'
                  setImageLoadError(true)
                  // Автоматически пробуем снова через 2 секунды
                  setTimeout(() => {
                    if (localGenerationId) {
                      retryImageLoad()
                    }
                  }, 2000)
                }}
                onLoad={() => {
                  console.log("✅ Image loaded successfully!")
                  setImageLoadError(false)
                }}
              />
              {imageLoadError && (
                <div className={styles.imageError}>
                  <p>⚠️ Не удалось загрузить изображение</p>
                  <p>Попытка {retryCount + 1}...</p>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className={styles.placeholderContent}>
            {isCurrentlyGenerating ? (
              <div className={styles.generatingContent}>
                <div className={styles.loadingSpinner}></div>
                <p>Идет генерация изображения...</p>
                <p>Это может занять несколько минут</p>
                {displayStatus?.progress > 0 && (
                  <p>Прогресс: {displayStatus.progress}%</p>
                )}
                {displayStatus?.status === 'processing' && (
                  <p className={styles.hint}>Нейросеть рисует изображение...</p>
                )}
              </div>
            ) : generationError ? (
              <div className={styles.errorContent}>
                <div className={styles.errorIcon}>⚠️</div>
                <p>{generationError}</p>
              </div>
            ) : (
              <div className={styles.placeholderText}>
                <p>Здесь будет сгенерированное изображение</p>
                <p className={styles.placeholderSubtext}>
                  Нажмите "Сгенерировать изображение" чтобы начать
                </p>
              </div>
            )}
          </div>
        )}
      </div>
      
      <div className={styles.generateButtonContainer}>
        <button 
          onClick={handleGenerate} 
          className={`${styles.generateBtn} ${isCurrentlyGenerating ? styles.generating : ''}`}
          disabled={isButtonDisabled}
        >
          {isCurrentlyGenerating ? (
            <>
              <span className={styles.spinner}></span>
              Идет генерация...
            </>
          ) : 'Сгенерировать изображение'}
        </button>
      </div>
    </div>
  )
}

// Вспомогательная функция для отображения статуса
function getStatusText(status) {
  const statusMap = {
    'pending': 'В очереди',
    'processing': 'Генерация...',
    'completed': 'Завершено',
    'failed': 'Ошибка'
  }
  return statusMap[status] || status
}

export default GenerationSection