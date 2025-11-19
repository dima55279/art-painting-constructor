import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  selectedFrame: null,
  frames: [
    { 
      id: 1, 
      name: 'Вестерн', 
      type: 'cowboy',
      cameraSettings: {
        minDistance: 10,
        maxDistance: 20,
        initialPosition: [0, 0, 50]
      }
    },
    { 
      id: 2, 
      name: 'Хэллоуин', 
      type: 'pumpkin',
      cameraSettings: {
        minDistance: 100,
        maxDistance: 125,
        initialPosition: [90, 90, 45]
      }
    },
    { 
      id: 3, 
      name: 'Цветы', 
      type: 'flowers',
      cameraSettings: {
        minDistance: 5,
        maxDistance: 7,
        initialPosition: [0, 0, 40]
      }
    },
    { 
      id: 4, 
      name: 'Новогодняя', 
      type: 'christmas',
      cameraSettings: {
        minDistance: 3,
        maxDistance: 5,
        initialPosition: [0, 0, 55]
      }
    },
    { 
      id: 5, 
      name: 'Море', 
      type: 'sea',
      cameraSettings: {
        minDistance: 5,
        maxDistance: 7,
        initialPosition: [0, 0, 48]
      }
    },
    { 
      id: 6, 
      name: 'Поп-арт', 
      type: 'popart',
      cameraSettings: {
        minDistance: 10,
        maxDistance: 20,
        initialPosition: [0, 0, 42]
      }
    },
    { 
      id: 7, 
      name: 'Дерево', 
      type: 'wood',
      cameraSettings: {
        minDistance: 10,
        maxDistance: 20,
        initialPosition: [0, 0, 52]
      }
    },
    { 
      id: 8, 
      name: 'Металл', 
      type: 'metal',
      cameraSettings: {
        minDistance: 10,
        maxDistance: 20,
        initialPosition: [0, 0, 46]
      }
    },
    { 
      id: 9, 
      name: 'Золото', 
      type: 'gold',
      cameraSettings: {
        minDistance: 10,
        maxDistance: 20,
        initialPosition: [0, 0, 58]
      }
    },
  ],
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
  },
})

export const { selectFrame, clearFrame } = frameSlice.actions
export default frameSlice.reducer