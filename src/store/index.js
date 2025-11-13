import { configureStore } from '@reduxjs/toolkit'
import themeReducer from './slices/themeSlice'
import photoReducer from './slices/photoSlice'
import frameReducer from './slices/frameSlice'
import questionnaireReducer from './slices/questionnaireSlice'
import authReducer from './slices/authSlice'

export const store = configureStore({
  reducer: {
    theme: themeReducer,
    photo: photoReducer,
    frame: frameReducer,
    questionnaire: questionnaireReducer,
    auth: authReducer,
  },
})