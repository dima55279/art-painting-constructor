import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  selectedFrame: null,
  frames: [
    { id: 1, name: 'Рамка 1', type: 'classic' },
    { id: 2, name: 'Рамка 2', type: 'modern' },
    { id: 3, name: 'Рамка 3', type: 'vintage' },
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