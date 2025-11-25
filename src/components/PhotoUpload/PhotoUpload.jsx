import React, { useRef, useState } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { useUploadPhotoMutation } from '../../services/api'
import { setUploadedPhoto } from '../../store/slices/photoSlice'
import styles from './PhotoUpload.module.css'

const PhotoUpload = () => {
  const { isDark } = useSelector((state) => state.theme)
  const { isAuthenticated, currentUser } = useSelector((state) => state.auth) // Добавлено currentUser
  const { uploadedPhoto } = useSelector((state) => state.photo) // Добавлено для отображения текущего фото
  const dispatch = useDispatch()
  const [uploadPhoto, { isLoading }] = useUploadPhotoMutation()
  const fileInputRef = useRef(null)
  const [selectedFile, setSelectedFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)

  const handleFileSelect = (event) => {
    const file = event.target.files[0]
    if (file) {
      if (!file.type.match('image.*')) {
        alert('Пожалуйста, выберите файл изображения (JPEG, PNG, etc.)')
        return
      }
      
      // Проверка размера файла (например, максимум 10MB)
      if (file.size > 10 * 1024 * 1024) {
        alert('Файл слишком большой. Максимальный размер: 10MB')
        return
      }
      
      setSelectedFile(file)
      
      // Создаем превью
      const reader = new FileReader()
      reader.onload = (e) => {
        setPreviewUrl(e.target.result)
      }
      reader.readAsDataURL(file)
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
      const formData = new FormData()
      formData.append('file', selectedFile)
      
      console.log('Uploading photo...')
      console.log('🔐 Статус авторизации:', isAuthenticated)
      console.log('👤 Текущий пользователь:', currentUser)
      
      const result = await uploadPhoto(formData).unwrap()
      
      // Сохраняем всю информацию о фото в Redux store
      dispatch(setUploadedPhoto({
        ...result,
        previewUrl: previewUrl // Добавляем временный URL для превью
      }))
      
      alert('Фото успешно загружено и проверено! Лицо обнаружено.')
      setSelectedFile(null)
      setPreviewUrl(null)
      
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (error) {
      console.error('Upload error:', error)
      const errorMessage = error.data?.detail || error.data?.error || 'Ошибка при загрузке фото'
      alert(errorMessage)
    }
  }

  const handleClearSelection = () => {
    setSelectedFile(null)
    setPreviewUrl(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  // Добавлено: функция для удаления загруженного фото
  const handleRemovePhoto = () => {
    dispatch(setUploadedPhoto(null))
    alert('Фото удалено из системы')
  }

  const themeClass = isDark ? styles.dark : styles.light

  return (
    <div className={`${styles.photoUpload} ${themeClass}`}>
      <h3 className={styles.uploadTitle}>
        Загрузка фотографии
      </h3>
      
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileSelect}
        className={styles.hiddenInput}
        accept="image/*"
        disabled={isLoading}
      />
      
      <div className={styles.uploadControls}>
        <button 
          onClick={handleSelectClick}
          className={styles.selectBtn}
          disabled={isLoading}
        >
          {isLoading ? 'Загрузка...' : 'Выбрать файл'}
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
          {isLoading ? 'Проверка...' : (uploadedPhoto ? 'Заменить фото' : 'Загрузить фото')}
        </button>
      </div>
      
      <div className={styles.uploadTips}>
        {!isAuthenticated && (
          <div className={styles.authHint}>
            <p>💡 <strong>Совет:</strong> Для сохранения фото в профиле и доступа к истории загрузок, рекомендуем зарегистрироваться.</p>
          </div>
        )}
        
      </div>
    </div>
  )
}

export default PhotoUpload