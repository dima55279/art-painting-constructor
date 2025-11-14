import React from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { selectFrame } from '../../store/slices/frameSlice'
import styles from './FrameSelection.module.css'

const FrameSelection = () => {
  const dispatch = useDispatch()
  const { frames, selectedFrame } = useSelector((state) => state.frame)
  const { isDark } = useSelector((state) => state.theme)

  const handleFrameSelect = (frameId) => {
    dispatch(selectFrame(frameId))
  }

  const themeClass = isDark ? styles.dark : styles.light

  return (
    <div className={`${styles.frameSelection} ${themeClass}`}>
      <h3 className={styles.frameTitle}>Выбор рамки</h3>
      
      <div className={styles.framesContainer}>
        <div className={styles.framesScroll}>
          {frames.map((frame) => (
            <div
              key={frame.id}
              className={`${styles.frame} ${themeClass} ${
                selectedFrame === frame.id ? styles.selected : ''
              }`}
              onClick={() => handleFrameSelect(frame.id)}
            >
              <div className={styles.frameContent}>
                <div className={styles.framePreview}></div>
                <span className={styles.frameName}>{frame.name}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
      
    </div>
  )
}

export default FrameSelection