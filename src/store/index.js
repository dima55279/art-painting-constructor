import { configureStore } from '@reduxjs/toolkit'
import { api } from '../services/api'
import frameReducer from './slices/frameSlice'
import authReducer from './slices/authSlice'
import photoReducer from './slices/photoSlice'
import questionnaireReducer from './slices/questionnaireSlice'
import themeReducer from './slices/themeSlice'
import { frameMiddleware } from './middleware/frameMiddleware'

export const store = configureStore({
  reducer: {
    auth: authReducer,
    frame: frameReducer,
    photo: photoReducer,
    questionnaire: questionnaireReducer,
    theme: themeReducer,
    [api.reducerPath]: api.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware()
      .concat(api.middleware)
      .concat(frameMiddleware),
})

export default store