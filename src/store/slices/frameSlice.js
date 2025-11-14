import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  selectedFrame: null,
  frames: [
    { id: 1, name: 'Классика', type: 'classic' },
    { id: 2, name: 'Модерн', type: 'modern' },
    { id: 3, name: 'Винтаж', type: 'vintage' },
    { id: 4, name: 'Минимализм', type: 'minimal' },
    { id: 5, name: 'Барокко', type: 'baroque' },
    { id: 6, name: 'Ар-деко', type: 'artdeco' },
    { id: 7, name: 'Поп-арт', type: 'popart' },
    { id: 8, name: 'Дерево', type: 'wood' },
    { id: 9, name: 'Металл', type: 'metal' },
    { id: 10, name: 'Золото', type: 'gold' },
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