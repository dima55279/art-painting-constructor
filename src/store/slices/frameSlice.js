import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  selectedFrame: null,
  frames: [
    { 
      id: 1, 
      name: 'Вестерн', 
      type: 'cowboy'
    },
    { 
      id: 2, 
      name: 'Хэллоуин', 
      type: 'pumpkin'
    },
    { 
      id: 3, 
      name: 'Цветы', 
      type: 'flowers'
    },
    { 
      id: 4, 
      name: 'Барокко', 
      type: 'baroque'
    },
    { 
      id: 5, 
      name: 'Ар-деко', 
      type: 'artdeco'
    },
    { 
      id: 6, 
      name: 'Поп-арт', 
      type: 'popart'
    },
    { 
      id: 7, 
      name: 'Дерево', 
      type: 'wood'
    },
    { 
      id: 8, 
      name: 'Металл', 
      type: 'metal'
    },
    { 
      id: 9, 
      name: 'Золото', 
      type: 'gold'
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