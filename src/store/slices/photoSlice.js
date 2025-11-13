import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  uploadedPhoto: null,
  generatedImage: null,
  isLoading: false,
}

export const photoSlice = createSlice({
  name: 'photo',
  initialState,
  reducers: {
    setUploadedPhoto: (state, action) => {
      state.uploadedPhoto = action.payload
    },
    setGeneratedImage: (state, action) => {
      state.generatedImage = action.payload
    },
    setLoading: (state, action) => {
      state.isLoading = action.payload
    },
    clearPhoto: (state) => {
      state.uploadedPhoto = null
      state.generatedImage = null
    },
  },
})

export const { setUploadedPhoto, setGeneratedImage, setLoading, clearPhoto } = photoSlice.actions
export default photoSlice.reducer