import React from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { Link } from 'react-router-dom'
import { logout } from '../../store/slices/authSlice.js'
import { clearPhoto } from '../../store/slices/photoSlice.js'
import { clearFrame } from '../../store/slices/frameSlice.js'
import { clearAnswers } from '../../store/slices/questionnaireSlice.js'
import Header from '../Header/Header.jsx'
import Footer from '../Footer/Footer.jsx'
import styles from './Profile.module.css'

const Profile = () => {
  const dispatch = useDispatch()
  const { user } = useSelector((state) => state.auth)
  const { uploadedPhoto, generatedImage } = useSelector((state) => state.photo)
  const { selectedFrame } = useSelector((state) => state.frame)
  const { answers } = useSelector((state) => state.questionnaire)

  const handleLogout = () => {
    dispatch(logout())
    dispatch(clearPhoto())
    dispatch(clearFrame())
    dispatch(clearAnswers())
  }

  const handleDeleteAccount = () => {
    if (window.confirm('Вы уверены, что хотите удалить аккаунт? Это действие нельзя отменить.')) {
      // Здесь должна быть логика удаления аккаунта
      handleLogout()
    }
  }

  return (
    <div>
      <Header />
      <div className={styles.container}>
        <div className={styles.mainContent}>
          <div className={styles.profileContainer}>
            <h1 className={styles.profileHeader}>ПРОФИЛЬ</h1>
            
            <div className={styles.profileInfo}>
              <div className={styles.userCard}>
                <div className={styles.avatarSection}>
                  <div className={styles.avatar}>
                    {user?.username?.charAt(0).toUpperCase() || 'U'}
                  </div>
                  <h2 className={styles.username}>{user?.username || 'Пользователь'}</h2>
                  <p className={styles.userEmail}>{user?.email || 'Email не указан'}</p>
                  <p className={styles.userPhone}>{user?.phone || 'Телефон не указан'}</p>
                </div>
                
                <div className={styles.statsSection}>
                  <h3>Статистика</h3>
                  <div className={styles.statsGrid}>
                    <div className={styles.statItem}>
                      <span className={styles.statNumber}>{uploadedPhoto ? 1 : 0}</span>
                      <span className={styles.statLabel}>Загружено фото</span>
                    </div>
                    <div className={styles.statItem}>
                      <span className={styles.statNumber}>{generatedImage ? 1 : 0}</span>
                      <span className={styles.statLabel}>Сгенерировано изображений</span>
                    </div>
                    <div className={styles.statItem}>
                      <span className={styles.statNumber}>{selectedFrame ? 1 : 0}</span>
                      <span className={styles.statLabel}>Выбрано рамок</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className={styles.currentProject}>
                <h3>Текущий проект</h3>
                {uploadedPhoto ? (
                  <div className={styles.projectDetails}>
                    <div className={styles.projectPreview}>
                      <h4>Загруженное фото:</h4>
                      <img 
                        src={uploadedPhoto} 
                        alt="Загруженное фото" 
                        className={styles.projectImage}
                      />
                    </div>
                    
                    <div className={styles.projectInfo}>
                      <div className={styles.infoItem}>
                        <strong>Выбранная рамка:</strong>
                        <span>{selectedFrame ? `Рамка ${selectedFrame}` : 'Не выбрана'}</span>
                      </div>
                      
                      <div className={styles.answersSection}>
                        <h4>Ответы анкеты:</h4>
                        {answers.setting && (
                          <div className={styles.answerItem}>
                            <strong>Сеттинг:</strong> {answers.setting}
                          </div>
                        )}
                        {answers.clothing && (
                          <div className={styles.answerItem}>
                            <strong>Одежда:</strong> {answers.clothing}
                          </div>
                        )}
                        {answers.pose && (
                          <div className={styles.answerItem}>
                            <strong>Поза:</strong> {answers.pose}
                          </div>
                        )}
                      </div>

                      {generatedImage && (
                        <div className={styles.generatedResult}>
                          <h4>Результат генерации:</h4>
                          <img 
                            src={generatedImage} 
                            alt="Сгенерированное изображение" 
                            className={styles.generatedImage}
                          />
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className={styles.noProject}>
                    <p>У вас нет активных проектов</p>
                    <Link to="/" className={styles.createProjectBtn}>
                      Создать новый проект
                    </Link>
                  </div>
                )}
              </div>

              <div className={styles.actionsSection}>
                <h3>Действия</h3>
                <div className={styles.actionsGrid}>
                  <Link to="/" className={styles.actionBtn}>
                    <span className={styles.actionIcon}>🎨</span>
                    <span>Создать новый проект</span>
                  </Link>
                  
                  <button className={styles.actionBtn} onClick={handleLogout}>
                    <span className={styles.actionIcon}>🚪</span>
                    <span>Выйти из аккаунта</span>
                  </button>
                  
                  <button 
                    className={`${styles.actionBtn} ${styles.danger}`}
                    onClick={handleDeleteAccount}
                  >
                    <span className={styles.actionIcon}>🗑️</span>
                    <span>Удалить аккаунт</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  )
}

export default Profile