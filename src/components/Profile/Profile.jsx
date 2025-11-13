import React from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { Link } from 'react-router-dom'
import { logout } from '../../store/slices/authSlice'
import { clearPhoto } from '../../store/slices/photoSlice'
import { clearFrame } from '../../store/slices/frameSlice'
import { clearAnswers } from '../../store/slices/questionnaireSlice'
import Header from '../../components/Header/Header'
import Footer from '../../components/Footer/Footer'
import styles from './Profile.module.css'

const Profile = () => {
  const dispatch = useDispatch()
  const { user } = useSelector((state) => state.auth)
  const { uploadedPhoto, generatedImage } = useSelector((state) => state.photo)
  const { selectedFrame, frames } = useSelector((state) => state.frame)
  const { answers } = useSelector((state) => state.questionnaire)
  const { isDark } = useSelector((state) => state.theme)

  const handleLogout = () => {
    dispatch(logout())
    dispatch(clearPhoto())
    dispatch(clearFrame())
    dispatch(clearAnswers())
  }

  const handleDeleteAccount = () => {
    if (window.confirm('Вы уверены, что хотите удалить аккаунт? Это действие нельзя отменить.')) {
      handleLogout()
    }
  }

  const themeClass = isDark ? styles.dark : styles.light
  const selectedFrameData = frames.find(frame => frame.id === selectedFrame)

  return (
    <div>
      <Header />
      <div className={styles.container}>
        <div className={styles.mainContent}>
          <div className={`${styles.profileContainer} ${themeClass}`}>
            <h1 className={`${styles.profileHeader} ${styles.themeText}`}>ПРОФИЛЬ</h1>
            
            <div className={styles.profileInfo}>
              <div className={`${styles.userCard} ${themeClass}`}>
                <div className={`${styles.avatarSection} ${themeClass}`}>
                  <div className={`${styles.avatar} ${themeClass}`}>
                    {user?.username?.charAt(0).toUpperCase() || 'U'}
                  </div>
                  <h2 className={`${styles.username} ${styles.themeText}`}>
                    {user?.username || 'Пользователь'}
                  </h2>
                  <p className={`${styles.userEmail} ${styles.themeText}`}>
                    {user?.email || 'Email не указан'}
                  </p>
                  <p className={`${styles.userPhone} ${styles.themeText}`}>
                    {user?.phone || 'Телефон не указан'}
                  </p>
                </div>
                
                <div className={styles.statsSection}>
                  <h3 className={styles.themeText}>Статистика</h3>
                  <div className={styles.statsGrid}>
                    <div className={`${styles.statItem} ${themeClass}`}>
                      <span className={`${styles.statNumber} ${styles.themeText}`}>
                        {uploadedPhoto ? 1 : 0}
                      </span>
                      <span className={`${styles.statLabel} ${styles.themeText}`}>
                        Загружено фото
                      </span>
                    </div>
                    <div className={`${styles.statItem} ${themeClass}`}>
                      <span className={`${styles.statNumber} ${styles.themeText}`}>
                        {generatedImage ? 1 : 0}
                      </span>
                      <span className={`${styles.statLabel} ${styles.themeText}`}>
                        Сгенерировано изображений
                      </span>
                    </div>
                    <div className={`${styles.statItem} ${themeClass}`}>
                      <span className={`${styles.statNumber} ${styles.themeText}`}>
                        {selectedFrame ? 1 : 0}
                      </span>
                      <span className={`${styles.statLabel} ${styles.themeText}`}>
                        Выбрано рамок
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div className={`${styles.currentProject} ${themeClass}`}>
                <h3 className={styles.themeText}>Текущий проект</h3>
                {uploadedPhoto ? (
                  <div className={styles.projectDetails}>
                    <div className={styles.projectPreview}>
                      <h4 className={styles.themeText}>Загруженное фото:</h4>
                      <img 
                        src={uploadedPhoto} 
                        alt="Загруженное фото" 
                        className={`${styles.projectImage} ${themeClass}`}
                      />
                    </div>
                    
                    <div className={styles.projectInfo}>
                      <div className={`${styles.infoItem} ${themeClass}`}>
                        <strong className={styles.themeText}>Выбранная рамка:</strong>
                        <span className={styles.themeText}>
                          {selectedFrameData ? selectedFrameData.name : 'Не выбрана'}
                        </span>
                      </div>
                      
                      <div className={`${styles.answersSection} ${themeClass}`}>
                        <h4 className={styles.themeText}>Ответы анкеты:</h4>
                        {answers.setting && (
                          <div className={`${styles.answerItem} ${themeClass}`}>
                            <strong className={styles.themeText}>Сеттинг:</strong> 
                            <span className={styles.themeText}>{answers.setting}</span>
                          </div>
                        )}
                        {answers.clothing && (
                          <div className={`${styles.answerItem} ${themeClass}`}>
                            <strong className={styles.themeText}>Одежда:</strong> 
                            <span className={styles.themeText}>{answers.clothing}</span>
                          </div>
                        )}
                        {answers.pose && (
                          <div className={`${styles.answerItem} ${themeClass}`}>
                            <strong className={styles.themeText}>Поза:</strong> 
                            <span className={styles.themeText}>{answers.pose}</span>
                          </div>
                        )}
                      </div>

                      {generatedImage && (
                        <div className={styles.generatedResult}>
                          <h4 className={styles.themeText}>Результат генерации:</h4>
                          <img 
                            src={generatedImage} 
                            alt="Сгенерированное изображение" 
                            className={`${styles.generatedImage} ${themeClass}`}
                          />
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className={styles.noProject}>
                    <p className={styles.themeText}>У вас нет активных проектов</p>
                    <Link to="/" className={styles.createProjectBtn}>
                      Создать новый проект
                    </Link>
                  </div>
                )}
              </div>

              <div className={`${styles.actionsSection} ${themeClass}`}>
                <h3 className={styles.themeText}>Действия</h3>
                <div className={styles.actionsGrid}>
                  <Link to="/" className={`${styles.actionBtn} ${themeClass}`}>
                    <span className={styles.actionIcon}>🎨</span>
                    <span className={styles.themeText}>Создать новый проект</span>
                  </Link>
                  
                  <button 
                    onClick={handleLogout} 
                    className={`${styles.actionBtn} ${themeClass}`}
                  >
                    <span className={styles.actionIcon}>🚪</span>
                    <span className={styles.themeText}>Выйти из аккаунта</span>
                  </button>
                  
                  <button 
                    className={`${styles.actionBtn} ${themeClass} ${styles.danger}`}
                    onClick={handleDeleteAccount}
                  >
                    <span className={styles.actionIcon}>🗑️</span>
                    <span className={styles.themeText}>Удалить аккаунт</span>
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