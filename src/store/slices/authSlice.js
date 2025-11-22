import { createSlice } from '@reduxjs/toolkit'

// Получаем начальное состояние из localStorage с обработкой ошибок
const getInitialState = () => {
  try {
    const token = localStorage.getItem('authToken')
    const user = localStorage.getItem('authUser')
    
    // Обрабатываем случай, когда в localStorage записано "undefined"
    const parsedToken = token && token !== "undefined" && token !== "null" ? JSON.parse(token) : null
    const parsedUser = user && user !== "undefined" && user !== "null" ? JSON.parse(user) : null
    
    return {
      token: parsedToken,
      user: parsedUser,
      isAuthenticated: !!parsedToken,
    }
  } catch (error) {
    console.error('Error parsing auth data from localStorage:', error)
    // Очищаем некорректные данные
    localStorage.removeItem('authToken')
    localStorage.removeItem('authUser')
    return {
      token: null,
      user: null,
      isAuthenticated: false,
    }
  }
}

export const authSlice = createSlice({
  name: 'auth',
  initialState: getInitialState(),
  reducers: {
    setCredentials: (state, action) => {
      state.token = action.payload.access_token
      state.user = action.payload.user
      state.isAuthenticated = true
      
      // Сохраняем в localStorage с обработкой ошибок
      try {
        localStorage.setItem('authToken', JSON.stringify(action.payload.access_token))
        localStorage.setItem('authUser', JSON.stringify(action.payload.user))
      } catch (error) {
        console.error('Error saving auth data to localStorage:', error)
      }
    },
    clearCredentials: (state) => {
      state.token = null
      state.user = null
      state.isAuthenticated = false
      
      // Удаляем из localStorage
      try {
        localStorage.removeItem('authToken')
        localStorage.removeItem('authUser')
      } catch (error) {
        console.error('Error clearing auth data from localStorage:', error)
      }
    },
    updateUser: (state, action) => {
      state.user = { ...state.user, ...action.payload }
      try {
        localStorage.setItem('authUser', JSON.stringify(state.user))
      } catch (error) {
        console.error('Error updating user data in localStorage:', error)
      }
    },
  },
})

export const { setCredentials, clearCredentials, updateUser } = authSlice.actions

export default authSlice.reducer

// Селекторы
export const selectCurrentToken = (state) => state.auth.token
export const selectCurrentUser = (state) => state.auth.user
export const selectIsAuthenticated = (state) => state.auth.isAuthenticated