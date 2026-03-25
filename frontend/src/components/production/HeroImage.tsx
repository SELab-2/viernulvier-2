interface HeroImageProps {
  title: string
  imageUrl: string | null
}

export default function HeroImage({ title, imageUrl }: HeroImageProps) {
  return (
    <div
      className="hero-image"
      style={{
        width: '100%',
        aspectRatio: '16/7',
        backgroundColor: '#1a1a1a',
        borderRadius: '4px',
        overflow: 'hidden',
        marginBottom: '32px',
      }}
    >
      {imageUrl ? (
        <img
          src={imageUrl}
          alt={title}
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        />
      ) : (
        <div
          style={{
            width: '100%',
            height: '100%',
            background: 'linear-gradient(135deg, #1a1a1a 0%, #333 100%)',
          }}
        />
      )}
    </div>
  )
}
