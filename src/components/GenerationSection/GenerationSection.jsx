import React, { useState, useEffect, useRef } from 'react'
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
  const { selectedFrame, frames } = useSelector((state) => state.frame)
  const { answers } = useSelector((state) => state.questionnaire)

  const selectedFrameData = frames.find(f => f.id === selectedFrame)
  
  const [generateImage, { isLoading: isGenerating }] = useGenerateImageMutation()
  
  const [generationId, setGenerationId] = useState(null)
  const [currentImageType, setCurrentImageType] = useState('watermarked')
  const [currentImageUrl, setCurrentImageUrl] = useState(null)
  const [isPolling, setIsPolling] = useState(false)
  const [generationError, setGenerationError] = useState(null)
  const [imageLoadError, setImageLoadError] = useState(false)
  const [lastImageUpdate, setLastImageUpdate] = useState(0)
  const [shouldPoll, setShouldPoll] = useState(true)

  // Константы
  const API_BASE_URL = 'http://localhost:8000'
  
  // Цены (в рублях)
  const PRICES = {
    WATERMARKED_IMAGE: 200,
    NUMBERED_IMAGE: 1400
  }

  // Расчет общей стоимости
  const calculateTotalPrice = () => {
    const framePrice = selectedFrameData ? selectedFrameData.price: 0
    const imagePrice = currentImageType === 'watermarked' ? PRICES.WATERMARKED_IMAGE : PRICES.NUMBERED_IMAGE
    return framePrice + imagePrice
  }

  // Получаем данные сгенерированного изображения
  const { 
    data: generatedImageData, 
    isLoading: isLoadingImageData,
    error: imageDataError,
    refetch: refetchImageData
  } = useGetGeneratedImageQuery(generationId, {
    skip: !generationId,
    refetchOnMountOrArgChange: true,
    pollingInterval: generationId && shouldPoll ? 2000 : 0,
  })

  // Получаем статус генерации
  const { 
    data: generationStatus,
    isLoading: isLoadingStatus 
  } = useGetGenerationStatusQuery(generationId, {
    skip: !generationId,
  })

  // Эффект для управления опросом
  useEffect(() => {
    if (generatedImageData) {
      if (generatedImageData.status === 'completed' || generatedImageData.status === 'failed') {
        console.log('🛑 Останавливаем опрос, статус:', generatedImageData.status)
        setShouldPoll(false)
      } else {
        setShouldPoll(true)
      }
    }
  }, [generatedImageData])

  // Основной эффект для обработки данных изображения
  useEffect(() => {
    if (!generatedImageData) {
      console.log('❌ generatedImageData отсутствует')
      return
    }

    if (generatedImageData.status === 'completed') {
      let imageUrl = null
      
      if (currentImageType === 'watermarked' && generatedImageData.generated_image_url) {
        imageUrl = generatedImageData.generated_image_url
      } else if (currentImageType === 'numbered' && generatedImageData.numbered_image_url) {
        imageUrl = generatedImageData.numbered_image_url
      } else if (generatedImageData.generated_image_url) {
        imageUrl = generatedImageData.generated_image_url
        setCurrentImageType('watermarked')
      }

      if (imageUrl) {
        const fullUrl = getFullImageUrl(imageUrl)
        
        if (fullUrl !== currentImageUrl) {
          console.log('🖼️ Устанавливаем новый URL:', fullUrl)
          setCurrentImageUrl(fullUrl)
          setLastImageUpdate(Date.now())
          setGenerationError(null)
          
          dispatch(setGeneratedImage({
            id: generatedImageData.id,
            url: fullUrl,
            status: 'completed',
            imageType: currentImageType
          }))
        }
      } else {
        console.log('❌ Нет доступного URL изображения')
      }
    } else if (generatedImageData.status === 'failed') {
      setGenerationError(generatedImageData.error_message || "Ошибка генерации изображения")
    }
  }, [generatedImageData, currentImageType, currentImageUrl, dispatch])

  // Функция для получения полного URL
  const getFullImageUrl = (imagePath) => {
    if (!imagePath) {
      console.log('❌ getFullImageUrl: imagePath отсутствует')
      return null
    }
    
    if (imagePath.startsWith('http')) {
      return imagePath
    }
    
    if (imagePath.startsWith('/static')) {
      return `${API_BASE_URL}${imagePath}`
    }
    
    return `${API_BASE_URL}/static/generated_images/${imagePath}`
  }

  // Переключение между типами изображений
  const toggleImageType = () => {
    if (!generatedImageData || generatedImageData.status !== 'completed') {
      return
    }
    
    const hasNumberedImage = !!generatedImageData.numbered_image_url
    const hasWatermarkedImage = !!generatedImageData.generated_image_url
    
    if (!hasWatermarkedImage) {
      console.log('⚠️ Нет доступных изображений для переключения')
      return
    }
    
    if (!hasNumberedImage) {
      console.log('⚠️ Изображение по номерам еще не готово')
      alert('Изображение по номерам еще не готово. Пожалуйста, подождите.')
      return
    }
    
    const newType = currentImageType === 'watermarked' ? 'numbered' : 'watermarked'
    console.log('🔄 Переключение типа изображения:', newType)
    
    setCurrentImageType(newType)
    setCurrentImageUrl(null)
  }

  // Принудительное обновление изображения
  const forceImageReload = () => {
    console.log('🔄 Принудительное обновление изображения')
    setLastImageUpdate(Date.now())
    
    if (generationId) {
      refetchImageData()
    }
  }

  // Сброс состояния для новой генерации
  const resetForNewGeneration = () => {
    console.log('🔄 Сброс состояния для новой генерации')
    
    setGenerationId(null)
    setCurrentImageType('watermarked')
    setCurrentImageUrl(null)
    setGenerationError(null)
    setImageLoadError(false)
    setShouldPoll(true)
  }

  const handleGenerate = async () => {
    resetForNewGeneration()

    if (!uploadedPhoto) {
        alert("Пожалуйста, сначала загрузите фото")
        return
    }

    if (!answers.setting || !answers.clothing || !answers.pose) {
        alert("Пожалуйста, заполните все поля анкеты")
        return
    }

    console.log('🔄 Начинаем генерацию изображения...')
    console.log('📸 ID фото:', uploadedPhoto.id)
    console.log('🖼️ ID рамки:', selectedFrame)

    try {
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

        console.log('📤 Отправка запроса на генерацию:', generationData)

        const result = await generateImage(generationData).unwrap()
        
        console.log('✅ Задача генерации создана:', result)
        setGenerationId(result.id)
        
    } catch (error) {
        console.error('❌ Ошибка при создании задачи генерации:', error)
        
        let errorMessage = 'Неизвестная ошибка при создании задачи генерации'
        if (error.data?.detail) {
            errorMessage = typeof error.data.detail === 'string' 
                ? error.data.detail 
                : JSON.stringify(error.data.detail)
        } else if (error.message) {
            errorMessage = error.message
        }
        
        setGenerationError(errorMessage)
    }
  }

  const themeClass = isDark ? styles.dark : styles.light
  
  const isCurrentlyGenerating = isGenerating || 
                               (generatedImageData ? 
                                 (generatedImageData.status === 'processing' || 
                                  generatedImageData.status === 'pending') 
                                 : (generationStatus?.status === 'processing' || 
                                    generationStatus?.status === 'pending'))
  
  const isButtonDisabled = isGenerating || 
                           (generatedImageData?.status === 'processing') ||
                           (generatedImageData?.status === 'pending') ||
                           !uploadedPhoto

  const hasNumberedImage = generatedImageData?.numbered_image_url && 
                          generatedImageData?.status === 'completed'
  const hasWatermarkedImage = generatedImageData?.generated_image_url && 
                             generatedImageData?.status === 'completed'

  const imageUrlWithTimestamp = currentImageUrl ? 
    `${currentImageUrl.split('?')[0]}?t=${lastImageUpdate}` : 
    null

  // Расчет текущей цены
  const totalPrice = calculateTotalPrice()
  const framePrice = selectedFrameData ? selectedFrameData.price : 0
  const imagePrice = currentImageType === 'watermarked' ? PRICES.WATERMARKED_IMAGE : PRICES.NUMBERED_IMAGE

  return (
    <div className={`${styles.generationSection} ${themeClass}`}>
      <h2 className={`${styles.sectionTitle} ${styles.themeText}`}>Генерация изображения</h2>

      {generationError && (
        <div className={styles.errorAlert}>
          <div className={styles.errorIcon}>⚠️</div>
          <div className={styles.errorContent}>
            <p><strong>Ошибка:</strong> {generationError}</p>
            <button 
              onClick={() => setGenerationError(null)}
              className={styles.dismissButton}
            >
              ✕
            </button>
          </div>
        </div>
      )}

      <h3 className={styles.themeText}>Результат:</h3>
      
      <div className={`${styles.resultGenerationPlaceholder} ${themeClass}`}>
        {imageUrlWithTimestamp ? (
          <div className={styles.generatedImageContainer}>
            <div className={styles.imageWrapper}>
              <img 
                key={`img-${generationId}-${lastImageUpdate}-${currentImageType}`}
                src={imageUrlWithTimestamp}
                alt={currentImageType === 'numbered' ? "Картина по номерам" : "Сгенерированная картина"} 
                className={styles.generatedImage}
                onError={(e) => {
                  console.error('❌ Ошибка загрузки изображения:', e.target.src)
                  setImageLoadError(true)
                  
                  setTimeout(() => {
                    forceImageReload()
                  }, 2000)
                }}
                onLoad={() => {
                  console.log('✅ Изображение успешно загружено!')
                  setImageLoadError(false)
                }}
              />
              {imageLoadError && (
                <div className={styles.imageError}>
                  <p>⚠️ Ошибка загрузки изображения</p>
                  <button 
                    onClick={forceImageReload}
                    className={styles.retryButton}
                  >
                    Повторить загрузку
                  </button>
                </div>
              )}
              
            </div>
          </div>
        ) : generatedImageData?.status === 'completed' && !currentImageUrl ? (
          <div className={styles.generatingContent}>
            <div className={styles.loadingSpinner}></div>
            <p>Загрузка изображения...</p>
          </div>
        ) : isCurrentlyGenerating ? (
          <div className={styles.generatingContent}>
            <div className={styles.loadingSpinner}></div>
            <p>Идет генерация изображения...</p>
            <p>Это может занять 1-2 минуты</p>
            {generatedImageData?.progress > 0 && (
              <div className={styles.progressContainer}>
                <div className={styles.progressBar}>
                  <div 
                    className={styles.progressFill} 
                    style={{ width: `${generatedImageData.progress}%` }}
                  />
                </div>
                <span className={styles.progressText}>
                  {generatedImageData.progress}%
                </span>
              </div>
            )}
          </div>
        ) : (
          <div className={styles.placeholderText}>
            <p>Здесь появится ваша картина</p>
            <p className={styles.placeholderSubtext}>
              Нажмите "Сгенерировать изображение" чтобы начать
            </p>
          </div>
        )}
      </div>
      
      {/* Панель управления изображением */}
      <div className={styles.imageControls}>
        {hasWatermarkedImage && (
          <>
            {hasNumberedImage && (
              <button 
                onClick={toggleImageType}
                className={styles.generateBtn}
              >
                {currentImageType === 'watermarked' 
                  ? 'Показать по номерам' 
                  : 'Показать с водяным знаком'}
              </button>
            )}
          </>
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
        
        <h2 className={`${styles.sectionTitle} ${styles.themeText}`}>Итоговая цена</h2>
        {/* Отображение цены */}
        <div className={`${styles.priceContainer} ${themeClass}`}>
          <div className={styles.priceBreakdown}>
            <div className={styles.priceItem}>
              <span className={styles.priceLabel}>Рамка: </span>
              <span className={styles.priceValue}>
                {framePrice > 0 ? ` ${framePrice.toFixed(0)} рублей` : ' Не выбрана'}
              </span>
            </div>
            <div className={styles.priceItem}>
              <span className={styles.priceLabel}>
                {currentImageType === 'watermarked' ? 'Сгенерированное изображение: ' : 'Картина по номерам: '}
              </span>
              <span className={styles.priceValue}>
                {currentImageType === 'watermarked' ? ' 200 рублей' : ' 1400 рублей'}
              </span>
            </div>
            <div className={styles.priceDivider}></div>
            <div className={styles.priceTotal}>
              <span className={styles.totalLabel}>Итого: </span>
              <span className={styles.totalValue}>{totalPrice.toFixed(0)} рублей</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default GenerationSection