import React from 'react'
import { useSelector } from 'react-redux'
import styles from './GenerationSection.module.css'

const GenerationSection = ({ onGenerate }) => {
  const { isDark } = useSelector((state) => state.theme)
  const { generatedImage, isLoading } = useSelector((state) => state.photo)

  const themeClass = isDark ? styles.dark : styles.light

  return (
    <div className={`${styles.generationSection} ${themeClass}`}>
      <h2 className={`${styles.sectionTitle} ${styles.themeText}`}>Генерация изображения</h2>
      <h3 className={styles.themeText}>Результат:</h3>
      <div className={`${styles.resultGenerationPlaceholder} ${themeClass}`}>
        {generatedImage ? (
          <img 
            src={generatedImage} 
            alt="Сгенерированное изображение" 
            className={styles.generatedImage}
          />
        ) : (
          <div className={`${styles.placeholderContent} ${styles.themeText}`}>
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
      
      {isLoading && (
        <div className={styles.loadingSpinner}></div>
      )}
    </div>
  )
}

export default GenerationSection