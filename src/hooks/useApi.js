import { useState } from 'react'
import { useDispatch } from 'react-redux'

export const useApi = (apiFunction) => {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [data, setData] = useState(null)

  const execute = async (...args) => {
    try {
      setIsLoading(true)
      setError(null)
      const result = await apiFunction(...args).unwrap()
      setData(result)
      return result
    } catch (err) {
      setError(err.data?.message || 'Произошла ошибка')
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  return {
    execute,
    isLoading,
    error,
    data,
    reset: () => {
      setIsLoading(false)
      setError(null)
      setData(null)
    }
  }
}

export const usePhotoUpload = () => {
  const [uploadPhoto] = useUploadPhotoMutation()
  return useApi(uploadPhoto)
}

export const useImageGeneration = () => {
  const [generateImage] = useGenerateImageMutation()
  return useApi(generateImage)
}