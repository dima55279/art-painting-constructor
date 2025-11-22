import { createSlice } from '@reduxjs/toolkit'

// Статические настройки камеры для каждого типа рамки
const frameCameraSettings = {
  'cowboy': { minDistance: 10, maxDistance: 20, initialPosition: [0, 0, 50] },
  'pumpkin': { minDistance: 100, maxDistance: 125, initialPosition: [90, 90, 45] },
  'flowers': { minDistance: 5, maxDistance: 7, initialPosition: [0, 0, 40] },
  'christmas': { minDistance: 3, maxDistance: 5, initialPosition: [0, 0, 55] },
  'sea': { minDistance: 5, maxDistance: 7, initialPosition: [0, 0, 48] }
}

const initialState = {
  selectedFrame: null,
  // Убираем статические frames, так как будем использовать данные с сервера
  frames: [],
  // Добавляем флаги для управления состоянием
  isLoading: false,
  error: null
}

export const frameSlice = createSlice({
  name: 'frame',
  initialState,
  reducers: {
    selectFrame: (state, action) => {
      state.selectedFrame = action.payload
    },
    clearFrame: (state) => {
      state.selectedFrame = null
    },
    // Новые actions для работы с данными с сервера
    setFrames: (state, action) => {
      state.frames = action.payload
    },
    setLoading: (state, action) => {
      state.isLoading = action.payload
    },
    setError: (state, action) => {
      state.error = action.payload
    },
    // Action для обогащения данных с сервера настройками камеры
    enrichFramesWithCameraSettings: (state) => {
      state.frames = state.frames.map(frame => ({
        ...frame,
        cameraSettings: frameCameraSettings[frame.frame_type] || frameCameraSettings.default
      }))
    }
  },
})

// Селекторы для удобного доступа к данным
export const selectSelectedFrame = (state) => state.frame.selectedFrame
export const selectAllFrames = (state) => state.frame.frames
export const selectFrameById = (frameId) => (state) => 
  state.frame.frames.find(frame => frame.id === frameId)
export const selectFrameLoading = (state) => state.frame.isLoading
export const selectFrameError = (state) => state.frame.error

// Вспомогательная функция для получения настроек камеры по типу рамки
export const getCameraSettingsByType = (frameType) => {
  return frameCameraSettings[frameType] || frameCameraSettings.default
}

export const { 
  selectFrame, 
  clearFrame, 
  setFrames, 
  setLoading, 
  setError,
  enrichFramesWithCameraSettings 
} = frameSlice.actions

export default frameSlice.reducer