import React from 'react'
import './Card.css'

const Card = ({
  children,
  className = '',
  padding = 'lg',
  shadow = false,
  hover = false,
  onClick,
  ...props
}) => {
  const cardClass = `card card-padding-${padding} ${shadow ? 'card-shadow' : ''} ${hover ? 'card-hover' : ''} ${onClick ? 'card-clickable' : ''} ${className}`.trim()

  return (
    <div
      className={cardClass}
      onClick={onClick}
      {...props}
    >
      {children}
    </div>
  )
}

export default Card
