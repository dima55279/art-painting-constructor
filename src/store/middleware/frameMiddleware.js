import { setFrames, enrichFramesWithCameraSettings } from '../slices/frameSlice'

export const frameMiddleware = (store) => (next) => (action) => {
  // Если action setFrames был вызван, автоматически обогащаем данные настройками камеры
  if (action.type === setFrames.type) {
    const result = next(action)
    // После установки frames, обогащаем их настройками камеры
    store.dispatch(enrichFramesWithCameraSettings())
    return result
  }
  
  return next(action)
}