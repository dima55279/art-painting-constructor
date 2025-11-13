import { useState } from 'react'
import { useDispatch } from 'react-redux'
import { setUploadedPhoto } from '../store/slices/photoSlice'

export const usePhotoUpload = () => {
  const dispatch = useDispatch()
  const [isLoading, setIsLoading] = useState(false)

  const handlePhotoUpload = (file) => {
    return new Promise((resolve, reject) => {
      if (!file) {
        reject(new Error('Файл не выбран'))
        return
      }

      if (!file.type.match('image.*')) {
        reject(new Error('Пожалуйста, выберите файл изображения (JPEG, PNG, etc.)'))
        return
      }

      setIsLoading(true)
      
      const reader = new FileReader()
      
      reader.onload = (e) => {
        dispatch(setUploadedPhoto(e.target.result))
        setIsLoading(false)
        resolve(e.target.result)
      }
      
      reader.onerror = () => {
        setIsLoading(false)
        reject(new Error('Ошибка при чтении файла'))
      }
      
      reader.readAsDataURL(file)
    })
  }

  return {
    handlePhotoUpload,
    isLoading
  }
}