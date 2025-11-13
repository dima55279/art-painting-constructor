import React, { useRef } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { setUploadedPhoto } from '../../store/slices/photoSlice'
import styles from './PhotoUpload.module.css'

const PhotoUpload = () => {
  const dispatch = useDispatch()
  const { uploadedPhoto } = useSelector((state) => state.photo)
  const fileInputRef = useRef(null)

  const handleFileUpload = (event) => {
    const file = event.target.files[0]
    if (file && file.type.match('image.*')) {
      const reader = new FileReader()
      reader.onload = (e) => {
        dispatch(setUploadedPhoto(e.target.result))
      }
      reader.readAsDataURL(file)
    } else {
      alert('Пожалуйста, выберите файл изображения')
    }
  }

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  return (
    <div className={styles.photoUpload}>
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileUpload}
        className={styles.fileInput}
        accept="image/*"
      />
      <button onClick={handleUploadClick} className={styles.uploadBtn}>
        Загрузить фото
      </button>
      
      {uploadedPhoto && (
        <div className={styles.photoPreview}>
          <h3>Ваше фото</h3>
          <div className={styles.resultPhotoPlaceholder}>
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