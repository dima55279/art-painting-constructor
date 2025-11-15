import React from 'react'
import { useSelector } from 'react-redux'
import { Link } from 'react-router-dom'
import Header from '../../components/Header/Header'
import Footer from '../../components/Footer/Footer'
import styles from './Profile.module.css'

const Profile = () => {
  const { user } = useSelector((state) => state.auth)
  const { isDark } = useSelector((state) => state.theme)

  const orderHistory = [
    { id: 1, name: "Картина 1", image: "paintingPlaceholderDark.png" },
    { id: 2, name: "Картина 2", image: "paintingPlaceholderDark.png" },
    { id: 3, name: "Картина 3", image: "paintingPlaceholderDark.png" },
    { id: 4, name: "Картина 4", image: "paintingPlaceholderDark.png" },
    { id: 5, name: "Картина 5", image: "paintingPlaceholderDark.png" },
    { id: 6, name: "Картина 6", image: "paintingPlaceholderDark.png" },
  ]

  const themeClass = isDark ? styles.dark : styles.light

  return (
    <div className={styles.profilePage}>
      <Header />
      <div className={styles.container}>
        <div className={styles.mainContent}>
          <div className={styles.profileLayout}>
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
              
              <div className={styles.orderHistorySection}>
                <h2 className={`${styles.paintingTitle} ${styles.themeText}`}>ИСТОРИЯ ЗАКАЗОВ</h2>
                
                <div className={styles.paintingsContainer}>
                  <div className={styles.paintingsScroll}>
                    {orderHistory.map((painting) => (
                      <div key={painting.id} className={`${styles.painting} ${themeClass}`}>
                        <img 
                          src={isDark
                            ? require(`../../images/profile/${painting.image}`)
                            : require(`../../images/profile/paintingPlaceholderLight.png`)
                          } 
                          alt={painting.name}
                          className={styles.paintingImage}
                        />
                        <p className={`${styles.paintingInfo} ${styles.themeText}`}>{painting.name}</p>
                      </div>
                    ))}
                  </div>
                </div>
                
                {orderHistory.length > 0 && (
                  <div className={`${styles.orderStats} ${themeClass}`}>
                    <p className={styles.themeText}>
                      Всего заказов: <strong>{orderHistory.length}</strong>
                    </p>
                  </div>
                )}
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