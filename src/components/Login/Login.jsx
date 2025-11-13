import React, { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { useNavigate, Link } from 'react-router-dom'
import { login } from '../../store/slices/authSlice'
import Header from '../../components/Header/Header'
import Footer from '../../components/Footer/Footer'
import styles from './Login.module.css'

const Login = () => {
  const dispatch = useDispatch()
  const navigate = useNavigate()
  const { isDark } = useSelector((state) => state.theme)
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  })
  const [error, setError] = useState('')

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
    setError('')
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    
    // Базовая валидация
    if (!formData.username || !formData.password) {
      setError('Все поля обязательны для заполнения')
      return
    }

    // Имитация авторизации
    try {
      dispatch(login({ 
        username: formData.username,
        id: Date.now()
      }))
      navigate('/')
    } catch (err) {
      setError('Ошибка авторизации')
    }
  }

  const themeClass = isDark ? styles.dark : styles.light

  return (
    <div>
      <Header />
      <div className={styles.container}>
        <div className={styles.mainContent}>
          <div className={`${styles.loginContainer} ${themeClass}`}>
            <h1 className={styles.registrationHeader}>ВХОД</h1>
            
            <form onSubmit={handleSubmit} className={styles.form}>
              {error && <div className={styles.errorMessage}>{error}</div>}
              
              <div className={styles.formGroup}>
                <input
                  className={`${styles.loginTextInput} ${themeClass}`}
                  type="text"
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  placeholder="Введите имя пользователя"
                  required
                />
              </div>
              
              <div className={styles.formGroup}>
                <input
                  className={`${styles.loginTextInput} ${themeClass}`}
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="Введите пароль"
                  required
                />
              </div>
              
              <button type="submit" className={styles.btnLoginSubmit}>
                ВОЙТИ
              </button>
              
            </form>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  )
}

export default Login