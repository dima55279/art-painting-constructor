import React from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { setGeneratedImage, setLoading } from '../../store/slices/photoSlice'
import Header from '../../components/Header/Header'
import Footer from '../../components/Footer/Footer'
import PhotoUpload from '../../components/PhotoUpload/PhotoUpload'
import FrameSelection from '../../components/FrameSelection/FrameSelection'
import Questionnaire from '../../components/Questionnaire/Questionnaire'
import GenerationSection from '../../components/GenerationSection/GenerationSection'
import styles from './MainPage.module.css'
import cowboyDark from '../../images/mainPage/cowboyAndFairyDark.png'
import cowboyLight from '../../images/mainPage/cowboyAndFairyLight.png'
import dragonDark from '../../images/mainPage/dragonAndPlanetDark.png'
import dragonLight from '../../images/mainPage/dragonAndPlanetLight.png'

const MainPage = () => {
  const dispatch = useDispatch()
  const { isDark } = useSelector((state) => state.theme)
  const { uploadedPhoto } = useSelector((state) => state.photo)

  const handleGenerate = async () => {
    dispatch(setLoading(true))
    // Имитация генерации изображения
    setTimeout(() => {
      dispatch(setGeneratedImage(
        isDark 
          ? '../../images/mainPage/generatedDark.png' 
          : '../../images/mainPage/generatedLight.png'
      ))
      dispatch(setLoading(false))
    }, 2000)
  }

  const themeClass = isDark ? styles.dark : styles.light

  return (
    <div className={styles.mainPage}>
      <Header />
      <div className={styles.container}>
        <div className={styles.mainContent}>
          <div className={`${styles.leftColumn} ${themeClass}`}>
            <div className={`${styles.photoBlock} ${themeClass}`}>
              <div className={styles.photoPreview}>
                <h3 className={styles.themeText}>Ваше фото</h3>
                <div className={`${styles.resultPhotoPlaceholder} ${themeClass}`}>
                  {uploadedPhoto ? (
                    <img 
                      src={uploadedPhoto} 
                      alt="Загруженное фото" 
                      className={styles.uploadedPhoto}
                    />
                  ) : (
                    <span className={styles.themeText}>Здесь будет ваше фото</span>
                  )}
                </div>
              </div>
              <FrameSelection />
            </div>
            <img 
              src={isDark ? cowboyDark : cowboyLight} 
              className={styles.presetCowboy} 
              alt="Cowboy and Fairy" 
            />
            <img 
              src={isDark ? dragonDark : dragonLight}
              className={styles.presetDragon}
              alt="Dragon and Planet"
            />
          </div>
          
          <div className={`${styles.rightColumn} ${themeClass}`}>
            <h2 className={`${styles.sectionTitle} ${styles.themeText}`}>Краткая информация</h2>
            <p className={`${styles.infoText} ${styles.themeText}`}>
              Испытываете муки выбора подарка любимому человеку?<br />
              Тогда наш сервис - идеальный выбор!<br />
              Загрузите фотографию того, кому хотите сделать подарок (убедитесь, что его лицо чётко видно), 
              ответьте на пару вопросов, выберите понравившуюся рамку - и закажите картину по номерам, 
              где Ваш любимый человек будет изображен в том образе и окружении, в котором Вы пожелаете!
            </p>
            
            <PhotoUpload />
            
            <Questionnaire />
          </div>
        </div>
        
        <GenerationSection onGenerate={handleGenerate} />
      </div>
      <Footer />
    </div>
  )
}

export default MainPage