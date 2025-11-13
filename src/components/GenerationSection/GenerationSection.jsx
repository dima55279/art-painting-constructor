import React from 'react'
import { useSelector } from 'react-redux'
import styles from './GenerationSection.module.css'

const GenerationSection = ({ onGenerate }) => {
  const { isDark } = useSelector((state) => state.theme)
  const { generatedImage, isLoading } = useSelector((state) => state.photo)

  return (
    <div className={styles.generationSection}>
      <h2 className={styles.sectionTitle}>Генерация изображения</h2>
      <h3>Результат:</h3>
      <div className={styles.resultGenerationPlaceholder}>
        {generatedImage ? (
          <img 
            src={generatedImage} 
            alt="Сгенерированное изображение" 
            className={styles.generatedImage}
          />
        ) : (
          <div className={styles.placeholderContent}>
            {isLoading ? 'Генерация...' : 'Здесь будет сгенерированное изображение'}
          </div>
        )}
      </div>
      <button 
        onClick={onGenerate} 
        className={styles.generateBtn}
        disabled={isLoading}
      >
        {isLoading ? 'Генерация...' : 'Сгенерировать'}
      </button>
    </div>
  )
}

export default GenerationSection