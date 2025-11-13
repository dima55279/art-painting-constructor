import React, { useState } from 'react'
import { useDispatch } from 'react-redux'
import { useNavigate } from 'react-router-dom'
import { login } from '../../store/slices/authSlice.js'
import Header from '../Header/Header.jsx'
import Footer from '../Footer/Footer.jsx'
import styles from './Login.module.css'

const Login = () => {
  const dispatch = useDispatch()
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  })

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    // Здесь должна быть реальная логика авторизации
    dispatch(login({ username: formData.username }))
    navigate('/')
  }

  return (
    <div>
      <Header />
      <div className={styles.container}>
        <div className={styles.mainContent}>
          <div className={styles.loginContainer}>
            <h1 className={styles.registrationHeader}>ВХОД</h1>
            
            <form onSubmit={handleSubmit} className={styles.form}>
              <div className={styles.formGroup}>
                <input
                  className={styles.loginTextInput}
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
                  className={styles.loginTextInput}
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