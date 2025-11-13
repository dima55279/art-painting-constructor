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

const MainPage = () => {
  const dispatch = useDispatch()
  const { isDark } = useSelector((state) => state.theme)
  const { uploadedPhoto } = useSelector((state) => state.photo)

  const handleGenerate = async () => {
    dispatch(setLoading(true))
    // Имитация генерации изображения
    setTimeout(() => {
      dispatch(setGeneratedImage('path/to/generated/image.png'))
      dispatch(setLoading(false))
    }, 2000)
  }

  return (
    <div className={styles.mainPage}>
      <Header />
      <div className={styles.container}>
        <div className={styles.mainContent}>
          <div className={styles.leftColumn}>
            <div className={styles.photoBlock}>
              <div className={styles.photoPreview}>
                <h3>Ваше фото</h3>
                <div className={styles.resultPhotoPlaceholder}>
                  {uploadedPhoto ? (
                    <img 
                      src={uploadedPhoto} 
                      alt="Загруженное фото" 
                      className={styles.uploadedPhoto}
                    />
                  ) : (
                    <span>Здесь будет ваше фото</span>
                  )}
                </div>
              </div>
              <FrameSelection />
            </div>
            <img 
              src={isDark 
                ? '/images/mainPage/cowboyAndFairyDark.png' 
                : '/images/mainPage/cowboyAndFairyLight.png'
              } 
              className={styles.presetCowboy} 
              alt="Cowboy and Fairy" 
            />
            <img 
              src={isDark
                ? '/images/mainPage/dragonAndPlanetDark.png'
                : '/images/mainPage/dragonAndPlanetLight.png'
              }
              className={styles.presetDragon}
              alt="Dragon and Planet"
            />
          </div>
          
          <div className={styles.rightColumn}>
            <h2 className={styles.sectionTitle}>Краткая информация</h2>
            <p className={styles.infoText}>
              Испытываете муки выбора подарка любимому человеку?<br />
              Тогда наш сервис - идеальный выбор!<br />
              Загрузите фотографию того, кому хотите сделать подарок (убедитесь, что его лицо чётко видно), 
              ответьте на пару вопросов, выберите понравившуюся рамку - и закажите картину по номерам, 
              где Ваш любимый человек будет изображен в том образе и окружении, в котором Вы пожелаете!
            </p>
            
            <div className={styles.photoUpload}>
              <input type="file" className={styles.fileInput} />
              <button className={styles.uploadBtn}>Загрузить фото</button>
            </div>
            
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