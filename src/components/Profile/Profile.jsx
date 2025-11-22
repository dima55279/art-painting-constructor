import React from 'react'
import { useSelector } from 'react-redux'
import { useGetProfileQuery, useGetOrdersQuery, useGetSubscriptionQuery } from '../../services/api'
import Header from '../Header/Header'
import Footer from '../Footer/Footer'
import styles from './Profile.module.css'

const Profile = () => {
  const { user } = useSelector((state) => state.auth)
  const { isDark } = useSelector((state) => state.theme)

  const { data: profileData, isLoading: isProfileLoading } = useGetProfileQuery()
  const { data: ordersData, isLoading: isOrdersLoading } = useGetOrdersQuery()
  const { data: subscriptionData, isLoading: isSubscriptionLoading } = useGetSubscriptionQuery()

  const themeClass = isDark ? styles.dark : styles.light

  if (isProfileLoading) {
    return <div>Загрузка...</div>
  }

  const currentUser = profileData?.user || user
  const orders = ordersData?.orders || []
  const subscription = subscriptionData?.subscription

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
                  <p className={styles.themeText}>{currentUser?.username || 'Логин'}</p>
                  <p className={styles.themeText}>{currentUser?.email || 'Электронная почта'}</p>
                  <p className={styles.themeText}>{currentUser?.phone || 'Номер телефона'}</p>
                </div>
              </div>
            </div>

            <div className={`${styles.purchaseBlock} ${themeClass}`}>
              <div className={styles.subscribeBlock}>
                <h2 className={`${styles.subscribeTitle} ${styles.themeText}`}>ПОДПИСКА</h2>
                <p className={`${styles.subscribeInfo} ${styles.themeText}`}>
                  {subscription ? `Активна до: ${new Date(subscription.expiresAt).toLocaleDateString()}` : 'Вы ещё не оформили подписку'}
                </p>
              </div>
              
              <div className={styles.orderHistorySection}>
                <h2 className={`${styles.paintingTitle} ${styles.themeText}`}>ИСТОРИЯ ЗАКАЗОВ</h2>
                
                <div className={styles.paintingsContainer}>
                  <div className={styles.paintingsScroll}>
                    {orders.length > 0 ? (
                      orders.map((order) => (
                        <div key={order.id} className={`${styles.painting} ${themeClass}`}>
                          <img 
                            src={order.imageUrl || (isDark
                              ? require('../../images/profile/paintingPlaceholderDark.png')
                              : require('../../images/profile/paintingPlaceholderLight.png')
                            )} 
                            alt={order.paintingName}
                            className={styles.paintingImage}
                          />
                          <p className={`${styles.paintingInfo} ${styles.themeText}`}>{order.paintingName}</p>
                        </div>
                      ))
                    ) : (
                      <p className={styles.themeText}>Заказов пока нет</p>
                    )}
                  </div>
                </div>
                
                {orders.length > 0 && (
                  <div className={`${styles.orderStats} ${themeClass}`}>
                    <p className={styles.themeText}>
                      Всего заказов: <strong>{orders.length}</strong>
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