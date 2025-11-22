import React from 'react'
import { useSelector } from 'react-redux'
import { useGetGeneratedImageQuery, useGetGenerationStatusQuery } from '../../services/api'
import styles from './GenerationSection.module.css'

const GenerationSection = ({ onGenerate, isLoading, generationId }) => {
  const { isDark } = useSelector((state) => state.theme)
  const { generatedImage } = useSelector((state) => state.photo)

  const { data: generationStatus } = useGetGenerationStatusQuery(generationId, {
    skip: !generationId,
    pollingInterval: 5000, 
  })

  const { data: generatedImageData } = useGetGeneratedImageQuery(generationId, {
    skip: !generationId,
  })

  const themeClass = isDark ? styles.dark : styles.light

  const imageToShow = generatedImageData?.imageUrl || generatedImage

  return (
    <div className={`${styles.generationSection} ${themeClass}`}>
      <h2 className={`${styles.sectionTitle} ${styles.themeText}`}>Генерация изображения</h2>
      <h3 className={styles.themeText}>Результат:</h3>
      <div className={`${styles.resultGenerationPlaceholder} ${themeClass}`}>
        {imageToShow ? (
          <img 
            src={imageToShow} 
            alt="Сгенерированное изображение" 
            className={styles.generatedImage}
          />
        ) : (
          <div className={`${styles.placeholderContent} ${styles.themeText}`}>
            {isLoading || generationStatus?.status === 'processing' 
              ? 'Генерация...' 
              : 'Здесь будет сгенерированное изображение'
            }
          </div>
        )}
      </div>
      <button 
        onClick={onGenerate} 
        className={styles.generateBtn}
        disabled={isLoading || generationStatus?.status === 'processing'}
      >
        {isLoading || generationStatus?.status === 'processing' ? 'Генерация...' : 'Сгенерировать'}
      </button>
      
      {(isLoading || generationStatus?.status === 'processing') && (
        <div className={styles.loadingSpinner}></div>
      )}
    </div>
  )
}

export default GenerationSection