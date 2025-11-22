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
    // Новый reducer для обновления информации о фото
    updatePhotoInfo: (state, action) => {
      if (state.uploadedPhoto) {
        state.uploadedPhoto = { ...state.uploadedPhoto, ...action.payload }
      }
    }
  },
})

export const { 
  setUploadedPhoto, 
  setGeneratedImage, 
  setLoading, 
  clearPhoto,
  updatePhotoInfo 
} = photoSlice.actions

export default photoSlice.reducer