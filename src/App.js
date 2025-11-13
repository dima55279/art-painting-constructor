// App.js
import React, { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Provider, useSelector, useDispatch } from 'react-redux'
import { store } from './store'
import { setTheme } from './store/slices/themeSlice'
import MainPage from './components/MainPage/MainPage'
import Login from './components/Login/Login'
import Registration from './components/Registration/Registration'
import Profile from './components/Profile/Profile'
import './App.css'

function ThemeWrapper({ children }) {
  const dispatch = useDispatch()
  const { isDark } = useSelector((state) => state.theme)

  useEffect(() => {
    // При загрузке приложения проверяем сохраненную тему
    const savedTheme = localStorage.getItem('theme')
    if (savedTheme) {
      dispatch(setTheme(savedTheme === 'dark'))
    }
  }, [dispatch])

  useEffect(() => {
    // Сохраняем тему в localStorage при изменении
    localStorage.setItem('theme', isDark ? 'dark' : 'light')
    
    // Добавляем класс к body для глобальных стилей
    document.body.className = isDark ? 'dark-theme' : 'light-theme'
  }, [isDark])

  return children
}

function AppContent() {
  return (
    <div className="App">
      <Routes>
        <Route path="/" element={<MainPage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/registration" element={<Registration />} />
        <Route path="/profile" element={<Profile />} />
      </Routes>
    </div>
  )
}

function App() {
  return (
    <Provider store={store}>
      <Router>
        <ThemeWrapper>
          <AppContent />
        </ThemeWrapper>
      </Router>
    </Provider>
  )
}

export default App