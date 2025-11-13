import React, { useRef } from 'react'
import { useSelector } from 'react-redux'
import { usePhotoUpload } from '../../hooks/usePhotoUpload'
import styles from './PhotoUpload.module.css'

const PhotoUpload = () => {
  const { uploadedPhoto } = useSelector((state) => state.photo)
  const { isDark } = useSelector((state) => state.theme)
  const { handlePhotoUpload, isLoading } = usePhotoUpload()
  const fileInputRef = useRef(null)

  const handleFileChange = async (event) => {
    const file = event.target.files[0]
    if (file) {
      try {
        await handlePhotoUpload(file)
        alert('Фото успешно загружено!')
      } catch (error) {
        alert(error.message)
      }
    }
  }

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  const themeClass = isDark ? styles.dark : styles.light
  const titleThemeClass = isDark ? styles.photoTitleDark : styles.photoTitleLight

  return (
    <div className={`${styles.photoUpload} ${themeClass}`}>
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        className={`${styles.fileInput} ${themeClass}`}
        accept="image/*"
        disabled={isLoading}
      />
      <button 
        onClick={handleUploadClick} 
        className={styles.uploadBtn}
        disabled={isLoading}
      >
        {isLoading ? 'Загрузка...' : 'Загрузить фото'}
      </button>
      
      {uploadedPhoto && (
        <div className={styles.photoPreview}>
          <h3 className={`${styles.photoTitle} ${titleThemeClass}`}>Ваше фото</h3>
          <div className={`${styles.resultPhotoPlaceholder} ${themeClass}`}>
            <img 
              src={uploadedPhoto} 
              alt="Загруженное фото" 
              className={styles.uploadedPhoto}
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default PhotoUpload