import React, { useState, useEffect } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { selectCurrentUser } from '../../store/slices/authSlice'
import { 
  useGenerateImageMutation, 
  useGetGeneratedImageQuery, 
  useGetGenerationStatusQuery,
  useSubmitQuestionnaireMutation,
  useUploadPhotoMutation // Добавьте этот импорт
} from '../../services/api'
import { setGeneratedImage, setUploadedPhoto } from '../../store/slices/photoSlice' // Добавьте setUploadedPhoto
import styles from './GenerationSection.module.css'

const GenerationSection = ({ onGenerate, isLoading, generationId }) => {
  const dispatch = useDispatch()
  const { isDark } = useSelector((state) => state.theme)
  const { uploadedPhoto, generatedImage } = useSelector((state) => state.photo)
  const { selectedFrame } = useSelector((state) => state.frame)
  const { answers } = useSelector((state) => state.questionnaire)
  const { isAuthenticated} = useSelector((state) => state.auth) // Добавьте эту строку
  const currentUser = useSelector(selectCurrentUser)

  const [generateImage, { isLoading: isGenerating }] = useGenerateImageMutation()
  const [submitQuestionnaire] = useSubmitQuestionnaireMutation()
  const [uploadPhoto] = useUploadPhotoMutation() // Добавьте эту строку
  const [localGenerationId, setLocalGenerationId] = useState(generationId)
  const [pollingEnabled, setPollingEnabled] = useState(false)

  // Опрос статуса генерации
  const { data: generationStatus } = useGetGenerationStatusQuery(localGenerationId, {
    skip: !localGenerationId || !pollingEnabled,
    pollingInterval: 2000,
  })

  // Получение результата генерации
  const { data: generatedImageData } = useGetGeneratedImageQuery(localGenerationId, {
    skip: !localGenerationId,
  })

  useEffect(() => {
  // Если пользователь авторизовался, но фото загружено как анонимное, перезагрузите фото
  if (isAuthenticated && uploadedPhoto && !uploadedPhoto.user_id) {
    console.log('🔄 Пользователь авторизован, но фото анонимное. Перезагружаем фото...');
    handleRegeneratePhoto();
  }
}, [isAuthenticated, uploadedPhoto]);

const handleRegeneratePhoto = async () => {
  if (!uploadedPhoto) return;
  
  try {
    // Вместо загрузки по URL, просто обновляем фото с текущим пользователем
    console.log('🔄 Обновляем фото для авторизованного пользователя...');
    
    // Просто диспатчим обновленное фото с user_id
    // В реальном приложении здесь должен быть API вызов для обновления owner фото
    const updatedPhoto = {
      ...uploadedPhoto,
      user_id: currentUser?.id // предполагая, что currentUser доступен
    };
    
    console.log('✅ Фото обновлено для авторизованного пользователя:', updatedPhoto);
    
    dispatch(setUploadedPhoto(updatedPhoto));
  } catch (error) {
    console.error('❌ Ошибка обновления фото:', error);
  }
};

const checkImageDirectly = async () => {
  if (!localGenerationId) return;
  
  try {
    const response = await fetch(`http://localhost:8000/api/generate/${localGenerationId}`);
    const data = await response.json();
    console.log("🔍 Direct API response:", data);
    
    if (data.generated_image_url) {
      console.log("✅ Found image URL via direct fetch:", data.generated_image_url);
      dispatch(setGeneratedImage({
        generated_image_url: data.generated_image_url,
        preview_image_url: data.preview_image_url
      }));
    }
  } catch (error) {
    console.error("❌ Direct fetch failed:", error);
  }
};

// Вызывайте эту функцию при завершении генерации
useEffect(() => {
  if (generationStatus?.status === 'completed') {
    checkImageDirectly();
  }
}, [generationStatus?.status, localGenerationId, dispatch]);

const handleGenerate = async () => {

  if (!uploadedPhoto) {
    alert("Пожалуйста, сначала загрузите фото");
    return;
  }
  
  if (!selectedFrame) {
    alert("Пожалуйста, выберите рамку");
    return;
  }
  
  if (!answers.setting || !answers.clothing || !answers.pose) {
    alert("Пожалуйста, заполните все поля анкеты");
    return;
  }

   console.log("🔄 Starting generation with simplified structure");

  try {
    // УПРОЩЕННАЯ СТРУКТУРА - данные напрямую без оберток
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
    };

    console.log("📤 Sending simplified generation data:", generationData);

    const result = await generateImage(generationData).unwrap();
    
    console.log("✅ Generation started successfully:", result);
    setLocalGenerationId(result.id);
    setPollingEnabled(true);
    
  } catch (error) {
    console.error("❌ Generation failed:", error);
    
    // Детальная диагностика ошибки
    if (error.data && error.data.detail) {
      console.log("🔍 Full error details:", JSON.stringify(error.data.detail, null, 2));
    }
    
    alert(`Ошибка генерации: ${error.status} - ${error.data?.detail || 'Неизвестная ошибка'}`);
  }
};

  const themeClass = isDark ? styles.dark : styles.light

  // Определяем какое изображение показывать
 const imageToShow = generatedImageData?.generated_image_url || 
                   generatedImage || 
                   (generationStatus?.status === 'completed' ? generationStatus.generated_image_url : null)
  console.log("🖼️ Image URL to show:", imageToShow);
  // Определяем статус загрузки
  const isCurrentlyGenerating = isGenerating || 
                               (pollingEnabled && 
                                generationStatus?.status !== 'completed' && 
                                generationStatus?.status !== 'failed')

  return (
    <div className={`${styles.generationSection} ${themeClass}`}>
      <h2 className={`${styles.sectionTitle} ${styles.themeText}`}>Генерация изображения</h2>
      
      <div className={styles.generationStatus}>
        {generationStatus && (
          <div className={styles.statusInfo}>
            <span className={styles.statusText}>
              Статус: {getStatusText(generationStatus.status)}
            </span>
            {generationStatus.progress > 0 && (
              <div className={styles.progressBar}>
                <div 
                  className={styles.progressFill}
                  style={{ width: `${generationStatus.progress}%` }}
                />
              </div>
            )}
          </div>
        )}
      </div>

      <h3 className={styles.themeText}>Результат:</h3>
      <div className={`${styles.resultGenerationPlaceholder} ${themeClass}`}>
        {imageToShow ? (
          <div className={styles.generatedImageContainer}>
            <img 
              src={`http://localhost:8000${imageToShow}`} 
              alt="Сгенерированное изображение" 
              className={styles.generatedImage}
              onError={(e) => {
                console.error("❌ Error loading image:", imageToShow);
                e.target.style.display = 'none';
              }}
              onLoad={() => console.log("✅ Image loaded successfully")}
            />
            <div className={styles.imageActions}>
              <button className={styles.downloadBtn}>Скачать</button>
              <button className={styles.regenerateBtn}>Перегенерировать</button>
            </div>
          </div>
        ) : (
          <div className={`${styles.placeholderContent}`}>
            {isCurrentlyGenerating ? (
              <div className={styles.generatingContent}>
                <div className={styles.loadingSpinner}></div>
                <p>Идет генерация изображения...</p>
                <p>Это может занять несколько минут</p>
                {generationStatus?.progress > 0 && (
                  <p>Прогресс: {generationStatus.progress}%</p>
                )}
              </div>
            ) : (
              'Здесь будет сгенерированное изображение'
            )}
          </div>
        )}
      </div>
      
      <button 
        onClick={handleGenerate} 
        className={styles.generateBtn}
        disabled={isCurrentlyGenerating || !uploadedPhoto || !selectedFrame}
      >
        {isCurrentlyGenerating ? 'Генерация...' : 'Сгенерировать изображение'}
      </button>
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