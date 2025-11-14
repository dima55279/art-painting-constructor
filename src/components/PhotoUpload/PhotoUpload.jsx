import React, { useRef, useState } from 'react'
import { useSelector } from 'react-redux'
import { usePhotoUpload } from '../../hooks/usePhotoUpload'
import styles from './PhotoUpload.module.css'

const PhotoUpload = () => {
  const { isDark } = useSelector((state) => state.theme)
  const { handlePhotoUpload, isLoading } = usePhotoUpload()
  const fileInputRef = useRef(null)
  const [selectedFile, setSelectedFile] = useState(null)

  const handleFileSelect = (event) => {
    const file = event.target.files[0]
    if (file) {
      if (!file.type.match('image.*')) {
        alert('Пожалуйста, выберите файл изображения (JPEG, PNG, etc.)')
        return
      }
      setSelectedFile(file)
    }
  }

  const handleSelectClick = () => {
    fileInputRef.current?.click()
  }

  const handleUploadClick = async () => {
    if (!selectedFile) {
      alert('Пожалуйста, сначала выберите файл')
      return
    }

    try {
      await handlePhotoUpload(selectedFile)
      alert('Фото успешно загружено! Теперь оно отображается в левой колонке.')
      setSelectedFile(null) 
    } catch (error) {
      alert(error.message)
    }
  }

  const handleClearSelection = () => {
    setSelectedFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const themeClass = isDark ? styles.dark : styles.light

  return (
    <div className={`${styles.photoUpload} ${themeClass}`}>
      
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileSelect}
        className={styles.hiddenInput}
        accept="image/*"
        disabled={isLoading}
      />
      
      <button 
        onClick={handleSelectClick}
        className={styles.selectBtn}
        disabled={isLoading}
      >
        Выбрать файл
      </button>

      {selectedFile && (
        <div className={styles.fileInfo}>
          <div className={styles.fileDetails}>
            <span className={styles.fileName}>{selectedFile.name}</span>
            <span className={styles.fileSize}>
              ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
            </span>
          </div>
          <button 
            onClick={handleClearSelection}
            className={styles.clearBtn}
            disabled={isLoading}
          >
            ×
          </button>
        </div>
      )}
      
      <button 
        onClick={handleUploadClick}
        className={styles.uploadBtn}
        disabled={!selectedFile || isLoading}
      >
        {isLoading ? 'Загрузка...' : 'Загрузить фото'}
      </button>
      
    </div>
  )
}

export default PhotoUpload