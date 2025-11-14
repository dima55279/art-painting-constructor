import React from 'react'
import { useSelector } from 'react-redux'
import { Link } from 'react-router-dom'
import Header from '../../components/Header/Header'
import Footer from '../../components/Footer/Footer'
import styles from './Profile.module.css'

const Profile = () => {
  const { user } = useSelector((state) => state.auth)
  const { isDark } = useSelector((state) => state.theme)

  const themeClass = isDark ? styles.dark : styles.light

  return (
    <div className={styles.profilePage}>
      <Header />
      <div className={styles.container}>
        <div className={styles.mainContent}>
          <div className={`${styles.profileBlock} ${themeClass}`}>
            <h2 className={styles.profileTitle}>ПРОФИЛЬ</h2>
            <hr className={styles.profileLine} />
            <br />
            <div className={styles.profileContent}>
              <img 
                src={isDark 
                  ? require('../../images/profile/iconPlaceholderDark.png') 
                  : require('../../images/profile/iconPlaceholderLight.png')
                } 
                alt="Аватар"
                className={styles.profileImage}
              />
              <div className={`${styles.profileInfo} ${themeClass}`}>
                <p className={styles.themeText}>{user?.username || 'Логин'}</p>
                <p className={styles.themeText}>{user?.email || 'Электронная почта'}</p>
                <p className={styles.themeText}>{user?.phone || 'Номер телефона'}</p>
              </div>
            </div>
          </div>
          <div className={`${styles.purchaseBlock} ${themeClass}`}>
            <div className={styles.subscribeBlock}>
              <h2 className={`${styles.subscribeTitle} ${styles.themeText}`}>ПОДПИСКА</h2>
              <p className={`${styles.subscribeInfo} ${styles.themeText}`}>Вы ещё не оформили подписку</p>
            </div>
            <div>
              <h2 className={`${styles.paintingTitle} ${styles.themeText}`}>ИСТОРИЯ ЗАКАЗОВ</h2>
              <div className={styles.paintingBlock}>
                <div className={`${styles.painting} ${themeClass}`}>
                  <img 
                    src={isDark
                      ? require('../../images/profile/paintingPlaceholderDark.png')
                      : require('../../images/profile/paintingPlaceholderLight.png')
                    } 
                    alt="Картина 1"
                    className={styles.paintingImage}
                  />
                  <p className={`${styles.paintingInfo} ${styles.themeText}`}>Картина</p>
                </div>
                <div className={`${styles.painting} ${themeClass}`}>
                  <img 
                    src={isDark
                      ? require('../../images/profile/paintingPlaceholderDark.png')
                      : require('../../images/profile/paintingPlaceholderLight.png')
                    } 
                    alt="Картина 2"
                    className={styles.paintingImage}
                  />
                  <p className={`${styles.paintingInfo} ${styles.themeText}`}>Картина</p>
                </div>
                <div className={`${styles.painting} ${themeClass}`}>
                  <img 
                    src={isDark
                      ? require('../../images/profile/paintingPlaceholderDark.png')
                      : require('../../images/profile/paintingPlaceholderLight.png')
                    } 
                    alt="Картина 3"
                    className={styles.paintingImage}
                  />
                  <p className={`${styles.paintingInfo} ${styles.themeText}`}>Картина</p>
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