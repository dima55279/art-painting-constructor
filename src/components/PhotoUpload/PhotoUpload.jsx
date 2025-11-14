import React, { useRef } from 'react'
import { useSelector } from 'react-redux'
import { usePhotoUpload } from '../../hooks/usePhotoUpload'
import styles from './PhotoUpload.module.css'

const PhotoUpload = () => {
  const { isDark } = useSelector((state) => state.theme)
  const { handlePhotoUpload, isLoading } = usePhotoUpload()
  const fileInputRef = useRef(null)

  const handleFileChange = async (event) => {
    const file = event.target.files[0]
    if (file) {
      try {
        await handlePhotoUpload(file)
        alert('Фото успешно загружено! Теперь оно отображается в левой колонке.')
      } catch (error) {
        alert(error.message)
      }
    }
  }

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  const themeClass = isDark ? styles.dark : styles.light

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
    </div>
  )
}

export default PhotoUpload