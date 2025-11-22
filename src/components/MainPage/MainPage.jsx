import React, { useState } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { useGenerateImageMutation } from '../../services/api'
import { setGeneratedImage, setLoading } from '../../store/slices/photoSlice'
import Header from '../Header/Header'
import Footer from '../Footer/Footer'
import PhotoUpload from '../PhotoUpload/PhotoUpload'
import FrameSelection from '../FrameSelection/FrameSelection'
import Questionnaire from '../Questionnaire/Questionnaire'
import GenerationSection from '../GenerationSection/GenerationSection'
import styles from './MainPage.module.css'

import cowboyDark from '../../images/mainPage/cowboyAndFairyDark.png'
import cowboyLight from '../../images/mainPage/cowboyAndFairyLight.png'
import dragonDark from '../../images/mainPage/dragonAndPlanetDark.png'
import dragonLight from '../../images/mainPage/dragonAndPlanetLight.png'

const MainPage = () => {
  const dispatch = useDispatch()
  const { isDark } = useSelector((state) => state.theme)
  const { uploadedPhoto } = useSelector((state) => state.photo) // Получаем загруженное фото из Redux
  const { selectedFrame } = useSelector((state) => state.frame)
  const { answers } = useSelector((state) => state.questionnaire)
  
  const [generateImage, { isLoading: isGenerating }] = useGenerateImageMutation()
  const [generationId, setGenerationId] = useState(null)

  const handleGenerate = async () => {
    if (!uploadedPhoto) {
      alert('Пожалуйста, сначала загрузите фото')
      return
    }

    if (!selectedFrame) {
      alert('Пожалуйста, выберите рамку')
      return
    }

    dispatch(setLoading(true))

    try {
      const generationData = {
        photo_id: uploadedPhoto.id, // Используем ID загруженного фото
        frame_id: selectedFrame,
        questionnaire: answers,
        theme: isDark ? 'dark' : 'light'
      }

      const result = await generateImage(generationData).unwrap()
      setGenerationId(result.generationId)
      dispatch(setGeneratedImage(result.generatedImageUrl))
    } catch (error) {
      alert(error.data?.message || 'Ошибка при генерации изображения')
      dispatch(setGeneratedImage(null))
    } finally {
      dispatch(setLoading(false))
    }
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
                <h3 className={styles.photoTitle}>Ваше фото</h3>
                <div className={`${styles.resultPhotoPlaceholder} ${themeClass}`}>
                  {uploadedPhoto ? (
                    <div className={styles.photoContainer}>
                      <img 
                        src={uploadedPhoto.previewUrl || uploadedPhoto.generated_image_url || '/placeholder-image.jpg'} 
                        alt="Загруженное фото" 
                        className={styles.uploadedPhoto}
                      />
                    </div>
                  ) : (
                    <div className={styles.placeholderContainer}>
                      <span className={styles.placeholderText}>
                        Загрузите фото, чтобы увидеть его здесь
                      </span>
                      <div className={styles.uploadInstructions}>
                        <p>Требования к фото:</p>
                        <ul>
                          <li>Четко видимое лицо</li>
                          <li>Хорошее освещение</li>
                          <li>Форматы: JPEG, PNG, WebP</li>
                          <li>Максимальный размер: 10MB</li>
                        </ul>
                      </div>
                    </div>
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
        
        <GenerationSection 
          onGenerate={handleGenerate} 
          isLoading={isGenerating}
          generationId={generationId}
          hasPhoto={!!uploadedPhoto}
          hasFrame={!!selectedFrame}
        />
      </div>
      <Footer />
    </div>
  )
}

export default MainPage